from pydantic import BaseModel,Field
from datetime import datetime

# User
class UserCreate(BaseModel):
    email: str
    password: str = Field(min_length=6)

class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime

    class Config:
        from_attributes = True

# Auth
class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Conversation
class ConversationCreate(BaseModel):
    title: str = "新對話"

class ConversationResponse(BaseModel):
    id: int
    title: str
    created_at: datetime

    class Config:
        from_attributes = True

# Message
class MessageCreate(BaseModel):
    content: str = Field(min_length=1)

class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributed = True