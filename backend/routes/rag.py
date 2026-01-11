from flask import Blueprint, request, jsonify
import os
import pymysql
from werkzeug.utils import secure_filename
from services.rag_service import rag_service

rag_bp = Blueprint('rag', __name__)

# 資料庫連線設定
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'db'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'mcp_user'),
    'password': os.getenv('DB_PASSWORD', 'mcp_password'),
    'database': os.getenv('DB_NAME', 'mcp_platform'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    return pymysql.connect(**DB_CONFIG)

@rag_bp.route('/api/rag/kb', methods=['GET'])
def list_knowledge_bases():
    """取得所有知識庫清單"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM knowledge_bases WHERE is_active = TRUE")
            kbs = cursor.fetchall()
        conn.close()
        return jsonify({"success": True, "data": kbs})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@rag_bp.route('/api/rag/kb', methods=['POST'])
def create_knowledge_base():
    """建立新的知識庫"""
    data = request.get_json()
    name = data.get('name')
    description = data.get('description', '')
    
    if not name:
        return jsonify({"success": False, "error": "名稱為必填項目"}), 400
        
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = "INSERT INTO knowledge_bases (name, description) VALUES (%s, %s)"
            cursor.execute(sql, (name, description))
            kb_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return jsonify({"success": True, "data": {"id": kb_id, "name": name}})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@rag_bp.route('/api/rag/kb/<int:kb_id>', methods=['PUT', 'PATCH'])
def update_knowledge_base(kb_id):
    """更新知識庫名稱與描述"""
    data = request.get_json()
    name = data.get('name')
    description = data.get('description', '')
    
    if not name:
        return jsonify({"success": False, "error": "名稱為必填項目"}), 400
        
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = "UPDATE knowledge_bases SET name = %s, description = %s WHERE id = %s"
            cursor.execute(sql, (name, description, kb_id))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "已更新知識庫"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@rag_bp.route('/api/rag/kb/<int:kb_id>', methods=['DELETE'])
def delete_knowledge_base(kb_id):
    """刪除知識庫"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM knowledge_bases WHERE id = %s", (kb_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "已刪除知識庫"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@rag_bp.route('/api/rag/kb/<int:kb_id>/files', methods=['GET'])
def list_kb_files(kb_id):
    """取得特定知識庫的檔案清單"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 透過連結表 kb_files 取得該知識庫的檔案
            sql = """
                SELECT f.* 
                FROM files f
                JOIN kb_files kf ON f.id = kf.file_id
                WHERE kf.kb_id = %s
                ORDER BY f.created_at DESC
            """
            cursor.execute(sql, (kb_id,))
            files = cursor.fetchall()
        conn.close()
        return jsonify({"success": True, "data": files})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@rag_bp.route('/api/rag/files', methods=['GET'])
def list_files():
    """取得所有檔案清單"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM files ORDER BY created_at DESC")
            files = cursor.fetchall()
        conn.close()
        return jsonify({"success": True, "data": files})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@rag_bp.route('/api/rag/files/delete', methods=['POST'])
def delete_files():
    """批次刪除檔案"""
    data = request.get_json()
    file_ids = data.get('file_ids', [])
    
    if not file_ids:
        return jsonify({"success": False, "error": "未提供檔案 ID"}), 400
        
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 取得檔案路徑以從磁碟刪除
            cursor.execute("SELECT file_path FROM files WHERE id IN %s", (tuple(file_ids),))
            files = cursor.fetchall()
            
            for f in files:
                if f['file_path'] and os.path.exists(f['file_path']):
                    try:
                        os.remove(f['file_path'])
                    except:
                        pass
            
            # 從資料庫中刪除
            cursor.execute("DELETE FROM files WHERE id IN %s", (tuple(file_ids),))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": f"已刪除 {len(file_ids)} 個檔案"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@rag_bp.route('/api/rag/upload', methods=['POST'])
def upload_file():
    """上傳檔案並儲存至資料庫"""
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "未提供檔案"}), 400
        
    file = request.files['file']
    original_filename = file.filename
    
    if not original_filename:
        return jsonify({"success": False, "error": "檔案名稱無效"}), 400
    
    # 獲取副檔名
    file_ext = os.path.splitext(original_filename)[1].lower()
    file_type = file_ext.replace('.', '')
    
    # 檢查檔案類型
    allowed_extensions = ['.pdf', '.docx', '.txt', '.md']
    if file_ext not in allowed_extensions:
        return jsonify({
            "success": False, 
            "error": f"不支援的檔案類型: {file_ext}",
            "error_message": "不支援的檔案類型",
            "file_type": file_type
        }), 400
    
    import time
    # 使用時間戳 + 副檔名作為檔名,避免中文問題
    filename = f"{int(time.time())}{file_ext}"
    file_path = os.path.join(rag_service.files_path, filename)
    
    try:
        file.save(file_path)
        file_size = os.path.getsize(file_path)
        
        # 獲取 kb_id (如果前端有傳)
        kb_id = request.form.get('kb_id')
        
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """INSERT INTO files (name, file_path, file_type, size, status) 
                     VALUES (%s, %s, %s, %s, %s)"""
            cursor.execute(sql, (original_filename, file_path, file_type, file_size, 'pending'))
            file_id = cursor.lastrowid
            
            # 如果有提供 kb_id,立即建立關聯
            if kb_id:
                cursor.execute("INSERT IGNORE INTO kb_files (kb_id, file_id) VALUES (%s, %s)", (kb_id, file_id))
                
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True, 
            "data": {
                "id": file_id, 
                "name": original_filename,
                "file_type": file_type,
                "size": file_size
            }
        })
    except Exception as e:
        # 如果儲存失敗,刪除已上傳的檔案
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        return jsonify({"success": False, "error": str(e)}), 500

