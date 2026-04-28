# PROJECT REPORT

## ON

# TERMINAL BASED CHAT APPLICATION

**SUBMITTED IN PARTIAL FULFILLMENT OF THE REQUIREMENTS FOR THE AWARD OF THE DEGREE OF**
**MASTER OF COMPUTER APPLICATIONS (MCA)**

**SUBMITTED TO:**
**Department of Computer Science**
**Himachal Pradesh University, Shimla**

**SUBMITTED BY:**
**Name:** [Walker]
**Roll No:** [Your Roll Number]
**Batch:** 2024-2026

---

### **DECLARATION**

I hereby declare that the project work entitled **"Terminal Based Chat Application"** submitted to the Department of Computer Science, Himachal Pradesh University, Shimla, is a record of an original work done by me under the guidance of **[Guide Name]**. This project work has not been submitted to any other University or Institute for the award of any degree or diploma.

**Place:** Shimla
**Date:** 17 April 2026

**(Signature of the Student)**

---

### **CERTIFICATE**

This is to certify that the project entitled **"Terminal Based Chat Application"** is a bona fide work carried out by **[Walker]**, a student of MCA, Department of Computer Science, Himachal Pradesh University, Shimla, in partial fulfillment of the requirements for the award of the degree of Master of Computer Applications (MCA) during the academic year 2024-2026.

**Place:** Shimla
**Date:** 17 April 2026

**(Signature of Guide)**
**(Signature of Head of Department)**

---

### **ACKNOWLEDGEMENT**

I would like to express my deep sense of gratitude to my project guide **[Guide Name]** for their valuable guidance and constant encouragement throughout the development of this project.

I am also thankful to the faculty members of the Department of Computer Science, Himachal Pradesh University, for providing the necessary facilities and support.

Finally, I would like to thank my family and friends for their support and motivation.

**[Walker]**

---

### **ABSTRACT**

The **Terminal Based Chat Application** is a real-time communication tool designed for the command-line interface. Built using modern Python frameworks like **FastAPI** and **Textual**, it provides a "WhatsApp-like" experience within the terminal. The application supports mobile-number-based authentication using an OTP mechanism, persistent message history using **PostgreSQL**, and real-time message delivery via **WebSockets**. This project demonstrates the power of asynchronous programming in Python and the capabilities of modern Terminal User Interface (TUI) frameworks.

---

### **TABLE OF CONTENTS**

1. **Chapter 1: Introduction**
   - 1.1 Project Overview
   - 1.2 Objectives
   - 1.3 Scope of the Project
2. **Chapter 2: System Analysis**
   - 2.1 Problem Definition
   - 2.2 Feasibility Study
   - 2.3 Software Requirement Specification (SRS)
3. **Chapter 3: System Design**
   - 3.1 System Architecture
   - 3.2 Database Design
   - 3.3 Data Flow Diagrams
4. **Chapter 4: Implementation**
   - 4.1 Technologies Used
   - 4.2 Source Code
5. **Chapter 5: Testing**
   - 5.1 Test Plan
   - 5.2 Test Cases
6. **Chapter 6: Conclusion & Future Scope**
   - 6.1 Conclusion
   - 6.2 Future Enhancements
7. **Bibliography**

---

## **CHAPTER 1: INTRODUCTION**

### **1.1 Project Overview**

The project aims to develop a terminal-centric chat application that mimics the functionality of modern messaging apps like WhatsApp but resides entirely within the user's terminal. It focuses on simplicity, speed, and real-time interaction.

### **1.2 Objectives**

- To provide a secure login system using mobile numbers and OTP.
- To enable real-time message exchange between users.
- To maintain a persistent record of chat history.
- To offer a modern and intuitive Terminal User Interface (TUI).

### **1.3 Scope of the Project**

The current version of the application supports one-to-one text messaging. Future versions can include group chats, file transfers, and multimedia support.

---

## **CHAPTER 2: SYSTEM ANALYSIS**

### **2.1 Problem Definition**

