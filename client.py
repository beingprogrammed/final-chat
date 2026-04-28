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
                Horizontal(
                    Static("Select a contact to start chatting", id="chat_title"),
                    Button("Clear Chat", variant="error", id="clear_btn"),
                    id="chat_header"
                ),
                ListView(id="messages_list"),
                Input(placeholder="Type a message...", id="message_input"),
                id="chat_area"
            )
        )
        yield Footer()

    async def on_mount(self) -> None:
        self.websocket = await websockets.connect(f"{WS_URL}/{self.app.user_phone}")
        asyncio.create_task(self.receive_messages())
        
        # Load contacts
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/contacts/{self.app.user_phone}")
            if response.status_code == 200:
                contacts = response.json()
                contacts_list = self.query_one("#contacts_list", ListView)
                for phone in contacts:
                    contacts_list.append(ContactItem(phone))

    async def receive_messages(self):
        try:
            async for message in self.websocket:
                data = json.loads(message)
                sender = data.get("sender")
                content = data.get("content")
                
                # Check if contact is already in the list
                contacts_list = self.query_one("#contacts_list", ListView)
                already_in_contacts = False
                for item in contacts_list.children:
                    if isinstance(item, ContactItem) and item.phone == sender:
                        already_in_contacts = True
                        break
                
                # If it's a new contact, add them to the sidebar automatically
                if not already_in_contacts:
                    contacts_list.append(ContactItem(sender))

                # Only show message if it's from the current recipient
                if sender == self.app.current_recipient:
                    self.query_one("#messages_list", ListView).append(ListItem(MessageItem(sender, content, False)))
                else:
                    self.notify(f"New message from {sender}")
        except:
            pass

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "clear_btn":
            if not self.app.current_recipient:
                self.notify("No contact selected", severity="warning")
                return
            
            async with httpx.AsyncClient() as client:
                response = await client.delete(f"{BASE_URL}/messages/{self.app.user_phone}/{self.app.current_recipient}")
                if response.status_code == 200:
                    self.query_one("#messages_list", ListView).clear()
                    self.notify("Chat cleared from database")

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
            self.query_one("#chat_title", Static).update(f"Chatting with {self.app.current_recipient}")
            
            # Load history
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
    #login_container {
        align: center middle;
        padding: 2;
    }
    #title {
        text-align: center;
        margin-bottom: 1;
        text-style: bold;
    }
    #sidebar {
        width: 30;
        border-right: tall white;
    }
    #chat_area {
        width: 1fr;
    }
    #chat_header {
        height: 3;
        background: $boost;
        padding: 0 1;
        align: left middle;
    }
    #chat_title {
        width: 1fr;
        padding-top: 1;
    }
    #clear_btn {
        margin-top: 0;
    }
    #messages_list {
        height: 1fr;
    }
    Input {
        margin: 1 0;
    }
    """
    user_phone = None
    current_recipient = None

    def on_mount(self) -> None:
        self.push_screen(LoginScreen())

if __name__ == "__main__":
    app = ChatApp()
    app.run()