@rag_bp.route('/api/rag/kb/<int:kb_id>/process', methods=['POST'])
def process_kb_files(kb_id):
    """處理知識庫中待處理的檔案並建立索引"""
    data = request.get_json()
    file_ids = data.get('file_ids', [])
    
    if not file_ids:
        return jsonify({"success": False, "error": "請選擇要處理的檔案"}), 400
    
    try:
        # 獲取知識庫配置
        kb_config = rag_service.get_kb_config(kb_id)
        chunk_strategy = kb_config.get('chunk_strategy', 'character')
        chunk_size = kb_config.get('chunk_size', 500)
        chunk_overlap = kb_config.get('chunk_overlap', 50)
        
        print(f"[RAG] 處理配置 - 策略: {chunk_strategy}, 大小: {chunk_size}, 重疊: {chunk_overlap}")
        
        conn = get_db_connection()
        all_chunks = []
        
        with conn.cursor() as cursor:
            # 建立 KB 與檔案的關聯 (如果尚未建立)
            for f_id in file_ids:
                cursor.execute("INSERT IGNORE INTO kb_files (kb_id, file_id) VALUES (%s, %s)", (kb_id, f_id))
            
            # 取得檔案路徑
            cursor.execute("SELECT id, file_path, name FROM files WHERE id IN %s", (tuple(file_ids),))
            files = cursor.fetchall()
            
            for f in files:
                try:
                    # 更新狀態為處理中
                    cursor.execute("UPDATE files SET status = 'processing' WHERE id = %s", (f['id'],))
                    conn.commit()
                    
                    print(f"[RAG] 處理檔案: {f['name']}")
                    
                    # 提取文字
                    text = rag_service.extract_text(f['file_path'])
                    print(f"[RAG] 提取文字長度: {len(text)} 字元")
                    
                    # 使用配置的策略切分
                    chunks = rag_service.split_text(
                        text, 
                        strategy=chunk_strategy,
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap
                    )
                    print(f"[RAG] 切分完成,產生 {len(chunks)} 個 chunks")
                    
                    all_chunks.extend(chunks)
                    
                    # 更新狀態為已完成
                    cursor.execute("UPDATE files SET status = 'completed' WHERE id = %s", (f['id'],))
                except Exception as ex:
                    print(f"[RAG] 處理檔案失敗: {str(ex)}")
                    cursor.execute("UPDATE files SET status = 'failed', error_message = %s WHERE id = %s", 
                                   (str(ex), f['id']))
            
            # 建立向量索引
            if all_chunks:
                print(f"[RAG] 開始建立向量索引,共 {len(all_chunks)} 個 chunks")
                rag_service.create_kb_index(kb_id, all_chunks)
                print(f"[RAG] 向量索引建立完成")
                
        conn.commit()
        conn.close()
        return jsonify({
            "success": True, 
            "message": "檔案處理與索引建立完成",
            "chunks_count": len(all_chunks),
            "config": {
                "strategy": chunk_strategy,
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap
            }
        })
    except Exception as e:
        print(f"[RAG] 處理失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@rag_bp.route('/api/rag/kb/<int:kb_id>/config', methods=['GET'])
def get_kb_config_api(kb_id):
    """獲取知識庫配置"""
    try:
        config = rag_service.get_kb_config(kb_id)
        return jsonify({"success": True, "data": config})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@rag_bp.route('/api/rag/kb/<int:kb_id>/config', methods=['PUT'])
def update_kb_config_api(kb_id):
    """更新知識庫配置"""
    data = request.get_json()
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 檢查配置是否存在
            cursor.execute("SELECT id FROM kb_configs WHERE kb_id = %s", (kb_id,))
            exists = cursor.fetchone()
            
            if exists:
                # 更新現有配置
                update_fields = []
                values = []
                
                if 'chunk_strategy' in data:
                    update_fields.append("chunk_strategy = %s")
                    values.append(data['chunk_strategy'])
                
                if 'chunk_size' in data:
                    update_fields.append("chunk_size = %s")
                    values.append(data['chunk_size'])
                
                if 'chunk_overlap' in data:
                    update_fields.append("chunk_overlap = %s")
                    values.append(data['chunk_overlap'])
                
                if 'embedding_provider' in data:
                    update_fields.append("embedding_provider = %s")
                    values.append(data['embedding_provider'])
                
                if 'embedding_model' in data:
                    update_fields.append("embedding_model = %s")
                    values.append(data['embedding_model'])
                
                if 'retrieval_top_k' in data:
                    update_fields.append("retrieval_top_k = %s")
                    values.append(data['retrieval_top_k'])
                
                if 'index_type' in data:
                    update_fields.append("index_type = %s")
                    values.append(data['index_type'])
                
                if update_fields:
                    values.append(kb_id)
                    sql = f"UPDATE kb_configs SET {', '.join(update_fields)} WHERE kb_id = %s"
                    cursor.execute(sql, values)
            else:
                # 創建新配置
                cursor.execute("""
                    INSERT INTO kb_configs 
                    (kb_id, chunk_strategy, chunk_size, chunk_overlap, 
                     embedding_provider, embedding_model, index_type, retrieval_top_k)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    kb_id,
                    data.get('chunk_strategy', 'character'),
                    data.get('chunk_size', 500),
                    data.get('chunk_overlap', 50),
                    data.get('embedding_provider', 'openai'),
                    data.get('embedding_model', 'text-embedding-3-small'),
                    data.get('index_type', 'flat'),
                    data.get('retrieval_top_k', 3)
                ))
        
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "配置已更新"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