Traditional chat applications are often bloated and resource-intensive. Developers and CLI enthusiasts often prefer staying within the terminal environment. This project addresses the need for a lightweight, CLI-based messaging tool.

### **2.2 Feasibility Study**

- **Technical Feasibility:** Python's FastAPI and Textual libraries provide all the necessary tools for WebSockets and TUI development.
- **Operational Feasibility:** The app is easy to use for anyone familiar with a terminal.

### **2.3 Software Requirement Specification (SRS)**

- **Operating System:** Linux / Windows / macOS
- **Language:** Python 3.10+
- **Frameworks:** FastAPI, Textual
- **Database:** PostgreSQL
- **Real-time Protocol:** WebSockets

---

## **CHAPTER 3: SYSTEM DESIGN**

### **3.1 System Architecture**

The system follows a Client-Server architecture. The server (FastAPI) handles authentication, database interactions, and message routing. The client (Textual) provides the user interface and maintains a WebSocket connection to the server.

### **3.2 Database Design**

The database consists of two primary tables:

- **User:** Stores `phone_number` and `verification_status`.
- **Message:** Stores `sender_id`, `receiver_id`, `content`, and `timestamp`.

### **3.3 Data Flow**

1. User enters Phone Number -> Server generates OTP.
2. User enters OTP -> Server verifies and grants access.
3. User sends Message -> Server saves to DB and forwards to recipient via WebSocket.

---

## **CHAPTER 4: IMPLEMENTATION**

### **4.1 Technologies Used**

- **FastAPI:** High-performance web framework for the backend.
- **SQLModel:** SQL database interaction using Python objects.
- **Asyncpg:** Asynchronous PostgreSQL driver.
- **Textual:** Reactive TUI framework for Python.
- **WebSockets:** Full-duplex communication protocol.

### **4.2 Source Code**

#### **main.py (Backend Server)**

```python
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
            statement = select(User).where(User.phone_number == phone_number)
            res = await session.execute(statement)
            sender = res.scalar_one()

            statement = select(User).where(User.phone_number == recipient_phone)
            res = await session.execute(statement)
            recipient = res.scalar_one_or_none()

            if recipient:
                db_message = Message(
                    sender_id=sender.id,
                    receiver_id=recipient.id,
                    content=content
                )
                session.add(db_message)
                await session.commit()

                if recipient_phone in active_connections:
                    await active_connections[recipient_phone].send_text(json.dumps({
                        "sender": phone_number,
                        "content": content,
                        "timestamp": str(db_message.timestamp)
                    }))
            else:
                await websocket.send_text(json.dumps({"error": "Recipient not found"}))

    except WebSocketDisconnect:
        if phone_number in active_connections:
            del active_connections[phone_number]

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
```

#### **client.py (TUI Application)**

