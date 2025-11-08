# main.py
import os

import requests
from fastapi import FastAPI, Request
from dotenv import load_dotenv

# load env file
load_dotenv()

from services.scheduler import start_scheduler
from services.telegram_service import handle_telegram_update, set_bot_commands
from services.tmdb_service import check_validation

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("TELEGRAM_WEBHOOK_URL")  
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = FastAPI(title="Movie Tracker API")

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/webhook")
async def telegram_webhook(request: Request) -> dict:
    """Telegram webhook endpoint"""
    update = await request.json()
    handle_telegram_update(update)
    return {"ok": True}

@app.get("/set_webhook")
def set_webhook() -> dict:
    set_bot_commands()
    r = requests.post(f'''{BASE_URL}/setWebhook''', json={"url": f'''{WEBHOOK_URL}/webhook'''})
    return r.json()

@app.on_event("startup")
def on_startup():
    start_scheduler()