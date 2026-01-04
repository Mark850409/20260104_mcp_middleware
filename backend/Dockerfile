# Backend API Dockerfile
FROM python:3.10-slim

# 安裝 curl (用於健康檢查)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# 設定工作目錄
WORKDIR /app

# 複製 requirements.txt
COPY requirements.txt .

# 安裝 Python 相依套件
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY . .

# 暴露 Flask API 端口
EXPOSE 5000

# 啟動 Flask 應用
CMD ["python", "app.py"]
