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
    filename = secure_filename(file.filename)
    import time
    # 增加時間戳避免重複檔名
    filename = f"{int(time.time())}_{filename}"
    file_path = os.path.join(rag_service.files_path, filename)
    file.save(file_path)
    
    file_size = os.path.getsize(file_path)
    file_type = os.path.splitext(filename)[1].replace('.', '')
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """INSERT INTO files (name, file_path, file_type, size, status) 
                     VALUES (%s, %s, %s, %s, %s)"""
            cursor.execute(sql, (original_filename, file_path, file_type, file_size, 'pending'))
            file_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return jsonify({"success": True, "data": {"id": file_id, "name": original_filename}})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@rag_bp.route('/api/rag/kb/<int:kb_id>/process', methods=['POST'])
def process_kb_files(kb_id):
    """處理知識庫中待處理的檔案並建立索引"""
    data = request.get_json()
    file_ids = data.get('file_ids', [])
    
    if not file_ids:
        return jsonify({"success": False, "error": "請選擇要處理的檔案"}), 400
        
    try:
        conn = get_db_connection()
        all_chunks = []
        
        with conn.cursor() as cursor:
            # 建立 KB 與檔案的關聯 (如果尚未建立)
            for f_id in file_ids:
                cursor.execute("INSERT IGNORE INTO kb_files (kb_id, file_id) VALUES (%s, %s)", (kb_id, f_id))
            
            # 取得檔案路徑
            cursor.execute("SELECT id, file_path FROM files WHERE id IN %s", (tuple(file_ids),))
            files = cursor.fetchall()
            
            for f in files:
                try:
                    # 更新狀態為處理中
                    cursor.execute("UPDATE files SET status = 'processing' WHERE id = %s", (f['id'],))
                    conn.commit()
                    
                    # 提取文字並切分
                    text = rag_service.extract_text(f['file_path'])
                    chunks = rag_service.split_text(text)
                    all_chunks.extend(chunks)
                    
                    # 更新狀態為已完成
                    cursor.execute("UPDATE files SET status = 'completed' WHERE id = %s", (f['id'],))
                except Exception as ex:
                    cursor.execute("UPDATE files SET status = 'failed', error_message = %s WHERE id = %s", 
                                   (str(ex), f['id']))
            
            # 建立向量索引
            if all_chunks:
                rag_service.create_kb_index(kb_id, all_chunks)
                
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "檔案處理與索引建立完成"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
