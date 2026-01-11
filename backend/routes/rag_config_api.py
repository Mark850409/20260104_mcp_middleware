@rag_bp.route('/api/rag/kb/<int:kb_id>/config', methods=['GET'])
def get_kb_config(kb_id):
    """獲取知識庫配置"""
    try:
        config = rag_service.get_kb_config(kb_id)
        return jsonify({"success": True, "data": config})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@rag_bp.route('/api/rag/kb/<int:kb_id>/config', methods=['PUT'])
def update_kb_config(kb_id):
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
                
                if update_fields:
                    values.append(kb_id)
                    sql = f"UPDATE kb_configs SET {', '.join(update_fields)} WHERE kb_id = %s"
                    cursor.execute(sql, values)
            else:
                # 創建新配置
                cursor.execute("""
                    INSERT INTO kb_configs 
                    (kb_id, chunk_strategy, chunk_size, chunk_overlap, 
                     embedding_provider, embedding_model, retrieval_top_k)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    kb_id,
                    data.get('chunk_strategy', 'character'),
                    data.get('chunk_size', 500),
                    data.get('chunk_overlap', 50),
                    data.get('embedding_provider', 'openai'),
                    data.get('embedding_model', 'text-embedding-3-small'),
                    data.get('retrieval_top_k', 3)
                ))
        
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "配置已更新"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
