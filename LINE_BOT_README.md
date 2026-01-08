# LINE BOT 整合指南

本專案已整合 LINE Messaging API,讓您可以將 AI Chatbot 與 MCP 工具串接到 LINE BOT。

## 快速開始

### 1. 資料庫遷移

```bash
cd backend
python init_line_db.py
```

### 2. 設定環境變數

在 `.env` 檔案中新增:

```bash
WEBHOOK_BASE_URL=https://your-domain.com
```

> 開發環境可使用 ngrok: `ngrok http 5000`

### 3. 啟動服務

```bash
docker-compose up -d
```

### 4. 設定 LINE BOT

1. 前往 [LINE Developers Console](https://developers.line.biz/)
2. 建立 Messaging API Channel
3. 取得 **Channel Access Token** 和 **Channel Secret**
4. 在後台管理介面 (http://localhost:8080) 點擊 "📱 LINE BOT"
5. 新增 LINE BOT 設定,填入上述資訊
6. 複製產生的 Webhook URL
7. 回到 LINE Developers Console,設定 Webhook URL
8. 啟用 Webhook 並關閉自動回覆

### 5. 測試

1. 掃描 QR Code 加入 BOT 好友
2. 發送訊息測試
3. 如果選擇了 MCP 工具,可以詢問相關問題 (例如: "台北今天天氣如何?")

## 功能特色

- ✅ 後台管理介面設定 LINE BOT
- ✅ 自動產生 Webhook URL
- ✅ 選擇要使用的 MCP 工具
- ✅ LINE 與後台聊天室訊息同步
- ✅ AI 自動呼叫 MCP 工具回應使用者
- ✅ 簽章驗證確保安全性

## 詳細說明

請參閱 [完整使用說明](walkthrough.md)

## 故障排除

### Webhook 驗證失敗

- 確認 backend 服務正在運行
- 確認 Webhook URL 可以從外部存取
- 檢查防火牆設定

### BOT 沒有回應

- 確認 BOT 已啟用 (在後台管理介面檢查開關)
- 檢查 backend 日誌: `docker-compose logs -f backend`
- 確認 Webhook 設定正確

## 注意事項

- LINE API 免費方案每月限制 500 則訊息
- Webhook URL 必須是公開可存取的 HTTPS 端點
- Channel Access Token 和 Channel Secret 是敏感資訊,請妥善保管

## 支援

- [LINE Messaging API 文件](https://developers.line.biz/en/docs/messaging-api/)
- [完整使用說明](walkthrough.md)
