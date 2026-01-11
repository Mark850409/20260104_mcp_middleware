#!/bin/bash
set -e

echo "============================================================"
echo "Backend 容器啟動中..."
echo "============================================================"

# 等待數據庫服務就緒
echo ""
echo "等待數據庫服務啟動..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  if python -c "import pymysql; pymysql.connect(host='${DB_HOST}', port=int('${DB_PORT}'), user='${DB_USER}', password='${DB_PASSWORD}', database='${DB_NAME}')" 2>/dev/null; then
    echo "✓ 數據庫連接成功"
    break
  fi
  RETRY_COUNT=$((RETRY_COUNT + 1))
  echo "等待數據庫... ($RETRY_COUNT/$MAX_RETRIES)"
  sleep 1
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
  echo "❌ 數據庫連接超時，無法啟動應用"
  exit 1
fi

# 執行數據庫初始化腳本
echo ""
echo "============================================================"
echo "開始初始化數據庫..."
echo "============================================================"

echo ""
echo "[1/5] 建立基礎資料表 (conversations, messages)..."
if python init_db.py; then
  echo "✓ 基礎資料表初始化完成"
else
  echo "⚠ init_db.py 執行失敗或表已存在"
fi

echo ""
echo "[2/5] 建立 MCP Servers 資料表..."
if python create_mcp_servers_table.py; then
  echo "✓ MCP Servers 資料表初始化完成"
else
  echo "⚠ create_mcp_servers_table.py 執行失敗或表已存在"
fi

echo ""
echo "[3/5] 建立 LINE Bot 相關資料表..."
if python init_line_db.py; then
  echo "✓ LINE Bot 資料表初始化完成"
else
  echo "⚠ init_line_db.py 執行失敗或表已存在"
fi

# Step 4: 系統提示詞資料庫初始化
echo ""
echo "[4/5] 建立系統提示詞資料表..."
if python init_prompts_db.py; then
  echo "✓ 系統提示詞資料表初始化完成"
else
  echo "⚠ init_prompts_db.py 執行失敗或表已存在"
fi

# Step 5: RAG 資料庫初始化
echo ""
echo "[5/5] 建立 RAG 資料表..."
if python init_rag_db.py; then
  echo "✓ RAG 資料表初始化完成"
else
  echo "⚠ init_rag_db.py 執行失敗或表已存在"
fi

echo ""
echo "============================================================"
echo "✅ 數據庫初始化完成"
echo "============================================================"

# 啟動 Flask 應用
echo ""
echo "啟動 Flask 應用..."
echo "============================================================"
exec python app.py
