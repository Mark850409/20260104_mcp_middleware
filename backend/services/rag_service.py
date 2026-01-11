import os
import faiss
import numpy as np
import pickle
from typing import List, Dict, Any, Optional
from pypdf import PdfReader
from docx import Document
import tiktoken
from services.ai_client import AIClientFactory

class RAGService:
    def __init__(self, storage_path: str = "storage/rag"):
        self.storage_path = storage_path
        self.index_path = os.path.join(storage_path, "indices")
        self.files_path = os.path.join(storage_path, "files")
        
        # 確保目錄存在
        os.makedirs(self.index_path, exist_ok=True)
        os.makedirs(self.files_path, exist_ok=True)
        
        # 初始化 Embedding 模型 (預設使用 OpenAI)
        self.embedding_model = "text-embedding-3-small"
        self.ai_provider = "openai"
        
        # 快取已載入的索引
        self._indices = {}

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

    def split_text(self, text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
        """將長文本切分成較小的區塊 (Chunks)"""
        # 簡單的基於字符的切分，未來可優化為基於 Token 的切分
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start = end - chunk_overlap
        return chunks

    def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """使用 AI 供應商產生 Embeddings"""
        # 注意：這裡需要實作與 OpenAI/Google API 的介接
        # 由於 AIClientFactory 主要是做 Chat，我們可能需要擴充它或直接在這邊調用 SDK
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("未設定 OPENAI_API_KEY")
            
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        response = client.embeddings.create(
            input=texts,
            model=self.embedding_model
        )
        
        embeddings = [data.embedding for data in response.data]
        return np.array(embeddings).astype('float32')

    def create_kb_index(self, kb_id: int, chunks: List[str]):
        """為指定的知識庫建立 FAISS 索引"""
        if not chunks:
            return
            
        embeddings = self.get_embeddings(chunks)
        dimension = embeddings.shape[1]
        
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings)
        
        # 儲存索引與對應的文本區塊
        kb_path = os.path.join(self.index_path, f"kb_{kb_id}.index")
        faiss.write_index(index, kb_path)
        
        chunks_path = os.path.join(self.index_path, f"kb_{kb_id}_chunks.pkl")
        with open(chunks_path, "wb") as f:
            pickle.dump(chunks, f)
            
        # 更新快取
        self._indices[kb_id] = {"index": index, "chunks": chunks}

    def query_kb(self, kb_id: int, query: str, top_k: int = 3) -> List[str]:
        """在知識庫中檢索與查詢最相關的內容"""
        # 載入索引 (如果不在快取中)
        if kb_id not in self._indices:
            kb_path = os.path.join(self.index_path, f"kb_{kb_id}.index")
            chunks_path = os.path.join(self.index_path, f"kb_{kb_id}_chunks.pkl")
            
            if not os.path.exists(kb_path) or not os.path.exists(chunks_path):
                return []
                
            index = faiss.read_index(kb_path)
            with open(chunks_path, "rb") as f:
                chunks = pickle.load(f)
            self._indices[kb_id] = {"index": index, "chunks": chunks}
            
        index_data = self._indices[kb_id]
        index = index_data["index"]
        chunks = index_data["chunks"]
        
        # 產生查詢的 Embedding
        query_embedding = self.get_embeddings([query])
        
        # 進行搜尋
        distances, indices = index.search(query_embedding, top_k)
        
        results = []
        for i in indices[0]:
            if i != -1 and i < len(chunks):
                results.append(chunks[i])
                
        return results

# 全域單例
rag_service = RAGService()
