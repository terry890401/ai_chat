# AI 聊天服務

## 功能
- 使用者註冊、登入
- 建立對話
- 發送訊息，AI 串流回覆
- 查詢歷史對話

## 技術棧
- FastAPI
- PostgreSQL + SQLAlchemy
- JWT 認證
- OpenAI GPT-4o-mini
- Streaming 輸出

## 如何執行
1. 安裝套件：pip install -r requirements.txt
2. 設定 .env
3. 執行：uvicorn main:app --reload