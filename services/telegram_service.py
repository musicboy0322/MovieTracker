# services/telegram_service.py
import os

import requests

from services.tmdb_service import get_upcoming, get_upcoming_by_genre, GENRE_DICT
from utils.tmdb_util import find_genre
from utils.telegram_util import generate_genre_inline_keyboard, send_message, send_photo
from db.database import Database

# initialize settings
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
GENRE_INLINE_KEYBOARD = generate_genre_inline_keyboard(GENRE_DICT) 
REGION_INLINE_KEYBOARD = {
    "inline_keyboard": [
        [
            {"text": "US", "callback_data": "region_US"},
            {"text": "CA", "callback_data": "region_CA"}
        ],
    ]
}

# initialize variables
db = Database()
user_movie_cache = {}

# --- functions ---
def handle_telegram_update(update: dict):
    # situation of callback query
    if "callback_query" in update:
        query = update["callback_query"]
        chat_id = query["message"]["chat"]["id"]
        data = query["data"]
        requests.post(f"{BASE_URL}/answerCallbackQuery", json={
            "callback_query_id": query["id"]
        })

        # region choosing
        if data.startswith("region_"):
            region = data.split("_")[1]
            send_message(chat_id, f"Your region is: {region}")
            db.add_user(chat_id, region)
            return

        # genre choosing
        elif data.startswith("genre_"):
            genre_id = data.split("_")[1]
            genre = find_genre(GENRE_DICT, genre_id)
            send_message(chat_id, f"Searching the upcoming movie of {genre}")
            region_id = db.get_user_region(chat_id) or "US"
            try:
                data = get_upcoming_by_genre(genre_id, region_id)
                movies = data["movies"]
                if not movies:
                    send_message(chat_id, "Can't find any upcoming of this genre")
                    return
                user_movie_cache[chat_id] = {
                    "movies": movies,
                    "index": 0,
                    "page": 1,
                    "region": region_id,
                    "mode": f"genre_{genre_id}" 
                }
                _send_local_movie_page(chat_id, movies, start=0)
            except Exception as e:
                send_message(chat_id, f"Failure: {e}")
            return
        
        # next page
        elif data.startswith("next_"):
            start = int(data.split("_")[1])
            cache = user_movie_cache.get(chat_id)

            if not cache:
                send_message(chat_id, "⚠️ Please type /upcoming or /upcoming_genre again to refresh list.")
                return

            movies = cache["movies"]
            region = cache["region"]
            page = cache["page"]
            mode = cache.get("mode", "all")  

            if start >= len(movies):
                try:
                    next_page = page + 1

                    if mode.startswith("genre_"):
                        genre_id = mode.split("_")[1]
                        data = get_upcoming_by_genre(genre_id, region, next_page)
                    else:
                        data = get_upcoming(region, next_page)

                    new_movies = data["movies"]

                    if not new_movies:
                        send_message(chat_id, f'''📭 No more upcoming movies available in {region}.''')
                        return

                    user_movie_cache[chat_id] = {
                        "movies": new_movies,
                        "index": 0,
                        "page": next_page,
                        "region": region,
                        "mode": mode
                    }
                    send_message(chat_id, f"📄 Loading page {next_page} ...")
                    _send_local_movie_page(chat_id, new_movies, start=0)

                except Exception as e:
                    send_message(chat_id, f"❌ Failed to fetch next page: {e}")
                return

            _send_local_movie_page(chat_id, movies, start)
            return
        
        elif data.startswith("detail_"):
            movie_id = int(data.split("_")[1])
            cache = user_movie_cache.get(chat_id)
            if not cache:
                send_message(chat_id, "⚠️ Please search movies first (/upcoming or /upcoming_genre)")
                return

            movies = cache["movies"]
            target = next((m for m in movies if m["id"] == movie_id), None)
            if not target:
                send_message(chat_id, "⚠️ Movie not found in current list.")
                return

            g = ", ".join(target["genres"]) if target.get("genres") else "N/A"
            caption = (
                f"🎬 <b>{target['title']}</b>\n"
                f"📅 {target['release_date']}\n"
                f"🎭 {g}\n\n"
            )

            if target.get("poster"):
                send_photo(chat_id, target["poster"], caption)
            else:
                send_message(chat_id, caption)
            return

        return 
    
    # situation of unknown
    if "message" not in update:
        return

    # situation of message
    message = update["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip().lower()
    if text.startswith("/start"):
        welcome = (
            "🎬 Welcome to Movie Tracker Bot!\n"
            "👇 Please choose your region below\n"
        )
        send_message(chat_id, welcome, REGION_INLINE_KEYBOARD)
        return

    elif text.startswith("/help"):
        help_text = (
            "📖 Available Commands\n"
            "/start - Set your region for the upcoming movies\n"
            "/upcoming - View upcoming movie releases\n"
            "/upcoming_genre - View upcoming movies releases by genre\n"
            "/about - Learn more about the author\n"
        )
        send_message(chat_id, help_text)
        return

    elif text.startswith("/about"):
        about_text = (
            "👨‍💻 Developer: https://www.kylekao.dev/\n"
            "💬 Feel free to chat or share feedback!\n"
            "📬 Telegram: @kylekao0322"
        )
        send_message(chat_id, about_text)
        return

    elif text.startswith("/upcoming_genre"):
        send_message(chat_id, "👇 Select your preferred movie genre", inline_keyboard=GENRE_INLINE_KEYBOARD)
        return

    elif text.startswith("/upcoming"):
        send_message(chat_id, "🔍 Searching current upcoming movies")
        region = db.get_user_region(chat_id) or "US"
        try:
            data = get_upcoming(region)
            movies = data["movies"]
            if not movies:
                send_message(chat_id, "Sorry. There is no upcoming movies")
                return
            user_movie_cache[chat_id] = {
                "movies": movies,   
                "index": 0,         
                "page": 1,        
                "region": region
            }
            _send_local_movie_page(chat_id, movies, start=0)
        except Exception as e:
            send_message(chat_id, f"Failure: {e}")
        return

    else:
        send_message(chat_id, "Sorry, I don’t recognize that command. Try /help to see what I can do!")

def set_bot_commands():
    commands = [
        {"command": "start", "description": "set your region"},
        {"command": "help", "description": "display all the commands"},
        {"command": "upcoming", "description": "search upcoming movie"},
        {"command": "upcoming_genre", "description": "search upcoming movie by genre"},
        {"command": "about", "description": "the detailed information of the developer"},
    ]
    r = requests.post(f"{BASE_URL}/setMyCommands", json={"commands": commands})

def _send_local_movie_page(chat_id: int, movies: dict, start: int):
    page_size = 5
    sliced = movies[start:start + page_size]

    reply = f"🎬 Upcoming Movies\n\n"
    inline_keyboard = {"inline_keyboard": []}

    number = 1
    for m in sliced:
        g = ", ".join(m["genres"]) if m.get("genres") else "N/A"
        reply += (
            f"{number}.\n"
            f"🎞️ {m['title']}\n"
            f"📅 {m['release_date']}\n"
            f"🎭 {g}\n\n"
        )
        inline_keyboard["inline_keyboard"].append([
            {"text": f"⭐ Add {number}", "callback_data": f"add_{m["id"]}"},
            {"text": "🔍 More detail", "callback_data": f"detail_{m['id']}"}
        ])
        number += 1
    inline_keyboard["inline_keyboard"].append([
        {"text": "➡ Next", "callback_data": f"next_{start + page_size}"}
    ])

    send_message(chat_id, reply, inline_keyboard)