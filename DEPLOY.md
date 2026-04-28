# Deployment Guide (Render)

This guide explains how to deploy your FastAPI backend to **Render** and connect your terminal client to it.

## 1. Prepare for Deployment

### Update `main.py`
Render requires the application to listen on a port provided by an environment variable. Your `main.py` already uses `0.0.0.0`, but we need to ensure it uses the `PORT` environment variable.

Update the bottom of `main.py`:
```python
if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
```

### Create `runtime.txt` (Optional)
Specify your Python version for Render:
```text
python-3.11.0
```

## 2. Push to GitHub
Render deploys directly from GitHub.
1. Create a new repository on GitHub.
2. Initialize git in your project:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```

## 3. Deploy Backend on Render
1. Log in to [Render.com](https://render.com).
2. Click **New +** and select **Web Service**.
3. Connect your GitHub repository.
4. **Settings**:
   - **Name**: `my-terminal-chat`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. **Environment Variables**:
   Click **Advanced** -> **Add Environment Variable**:
   - `DATABASE_URL`: Your External Database URL (See step 4).
   - `SECRET_KEY`: A long random string.
   - `API_BASE_URL`: (Not needed for backend).
   - `WS_BASE_URL`: (Not needed for backend).

## 4. Setup Database (Render PostgreSQL)
You cannot use your `localhost` Postgres on Render.
1. On Render, click **New +** and select **PostgreSQL**.
2. Once created, copy the **Internal Database URL** (if backend is on Render) or **External Database URL**.
3. Go back to your Web Service -> Environment Variables and paste this into `DATABASE_URL`.
   *Note: Change the start of the URL from `postgres://` to `postgresql+asyncpg://` to match what the app expects.*

## 5. Update Local Client
Once your backend is live (e.g., `https://my-chat.onrender.com`), update your local `.env` file:

```env
API_BASE_URL=https://my-chat.onrender.com
WS_BASE_URL=wss://my-chat.onrender.com/ws
```
*Note: Use `wss://` for secure WebSockets on Render.*

## 6. Run
Now you can run `python client.py` on your machine, and it will communicate with the server on Render!
