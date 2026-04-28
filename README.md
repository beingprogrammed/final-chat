# Terminal WebSocket Chat (WhatsApp Style)

A modern, terminal-based chat application built with **FastAPI** (Backend) and **Textual** (TUI Frontend). It features mobile-number-based login with OTP verification and persistent message history using **PostgreSQL**.

## Features
- 📱 **Phone Number Login**: Simple login using phone numbers.
- 🔑 **Console OTP**: OTP is generated and displayed in the server terminal for security/simplicity.
- 💬 **Real-time Messaging**: Uses WebSockets for instant message delivery.
- 📜 **Chat History**: All messages are saved in PostgreSQL and reloaded when you click a contact.
- 🖥️ **Modern TUI**: A beautiful terminal interface with a sidebar and message alignment.

## Prerequisites
- **Python 3.10+**
- **PostgreSQL** installed and running.

## Setup Instructions

### 1. Database Setup
Create a database named `chat_db` in your PostgreSQL instance:
```bash
# In your terminal or psql console
CREATE DATABASE chat_db;
```

### 2. Environment Configuration
Create a `.env` file in the root directory (I have already created a template for you). Ensure it contains your Postgres credentials:
```env
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/chat_db
SECRET_KEY=any_random_string
```
*Note: If you don't have a password for the `postgres` user, use `postgresql+asyncpg://postgres@localhost:5432/chat_db`.*

### 3. Installation
Install the required Python packages:
```bash
pip install -r requirements.txt
```

## How to Run

### Step 1: Start the Backend
```bash
python main.py
```
*Keep this terminal open! This is where you will see the OTP codes.*

### Step 2: Start the Client(s)
Open a new terminal (or two for testing) and run:
```bash
python client.py
```

## How to Use
1. **Login**: 
   - Enter your phone number in the client.
   - Click **"Request OTP"**.
   - Copy the 6-digit code from the **Backend Terminal**.
   - Enter it in the client and click **"Login"**.
2. **Add Contacts**:
   - In the sidebar, type the phone number of the person you want to chat with in the "New Contact Phone" box and press **Enter**.
3. **Chatting**:
   - Click on a contact in the sidebar list.
   - Type your message in the input box at the bottom and press **Enter**.

## Tech Stack
- **FastAPI**: Backend API & WebSocket management.
- **SQLModel**: ORM for PostgreSQL.
- **Asyncpg**: Asynchronous PostgreSQL driver.
- **Textual**: Modern Terminal UI framework.
- **Websockets**: Real-time communication protocol.
