from datetime import datetime
from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    phone_number: str = Field(index=True, unique=True)
    is_verified: bool = Field(default=False)
    
    sent_messages: List["Message"] = Relationship(
        back_populates="sender", 
        sa_relationship_kwargs={"primaryjoin": "User.id==Message.sender_id"}
    )
    received_messages: List["Message"] = Relationship(
        back_populates="receiver", 
        sa_relationship_kwargs={"primaryjoin": "User.id==Message.receiver_id"}
    )

class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sender_id: int = Field(foreign_key="user.id")
    receiver_id: int = Field(foreign_key="user.id")
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    sender: User = Relationship(
        back_populates="sent_messages", 
        sa_relationship_kwargs={"primaryjoin": "Message.sender_id==User.id"}
    )
    receiver: User = Relationship(
        back_populates="received_messages", 
        sa_relationship_kwargs={"primaryjoin": "Message.receiver_id==User.id"}
    )

class OTPRequest(SQLModel):
    phone_number: str

class VerifyRequest(SQLModel):
    phone_number: str
    otp: str
