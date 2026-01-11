import os
import faiss
import numpy as np
import pickle
from typing import List, Dict, Any, Optional
from pypdf import PdfReader
from docx import Document
import tiktoken
from services.ai_client import AIClientFactory
import pymysql
import json
import logging

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self, storage_path: str = "storage/rag"):
        self.storage_path = storage_path
        self.index_path = os.path.join(storage_path, "indices")
        self.files_path = os.path.join(storage_path, "files")
        
        # 確保目錄存在
        os.makedirs(self.index_path, exist_ok=True)
        os.makedirs(self.files_path, exist_ok=True)
        
        # 模型與供應商快取 (懶載入)
        self._local_model = None
        self._google_api_key = os.getenv('GOOGLE_API_KEY')
        self._openai_client = None
        
        # 快取已載入的索引
        self._indices = {}
        
        # 資料庫配置
        self.db_config = {
            'host': os.getenv('DB_HOST', 'db'),
            'port': int(os.getenv('DB_PORT', '3306')),
            'user': os.getenv('DB_USER', 'mcp_user'),
            'password': os.getenv('DB_PASSWORD', 'mcp_password'),
            'database': os.getenv('DB_NAME', 'mcp_platform'),
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }

    def get_kb_config(self, kb_id: int) -> Dict[str, Any]:
        """獲取知識庫配置"""
        try:
            conn = pymysql.connect(**self.db_config)
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM kb_configs WHERE kb_id = %s
                """, (kb_id,))
                config = cursor.fetchone()
            conn.close()
            
            if config:
                return config
            else:
                # 如果沒有配置,返回預設值
                return {
                    'chunk_strategy': 'character',
                    'chunk_size': 500,
                    'chunk_overlap': 50,
                    'embedding_provider': 'openai',
                    'embedding_model': 'text-embedding-3-small',
                    'embedding_dimension': 1536,
                    'index_type': 'flat',
                    'retrieval_top_k': 3,
                    'similarity_threshold': 0.0
                }
        except Exception as e:
            print(f"獲取配置失敗: {str(e)}")
            # 返回預設配置
            return {
                'chunk_strategy': 'character',
                'chunk_size': 500,
                'chunk_overlap': 50,
                'embedding_provider': 'openai',
                'embedding_model': 'text-embedding-3-small',
                'embedding_dimension': 1536,
                'index_type': 'flat',
                'retrieval_top_k': 3,
                'similarity_threshold': 0.0
            }

    def extract_text(self, file_path: str) -> str:
        """從不同格式的文件中提取文字"""
        ext = os.path.splitext(file_path)[1].lower()
        text = ""
        
        if ext == ".pdf":
            reader = PdfReader(file_path)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        elif ext == ".docx":
            doc = Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        elif ext in [".txt", ".md"]:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        else:
            raise ValueError(f"不支援的檔案格式: {ext}")
            
        return text

    def split_text(self, text: str, strategy: str = 'character', 
                   chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
        """將長文本切分成較小的區塊 (Chunks)"""
        if strategy == 'character':
            return self._character_split(text, chunk_size, chunk_overlap)
        elif strategy == 'token':
            return self._token_split(text, chunk_size, chunk_overlap)
        elif strategy == 'semantic':
            return self._semantic_split(text, chunk_size)
        elif strategy == 'recursive':
            return self._recursive_split(text, chunk_size, chunk_overlap)
        else:
            # 預設使用字符切分
            return self._character_split(text, chunk_size, chunk_overlap)

    def _character_split(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        """字符切分"""
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start = end - chunk_overlap
        return chunks

    def _token_split(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        """Token 切分(使用 tiktoken)"""
        try:
            encoding = tiktoken.get_encoding("cl100k_base")
            tokens = encoding.encode(text)
            
            chunks = []
            start = 0
            while start < len(tokens):
                end = start + chunk_size
                chunk_tokens = tokens[start:end]
                chunk_text = encoding.decode(chunk_tokens)
                chunks.append(chunk_text)
                start = end - chunk_overlap
            
            return chunks
        except Exception as e:
            print(f"Token 切分失敗,回退到字符切分: {str(e)}")
            return self._character_split(text, chunk_size * 4, chunk_overlap * 4)

    def _semantic_split(self, text: str, max_size: int) -> List[str]:
        """語義切分(基於句子)"""
        import re
        # 使用正則表達式按句子切分
        sentences = re.split(r'[。！？\n]+|[.!?\n]+', text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            if len(current_chunk) + len(sentence) <= max_size:
                current_chunk += sentence + "。"
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence + "。"
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks

    def _recursive_split(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        """遞歸切分(LangChain 風格)"""
        separators = ["\n\n", "\n", "。", ".", " ", ""]
        
        def split_with_separators(text: str, seps: List[str]) -> List[str]:
            if not seps:
                return self._character_split(text, chunk_size, chunk_overlap)
            
            sep = seps[0]
            if sep:
                splits = text.split(sep)
            else:
                splits = list(text)
            
            chunks = []
            current_chunk = ""
            
            for split in splits:
                if len(current_chunk) + len(split) + len(sep) <= chunk_size:
                    current_chunk += split + sep
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    
                    if len(split) > chunk_size:
                        # 如果單個分段太大,使用下一個分隔符
                        sub_chunks = split_with_separators(split, seps[1:])
                        chunks.extend(sub_chunks)
                        current_chunk = ""
                    else:
                        current_chunk = split + sep
            
            if current_chunk:
                chunks.append(current_chunk)
            
            return chunks
        
        return split_with_separators(text, separators)

    def get_embeddings(self, texts: List[str], provider: str = 'openai', model: str = 'text-embedding-3-small') -> np.ndarray:
        """使用指定的 AI 供應商或本地模型產生 Embeddings"""
        if provider == 'openai':
            return self._get_openai_embeddings(texts, model)
        elif provider == 'google':
            return self._get_google_embeddings(texts, model)
        elif provider == 'local':
            return self._get_local_embeddings(texts, model)
        else:
            raise ValueError(f"不支援的 Embedding 供應商: {provider}")

    def _get_openai_embeddings(self, texts: List[str], model: str) -> np.ndarray:
        """使用 OpenAI 產生 Embeddings"""
        if not self._openai_client:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("未設定 OPENAI_API_KEY")
            from openai import OpenAI
            self._openai_client = OpenAI(api_key=api_key)
            
        response = self._openai_client.embeddings.create(
            input=texts,
            model=model
        )
        embeddings = [data.embedding for data in response.data]
        return np.array(embeddings).astype('float32')

    def _get_google_embeddings(self, texts: List[str], model: str) -> np.ndarray:
        """使用 Google Gemini 產生 Embeddings"""
        if not self._google_api_key:
            raise ValueError("未設定 GOOGLE_API_KEY")
            
        import google.generativeai as genai
        genai.configure(api_key=self._google_api_key)
        
        # Google API 處理單個或多個 texts
        response = genai.embed_content(
            model=f"models/{model}",
            content=texts,
            task_type="retrieval_document"
        )
        
        return np.array(response['embedding']).astype('float32')

    def _get_local_embeddings(self, texts: List[str], model: str) -> np.ndarray:
        """使用本地 SentenceTransformers 產生 Embeddings"""
        if not self._local_model:
            from sentence_transformers import SentenceTransformer
            # 如果使用者沒指定具體模型,使用預設的多語言模型
            model_name = model if '/' in model or '-' in model else "paraphrase-multilingual-MiniLM-L12-v2"
            print(f"[RAG] 正在載入本地模型: {model_name}")
            self._local_model = SentenceTransformer(model_name)
            
        embeddings = self._local_model.encode(texts)
        return np.array(embeddings).astype('float32')

    def create_kb_index(self, kb_id: int, chunks: List[str], config: Dict[str, Any] = None):
        """為指定的知識庫建立 FAISS 索引,支援不同索引類型"""
        if not chunks:
            return
            
        # 獲取配置 (如果沒傳則去資料庫拿)
        if not config:
            config = self.get_kb_config(kb_id)
            
        provider = config.get('embedding_provider', 'openai')
        model = config.get('embedding_model', 'text-embedding-3-small')
        index_type = config.get('index_type', 'flat')
        
        print(f"[RAG] 建立索引 - Provider: {provider}, Model: {model}, Type: {index_type}")
        
        embeddings = self.get_embeddings(chunks, provider, model)
        dimension = embeddings.shape[1]
        
        # 根據 index_type 建立不同的索引
        if index_type == 'ivf':
            # IVF 需要訓練,適合中大規模數據
            nlist = min(len(chunks) // 4, 100) if len(chunks) > 10 else 1
            quantizer = faiss.IndexFlatL2(dimension)
            index = faiss.IndexIVFFlat(quantizer, dimension, nlist, faiss.METRIC_L2)
            index.train(embeddings)
        elif index_type == 'hnsw':
            # HNSW 圖索引,檢索速度極快
            index = faiss.IndexHNSWFlat(dimension, 32)
        else:
            # 預設 Flat 索引 (IndexFlatL2)
            index = faiss.IndexFlatL2(dimension)
            
        index.add(embeddings)
        
        # 儲存索引與對應的文本區塊
        kb_path = os.path.join(self.index_path, f"kb_{kb_id}.index")
        faiss.write_index(index, kb_path)
        
        # 儲存 metadata (包括 chunks 和使用的配置)
        metadata_path = os.path.join(self.index_path, f"kb_{kb_id}_metadata.pkl")
        with open(metadata_path, "wb") as f:
            pickle.dump({
                "chunks": chunks,
                "config": {
                    "provider": provider,
                    "model": model,
                    "index_type": index_type,
                    "dimension": dimension
                }
            }, f)
            
        # 更新快取
        self._indices[kb_id] = {"index": index, "chunks": chunks}

    def query_kb(self, kb_id: int, query: str, top_k: int = 3) -> List[str]:
        """在知識庫中檢索與查詢最相關的內容"""
        # 載入索引 (如果不在快取中)
        if kb_id not in self._indices:
            kb_path = os.path.join(self.index_path, f"kb_{kb_id}.index")
            metadata_path = os.path.join(self.index_path, f"kb_{kb_id}_metadata.pkl")
            # 兼容舊版命名
            old_chunks_path = os.path.join(self.index_path, f"kb_{kb_id}_chunks.pkl")
            
            if not os.path.exists(kb_path):
                return []
                
            index = faiss.read_index(kb_path)
            
            if os.path.exists(metadata_path):
                with open(metadata_path, "rb") as f:
                    meta = pickle.load(f)
                    chunks = meta["chunks"]
                    config = meta.get("config", {})
            elif os.path.exists(old_chunks_path):
                with open(old_chunks_path, "rb") as f:
                    chunks = pickle.load(f)
                    config = {}
            else:
                return []
                
            self._indices[kb_id] = {"index": index, "chunks": chunks, "config": config}
            
        index_data = self._indices[kb_id]
        index = index_data["index"]
        chunks = index_data["chunks"]
        config = index_data.get("config", {})
        
        # 如果是 IVF 索引,設定 nprobe
        if isinstance(index, faiss.IndexIVF):
            index.nprobe = 10
            
        # 產生查詢的 Embedding
        provider = config.get('provider', 'openai')
        model = config.get('model', 'text-embedding-3-small')
        query_embedding = self.get_embeddings([query], provider, model)
        
        # 進行搜尋
        distances, indices = index.search(query_embedding, top_k)
        
        results = []
        for i in indices[0]:
            if i != -1 and i < len(chunks):
                results.append(chunks[i])
                
        return results

# 全域單例
rag_service = RAGService()
