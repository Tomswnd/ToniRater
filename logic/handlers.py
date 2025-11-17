import re
import logging
import asyncio
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters, CallbackContext

from config import BOT_TOKEN
from logic.rating_manager import add_rating, get_stats, should_delete
from yt_dlp import YoutubeDL

# Logger
logger = logging.getLogger(__name__)

# Istanza bot per inviare messaggi
my_bot_instance = Bot(token=BOT_TOKEN)

# ---------------------------------------------------------
# Controlla se il link è un video valido
# ---------------------------------------------------------
def is_video_link(url: str) -> bool:
    # Se il link è TikTok → consideralo subito valido
    if "tiktok.com" in url.lower():
        return True

    ydl_opts = {
        'quiet': True,
        'skip_download': True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'entries' in info:
                return len(info['entries']) > 0
            return True
    except Exception:
        return False

# ---------------------------------------------------------
# Handler per messaggi contenenti link
# ---------------------------------------------------------
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    text = message.text

    # Controlla che ci sia un link
    match = re.search(r'https?://\S+', text)
    if not match:
        return
    url = match.group(0)

    # Verifica che sia un video
    if not is_video_link(url):
        return

    link_message_id = message.message_id
    chat_id = message.chat_id

    survey_text = "Vota questo video/link:\nMedia attuale: — (0 voti)"
    keyboard = [[
        InlineKeyboardButton("⭐ 1", callback_data=f"rate:{link_message_id}:1"),
        InlineKeyboardButton("⭐ 2", callback_data=f"rate:{link_message_id}:2"),
        InlineKeyboardButton("⭐ 3", callback_data=f"rate:{link_message_id}:3"),
        InlineKeyboardButton("⭐ 4", callback_data=f"rate:{link_message_id}:4"),
        InlineKeyboardButton("⭐ 5", callback_data=f"rate:{link_message_id}:5"),
    ]]

    # Aspetta 3 secondi prima di inviare il sondaggio
    time.sleep(3)

    await message.reply_text(
        survey_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------------------------------------------------
# Handler per messaggi video inviati da utenti
# ---------------------------------------------------------
async def handle_id(update: Update, context: CallbackContext):
    message = update.message
    video_message_id = message.message_id
    chat_id = message.chat_id
    await handle_video(video_message_id, chat_id)

async def handle_video(video_message_id, chat_id):
    text = "Vota questo video:\nMedia attuale: — (0 voti)"
    keyboard = [[
        InlineKeyboardButton("⭐ 1", callback_data=f"rate:{video_message_id}:1"),
        InlineKeyboardButton("⭐ 2", callback_data=f"rate:{video_message_id}:2"),
        InlineKeyboardButton("⭐ 3", callback_data=f"rate:{video_message_id}:3"),
        InlineKeyboardButton("⭐ 4", callback_data=f"rate:{video_message_id}:4"),
        InlineKeyboardButton("⭐ 5", callback_data=f"rate:{video_message_id}:5"),
    ]]

    # Aspetta 1 secondo prima di inviare il sondaggio
    time.sleep(1)

    await my_bot_instance.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        reply_to_message_id=video_message_id,
        allow_sending_without_reply=True
    )

# ---------------------------------------------------------
# Handler per callback dei voti
# ---------------------------------------------------------
async def rate_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Voto registrato!")

    try:
        _, message_id, vote = query.data.split(":")
        message_id = int(message_id)
        vote = int(vote)
    except ValueError:
        return

    user_id = query.from_user.id
    await add_rating(message_id, user_id, vote)
    count, avg = await get_stats(message_id)

    # Controlla se eliminare il messaggio
    if await should_delete(message_id):
        try:
            await context.bot.delete_message(chat_id=query.message.chat_id, message_id=message_id)
            await query.edit_message_text(
                f"🗑️ Video eliminato!\nMedia finale: {avg:.1f} ⭐ su {count} voti (Troppo bassa)."
            )
        except Exception as e:
            logger.error(f"Errore cancellazione video: {e}")
            await query.edit_message_text(
                f"⚠️ Il video ha media {avg:.1f}, dovrebbe essere eliminato ma non ho i permessi."
            )
        return

    # Aggiorna il messaggio con la media aggiornata
    keyboard = [[
        InlineKeyboardButton("⭐ 1", callback_data=f"rate:{message_id}:1"),
        InlineKeyboardButton("⭐ 2", callback_data=f"rate:{message_id}:2"),
        InlineKeyboardButton("⭐ 3", callback_data=f"rate:{message_id}:3"),
        InlineKeyboardButton("⭐ 4", callback_data=f"rate:{message_id}:4"),
        InlineKeyboardButton("⭐ 5", callback_data=f"rate:{message_id}:5"),
    ]]
    new_text = f"Vota questo video:\nMedia attuale: {avg:.1f} ⭐ ({count} voti)"

    if query.message.text != new_text:
        try:
            await query.edit_message_text(new_text, reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception:
            pass

# ---------------------------------------------------------
# Registrazione handler
# ---------------------------------------------------------
def register_handlers(app):
    link_filter = filters.TEXT & filters.Regex(r'https?://')
    video_filter = filters.VIDEO

    app.add_handler(MessageHandler(link_filter, handle_link))
    app.add_handler(MessageHandler(video_filter, handle_id))
    app.add_handler(CallbackQueryHandler(rate_callback, pattern="^rate:"))
