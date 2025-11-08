import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from db.database import Database
from utils.telegram_util import send_message

db = Database()

def send_daily_reminders():
    today = datetime.now().date()
    users = db.get_all_user_movies() 

    for chat_id in users:
        tracked = db.get_user_tracked_movies(chat_id)
        if not tracked:
            continue

        reply = f'''🎬 Daily Reminder ({today.strftime('%Y-%m-%d')})\n\n'''
        inline_keyboard = {"inline_keyboard": []}
        number = 1

        for m in tracked:
            release_date_str = m["release_date"]
            if not release_date_str:
                continue

            try:
                release_date = datetime.strptime(release_date_str, "%Y-%m-%d").date()
                days_left = (release_date - today).days
            except Exception:
                days_left = None

            if days_left is None:
                countdown_text = "❔ Unknown date"
            elif days_left > 0:
                countdown_text = f"{days_left} day{'s' if days_left > 1 else ''} left"
            elif days_left == 0:
                countdown_text = "🎬 Releases today!"
            else:
                countdown_text = "✅ Already released"

            reply += (
                f"{number}.\n"
                f"🎞️ {m['title']}\n"
                f"📅 {m['release_date']} — {countdown_text}\n\n"
            )

            inline_keyboard["inline_keyboard"].append([
                {"text": f"❌ Remove {number}", "callback_data": f"remove_{m['movie_id']}"},
                {"text": "🔍 More Detail", "callback_data": f"detail_{m['movie_id']}"}
            ])
            number += 1

        send_message(chat_id, reply, inline_keyboard)

def start_scheduler():
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(send_daily_reminders, "interval", hours=24)
    send_daily_reminders() 
    scheduler.start()