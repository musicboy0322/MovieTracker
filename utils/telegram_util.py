# utils/telegram_util.py
import os
import time

from dotenv import load_dotenv
import requests

# load env file
load_dotenv()

# initialize settings
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def generate_genre_inline_keyboard(genre_dict: dict, row_size: int = 2) -> dict:
    inline_keyboard = []
    row = []
    for genre_id, genre_name in genre_dict.items():
        button = {
            "text": genre_name,
            "callback_data": f"genre_{genre_id}"
        }
        row.append(button)
        if len(row) == row_size:
            inline_keyboard.append(row)
            row = []
    if row:
        inline_keyboard.append(row)

    return {"inline_keyboard": inline_keyboard}   

def send_message(chat_id: int, text: str, inline_keyboard: dict | None = None):
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    if inline_keyboard:
        payload["reply_markup"] = inline_keyboard
    requests.post(f"{BASE_URL}/sendMessage", json=payload)

def send_photo(chat_id: int, photo_url: str, caption: str, inline_keyboard: dict | None = None):
    payload = {
        "chat_id": chat_id,
        "photo": photo_url,
        "caption": caption,
        "parse_mode": "HTML"
    }
    if inline_keyboard:
        payload["reply_markup"] = inline_keyboard

    r = requests.post(f"{BASE_URL}/sendPhoto", json=payload)
    time.sleep(0.3)
    return r