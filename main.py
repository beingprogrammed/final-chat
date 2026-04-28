import random
from typing import Dict, List
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from models import User, Message, OTPRequest, VerifyRequest
from database import get_session, init_db
import json

app = FastAPI()

# Temporary OTP storage: {phone_number: otp}
otp_storage: Dict[str, str] = {}

# Active WebSocket connections: {phone_number: WebSocket}
active_connections: Dict[str, WebSocket] = {}

@app.on_event("startup")
async def on_startup():
    await init_db()

@app.post("/request-otp")
async def request_otp(request: OTPRequest):
    otp = str(random.randint(100000, 999999))
    otp_storage[request.phone_number] = otp
    print(f"\n[BACKEND] OTP for {request.phone_number}: {otp}\n")
    return {"message": "OTP generated. Check server logs."}

@app.post("/verify-otp")
async def verify_otp(request: VerifyRequest, session: AsyncSession = Depends(get_session)):
    stored_otp = otp_storage.get(request.phone_number)
    if not stored_otp or stored_otp != request.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    # Check if user exists, else create
    statement = select(User).where(User.phone_number == request.phone_number)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(phone_number=request.phone_number, is_verified=True)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    
    # Remove OTP after verification
    del otp_storage[request.phone_number]
    
    return {"message": "Verified", "user_id": user.id}

@app.get("/messages/{phone1}/{phone2}")
async def get_messages(phone1: str, phone2: str, session: AsyncSession = Depends(get_session)):
    # Get user IDs
    stmt1 = select(User).where(User.phone_number == phone1)
    res1 = await session.execute(stmt1)
    user1 = res1.scalar_one_or_none()
    
    stmt2 = select(User).where(User.phone_number == phone2)
    res2 = await session.execute(stmt2)
    user2 = res2.scalar_one_or_none()
    
    if not user1 or not user2:
        return []
    
    # Fetch messages between them
    stmt = select(Message).where(
        ((Message.sender_id == user1.id) & (Message.receiver_id == user2.id)) |
        ((Message.sender_id == user2.id) & (Message.receiver_id == user1.id))
    ).order_by(Message.timestamp)
    
    res = await session.execute(stmt)
    messages = res.scalars().all()
    
    return [
        {
            "sender": phone1 if m.sender_id == user1.id else phone2,
            "content": m.content,
            "timestamp": str(m.timestamp)
        } for m in messages
    ]

@app.delete("/messages/{phone1}/{phone2}")
async def clear_messages(phone1: str, phone2: str, session: AsyncSession = Depends(get_session)):
    # Get user IDs
    stmt1 = select(User).where(User.phone_number == phone1)
    res1 = await session.execute(stmt1)
    user1 = res1.scalar_one_or_none()
    
    stmt2 = select(User).where(User.phone_number == phone2)
    res2 = await session.execute(stmt2)
    user2 = res2.scalar_one_or_none()
    
    if not user1 or not user2:
        return {"message": "Users not found"}
    
    # Delete messages between them
    from sqlmodel import delete
    stmt = delete(Message).where(
        ((Message.sender_id == user1.id) & (Message.receiver_id == user2.id)) |
        ((Message.sender_id == user2.id) & (Message.receiver_id == user1.id))
    )
    await session.execute(stmt)
    await session.commit()
    
    return {"message": "Chat cleared"}

@app.get("/contacts/{phone_number}")
async def get_contacts(phone_number: str, session: AsyncSession = Depends(get_session)):
    # Get user id
    stmt = select(User).where(User.phone_number == phone_number)
    res = await session.execute(stmt)
    user = res.scalar_one_or_none()
    
    if not user:
        return []
    
    # Query all messages involving this user
    stmt = select(Message).where(
        (Message.sender_id == user.id) | (Message.receiver_id == user.id)
    )
    res = await session.execute(stmt)
    messages = res.scalars().all()
    
    # Extract unique contact IDs
    contact_ids = set()
    for m in messages:
        if m.sender_id != user.id:
            contact_ids.add(m.sender_id)
        if m.receiver_id != user.id:
            contact_ids.add(m.receiver_id)
    
    if not contact_ids:
        return []
    
    # Fetch phone numbers for these IDs
    stmt = select(User.phone_number).where(User.id.in_(list(contact_ids)))
    res = await session.execute(stmt)
    contacts = res.scalars().all()
    
    return contacts

@app.websocket("/ws/{phone_number}")
async def websocket_endpoint(websocket: WebSocket, phone_number: str, session: AsyncSession = Depends(get_session)):
    await websocket.accept()
    active_connections[phone_number] = websocket
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            recipient_phone = message_data.get("recipient")
            content = message_data.get("content")
            
            # Save to database
            # 1. Get sender id
            statement = select(User).where(User.phone_number == phone_number)
            res = await session.execute(statement)
            sender = res.scalar_one()
            
            # 2. Get or create recipient
            statement = select(User).where(User.phone_number == recipient_phone)
            res = await session.execute(statement)
            recipient = res.scalar_one_or_none()
            
            if not recipient:
                # Create a placeholder user so we can save the message
                recipient = User(phone_number=recipient_phone, is_verified=False)
                session.add(recipient)
                await session.commit()
                await session.refresh(recipient)
            
            db_message = Message(
                sender_id=sender.id,
                receiver_id=recipient.id,
                content=content
            )
            session.add(db_message)
            await session.commit()
            
            # Forward to recipient if online
            if recipient_phone in active_connections:
                await active_connections[recipient_phone].send_text(json.dumps({
                    "sender": phone_number,
                    "content": content,
                    "timestamp": str(db_message.timestamp)
                }))
                
    except WebSocketDisconnect:
        if phone_number in active_connections:
            del active_connections[phone_number]

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
