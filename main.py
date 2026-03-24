from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import engine, get_db, Base
from models import User, Conversation, Message
from schemas import (
    UserCreate, UserResponse,
    LoginRequest, TokenResponse,
    ConversationCreate, ConversationResponse,
    MessageCreate, MessageResponse
)
from auth import hash_password, verify_password, create_token, verify_token
from llm import get_ai_reply_stream

# 啟動時自動建立資料表
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI 聊天服務")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================
# 使用者
# =====================

@app.post("/register", response_model=UserResponse)
def register(req: UserCreate, db: Session = Depends(get_db)):
    # 檢查 email 是否已存在
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="Email 已被使用")

    user = User(
        email=req.email,
        password_hash=hash_password(req.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@app.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="帳號或密碼錯誤")

    token = create_token({"user_id": user.id, "email": user.email})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/me", response_model=UserResponse)
def get_me(payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    return user

# =====================
# 對話
# =====================

@app.post("/conversations", response_model=ConversationResponse)
def create_conversation(
    req: ConversationCreate,
    payload: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    conv = Conversation(user_id=payload["user_id"], title=req.title)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv

@app.get("/conversations", response_model=list[ConversationResponse])
def get_conversations(
    payload: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    return db.query(Conversation).filter(
        Conversation.user_id == payload["user_id"]
    ).all()

# =====================
# 訊息
# =====================

@app.post("/conversations/{conversation_id}/messages")
def send_message(
    conversation_id: int,
    req: MessageCreate,
    payload: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    # 確認對話存在且屬於這個使用者
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == payload["user_id"]
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="找不到對話")

    # 存使用者的訊息
    user_msg = Message(
        conversation_id=conversation_id,
        role="user",
        content=req.content
    )
    db.add(user_msg)
    db.commit()

    # 從資料庫讀取對話歷史
    history = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).all()

    # 組裝 messages
    messages = [{"role": "system", "content": "你是一個友善的 AI 助手"}]
    for msg in history:
        messages.append({"role": msg.role, "content": msg.content})

    # Streaming 回覆
    full_reply = ""

    def generate():
        nonlocal full_reply
        for chunk in get_ai_reply_stream(messages):
            full_reply += chunk
            yield chunk

        # Streaming 結束後存 AI 的回覆
        ai_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=full_reply
        )
        db.add(ai_msg)
        db.commit()

    return StreamingResponse(generate(), media_type="text/plain")

@app.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
def get_messages(
    conversation_id: int,
    payload: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == payload["user_id"]
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="找不到對話")

    return db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).all()