```python
import asyncio
import json
import os
import httpx
import websockets
from dotenv import load_dotenv
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Input, Static, ListItem, ListView, Button
from textual.screen import Screen
from textual.reactive import reactive

load_dotenv()

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
WS_URL = os.getenv("WS_BASE_URL", "ws://localhost:8000/ws")

class LoginScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("Welcome to Terminal Chat", id="title"),
            Input(placeholder="Enter Phone Number", id="phone_input"),
            Input(placeholder="Enter OTP", id="otp_input", password=True),
            Button("Request OTP", variant="primary", id="request_btn"),
            Button("Login", variant="success", id="login_btn"),
            id="login_container"
        )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        phone = self.query_one("#phone_input", Input).value
        if event.button.id == "request_btn":
            async with httpx.AsyncClient() as client:
                await client.post(f"{BASE_URL}/request-otp", json={"phone_number": phone})
                self.notify("OTP requested! Check server console.")

        elif event.button.id == "login_btn":
            otp = self.query_one("#otp_input", Input).value
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{BASE_URL}/verify-otp", json={"phone_number": phone, "otp": otp})
                if response.status_code == 200:
                    self.app.user_phone = phone
                    self.app.push_screen(ChatScreen())
                else:
                    self.notify("Invalid OTP", severity="error")

class MessageItem(Static):
    def __init__(self, sender: str, content: str, is_self: bool):
        super().__init__()
        self.sender = sender
        self.content = content
        self.is_self = is_self

    def render(self) -> str:
        align = "right" if self.is_self else "left"
        color = "green" if self.is_self else "blue"
        return f"[{color}][{self.sender}]: {self.content}[/]"

class ContactItem(ListItem):
    def __init__(self, phone: str):
        super().__init__(Static(phone))
        self.phone = phone

class ChatScreen(Screen):
    messages = reactive([])

    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            Vertical(
                Static("Contacts"),
                ListView(id="contacts_list"),
                Input(placeholder="New Contact Phone", id="new_contact_input"),
                id="sidebar"
            ),
            Vertical(
                ListView(id="messages_list"),
                Input(placeholder="Type a message...", id="message_input"),
                id="chat_area"
            )
        )
        yield Footer()

    async def on_mount(self) -> None:
        self.websocket = await websockets.connect(f"{WS_URL}/{self.app.user_phone}")
        asyncio.create_task(self.receive_messages())

    async def receive_messages(self):
        try:
            async for message in self.websocket:
                data = json.loads(message)
                sender = data.get("sender")
                content = data.get("content")
                if sender == self.app.current_recipient:
                    self.query_one("#messages_list", ListView).append(ListItem(MessageItem(sender, content, False)))
                else:
                    self.notify(f"New message from {sender}")
        except:
            pass

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "message_input":
            content = event.value
            recipient = self.app.current_recipient
            if not recipient:
                self.notify("Select a recipient first", severity="warning")
                return

            await self.websocket.send(json.dumps({
                "recipient": recipient,
                "content": content
            }))
            self.query_one("#messages_list", ListView).append(ListItem(MessageItem("Me", content, True)))
            event.input.value = ""

        elif event.input.id == "new_contact_input":
            phone = event.value
            if phone:
                self.query_one("#contacts_list", ListView).append(ContactItem(phone))
                event.input.value = ""

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id == "contacts_list" and isinstance(event.item, ContactItem):
            self.app.current_recipient = event.item.phone
            self.notify(f"Chatting with {self.app.current_recipient}")

            async with httpx.AsyncClient() as client:
                response = await client.get(f"{BASE_URL}/messages/{self.app.user_phone}/{self.app.current_recipient}")
                if response.status_code == 200:
                    history = response.json()
                    messages_list = self.query_one("#messages_list", ListView)
                    messages_list.clear()
                    for msg in history:
                        is_self = msg["sender"] == self.app.user_phone
                        sender_label = "Me" if is_self else msg["sender"]
                        messages_list.append(ListItem(MessageItem(sender_label, msg["content"], is_self)))

class ChatApp(App):
    CSS = """
    #login_container { align: center middle; padding: 2; }
    #title { text-align: center; margin-bottom: 1; text-style: bold; }
    #sidebar { width: 30; border-right: tall white; }
    #chat_area { width: 1fr; }
    #messages_list { height: 1fr; }
    Input { margin: 1 0; }
    """
    user_phone = None
    current_recipient = None

    def on_mount(self) -> None:
        self.push_screen(LoginScreen())

if __name__ == "__main__":
    app = ChatApp()
    app.run()
```

#### **models.py (Database Models)**

```python
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
```

#### **database.py (Database Connection)**

```python
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL, echo=True, future=True)

async def init_db():
    from models import SQLModel
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session() -> AsyncSession:
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
```

---

