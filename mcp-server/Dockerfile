# MCP Server Dockerfile - 多語言環境 (Python + Node.js + Docker)
FROM python:3.10-slim

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    ca-certificates \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# 安裝 Docker CLI (用於管理 NPX 容器)
RUN install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc \
    && chmod a+r /etc/apt/keyrings/docker.asc \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update \
    && apt-get install -y docker-ce-cli \
    && rm -rf /var/lib/apt/lists/*

# 安裝 Node.js 20.x LTS
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# 驗證安裝
RUN python --version && node --version && npm --version && docker --version

# 注意: 不設定 NPM_CONFIG_PREFIX,避免干擾 NPXDockerProvider 建立的子容器
# 子容器會使用自己的 npm 配置

# 設定工作目錄
WORKDIR /app

# 複製 requirements.txt
COPY requirements.txt .

# 安裝 Python 相依套件 (包含 docker-py)
RUN pip install --no-cache-dir -r requirements.txt docker

# 複製應用程式碼
COPY . .

# 暴露 MCP 服務端口
EXPOSE 8000

# 啟動 MCP Server
CMD ["python", "mcp_server_sse.py"]

