# GUI Dockerfile
FROM node:18-slim

# 設定工作目錄
WORKDIR /app

# 複製 package.json 和 package-lock.json
COPY package*.json ./

# 安裝相依套件
RUN npm install

# 複製應用程式碼
COPY . .

# 暴露開發伺服器端口
EXPOSE 8080

# 啟動 Vite 開發伺服器
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