(finalchatvenv)   final-chat python client.py
╭────────────────────────────────────── Traceback (most recent call last) ───────────────────────────────────────╮
│ /run/media/walker/data-volume/HPU/MCA2/Python/Projects/final-chat/client.py:111 in on_list_view_selected │
│ │
│ 108 │ async def on_list_view_selected(self, event: ListView.Selected) -> None: │
│ 109 │ │ if event.list_view.id == "contacts_list": │
│ 110 │ │ │ # Extract phone from static text │
│ ❱ 111 │ │ │ self.app.current_recipient = str(event.item.children[0].renderable) │
│ 112 │ │ │ self.notify(f"Chatting with {self.app.current_recipient}") │
│ 113 │ │ │ │
│ 114 │ │ │ # Load history │
│ │
│ ╭─────── locals ───────╮ │
│ │ event = Selected() │ │
│ │ self = ChatScreen() │ │
│ ╰──────────────────────╯ │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
AttributeError: 'Static' (finalchatvenv)   final-chat python client.py
╭────────────────────────────────────── Traceback (most recent call last) ───────────────────────────────────────╮
│ /run/media/walker/data-volume/HPU/MCA2/Python/Projects/final-chat/client.py:111 in on_list_view_selected │
│ │
│ 108 │ async def on_list_view_selected(self, event: ListView.Selected) -> None: │
│ 109 │ │ if event.list_view.id == "contacts_list": │
│ 110 │ │ │ # Extract phone from static text │
│ ❱ 111 │ │ │ self.app.current_recipient = str(event.item.children[0].renderable) │
│ 112 │ │ │ self.notify(f"Chatting with {self.app.current_recipient}") │
│ 113 │ │ │ │
│ 114 │ │ │ # Load history │
│ │
│ ╭─────── locals ───────╮ │
│ │ event = Selected() │ │
│ │ self = ChatScreen() │ │
│ ╰──────────────────────╯ │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
AttributeError: 'Static' object has no attribute 'renderable'
(finalchatvenv)   final-chat object has no attribute 'renderable'
(finalchatvenv)   final-chat

## **CHAPTER 5: TESTING**

### **5.1 Test Plan**

Testing was conducted manually by running the server and two client instances simultaneously.

### **5.2 Test Cases**

- **Test Case 1:** Request OTP -> Result: Success (OTP printed on console).
- **Test Case 2:** Verify OTP (Correct) -> Result: Success (Redirected to Chat).
- **Test Case 3:** Verify OTP (Incorrect) -> Result: Failure (Error notification).
- **Test Case 4:** Send Message -> Result: Success (Message appeared on recipient's terminal).
- **Test Case 5:** Persistence -> Result: Success (Reloading app showed old(finalchatvenv)   final-chat python client.py
  ╭────────────────────────────────────── Traceback (most recent call last) ───────────────────────────────────────╮
  │ /run/media/walker/data-volume/HPU/MCA2/Python/Projects/final-chat/client.py:111 in on_list_view_selected │
  │ │
  │ 108 │ async def on_list_view_selected(self, event: ListView.Selected) -> None: │
  │ 109 │ │ if event.list_view.id == "contacts_list": │
  │ 110 │ │ │ # Extract phone from static text │
  │ ❱ 111 │ │ │ self.app.current_recipient = str(event.item.children[0].renderable) │
  │ 112 │ │ │ self.notify(f"Chatting with {self.app.current_recipient}") │
  │ 113 │ │ │ │
  │ 114 │ │ │ # Load history │
  │ │
  │ ╭─────── locals ───────╮ │
  │ │ event = Selected() │ │
  │ │ self = ChatScreen() │ │
  │ ╰──────────────────────╯ │
  ╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
  AttributeError: 'Static' object has no attribute 'renderable'
  (finalchatvenv)   final-chat messages).

---

## **CHAPTER 6: CONCLUSION & FUTURE SCOPE**

### **6.1 Conclusion**

The project successfully implemented a terminal-based chat application with all requested features. It demonstrates that terminal applications can be just as interactive and capable as their GUI counterparts.

### **6.2 Future Enhancements**

- Implementation of Group Chats.
- End-to-End Encryption for messages.
- Support for file sharing.
- User profile customization.

---

## **BIBLIOGRAPHY**

1. FastAPI Documentation: https://fastapi.tiangolo.com/
2. Textual Documentation: https://textual.textualize.io/
3. SQLModel Documentation: https://sqlmodel.tiangolo.com/
4. Python WebSockets: https://websockets.readthedocs.io/
