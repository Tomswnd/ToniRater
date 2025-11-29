import re
import logging
import asyncio
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters, CallbackContext, CommandHandler
from logic.rating_manager import get_leaderboard, get_worst_user

from config import BOT_TOKEN
from logic.rating_manager import add_rating, get_stats, should_delete, register_video, upsert_user
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
    user = message.from_user

    # 1. Salva/Aggiorna Utente (Mittente)
    await upsert_user(user.id, user.first_name, user.username)
    # 2. Registra il Video nel DB
    await register_video(chat_id, link_message_id, user.id)

    # link_message_id = message.message_id
    # chat_id = message.chat_id
    #
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
# async def handle_id(update: Update, context: CallbackContext):
#     message = update.message
#     video_message_id = message.message_id
#     chat_id = message.chat_id
#     await handle_video(video_message_id, chat_id)
async def handle_id(update: Update, context: CallbackContext):
    message = update.message
    video_message_id = message.message_id
    chat_id = message.chat_id
    user = message.from_user

    # 1. Salva/Aggiorna Utente (Mittente)
    await upsert_user(user.id, user.first_name, user.username)
    # 2. Registra il Video
    await register_video(chat_id, video_message_id, user.id)

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

    # NON rispondiamo subito con query.answer(). Aspettiamo l'esito del voto.

    try:
        # Parsing dei dati
        data_parts = query.data.split(":")
        _, message_id, vote = data_parts
        message_id = int(message_id)
        vote = int(vote)
    except ValueError:
        await query.answer("❌ Errore nei dati del bottone.")
        return

    user = query.from_user
    user_id = user.id
    chat_id = query.message.chat_id

    # 1. Salva/Aggiorna Utente nel DB
    await upsert_user(user_id, user.first_name, user.username)

    # 2. Tenta di aggiungere il voto
    success = await add_rating(chat_id, message_id, user_id, vote)

    # --- PUNTO CRUCIALE: Gestione della risposta ---
    if not success:
        # Se add_rating ritorna False, è autovoto
        # show_alert=True fa apparire una finestra popup che l'utente deve chiudere
        await query.answer("🚫 Non puoi votare i tuoi video!", show_alert=True)
        return
    else:
        # Se è True, il voto è valido
        await query.answer("✅ Voto registrato!")
    # -----------------------------------------------

    # 3. Calcola statistiche aggiornate
    count, avg = await get_stats(chat_id, message_id)

    # 4. Controlla se eliminare il messaggio
    if await should_delete(chat_id, message_id):
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            # Modifichiamo il testo del bottone (se possibile) o mandiamo un messaggio
            # Nota: se il messaggio è cancellato, non possiamo editarlo.
            # Possiamo mandare un messaggio nel gruppo o rispondere al callback.
            final_text = (
                f"🗑️ <b>CONTENUTO ELIMINATO</b>\n\n"
                f"Questo video è stato rimosso dalla community.\n"
                f"📉 <b>Punteggio finale:</b> {avg:.1f} ⭐ su {count} voti."
            )

            # reply_markup=None serve a RIMUOVERE i bottoni (le stelline)
            await query.edit_message_text(
                text=final_text,
                parse_mode="HTML",
                reply_markup=None
            )
            return
            return
        except Exception as e:
            logger.error(f"Errore cancellazione video: {e}")
            await query.answer("⚠️ Video da eliminare, ma mancano i permessi!", show_alert=True)

        # final_text = (
        #     f"🗑️ <b>CONTENUTO ELIMINATO</b>\n\n"
        #     f"Questo video è stato rimosso dalla community.\n"
        #     f"📉 <b>Punteggio finale:</b> {avg:.1f} ⭐ su {count} voti."
        # )
        #
        # # reply_markup=None serve a RIMUOVERE i bottoni (le stelline)
        # await query.edit_message_text(
        #     text=final_text,
        #     parse_mode="HTML",
        #     reply_markup=None
        # )
        # return

    # 5. Aggiorna il messaggio con la nuova media
    keyboard = [[
        InlineKeyboardButton("⭐ 1", callback_data=f"rate:{message_id}:1"),
        InlineKeyboardButton("⭐ 2", callback_data=f"rate:{message_id}:2"),
        InlineKeyboardButton("⭐ 3", callback_data=f"rate:{message_id}:3"),
        InlineKeyboardButton("⭐ 4", callback_data=f"rate:{message_id}:4"),
        InlineKeyboardButton("⭐ 5", callback_data=f"rate:{message_id}:5"),
    ]]
    new_text = f"Vota questo video:\nMedia attuale: {avg:.1f} ⭐ ({count} voti)"

    if query.message.text.strip() != new_text.strip():
        try:
            await query.edit_message_text(new_text, reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception:
            pass  # Ignoriamo errori se il messaggio non è modificabile


async def cmd_classifica(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    min_videos = 3  # Soglia minima per apparire

    # 1. Recuperiamo i TOP
    top_users = await get_leaderboard(chat_id, min_videos=min_videos)

    # 2. Recuperiamo il FLOP (Il peggiore)
    worst_user = await get_worst_user(chat_id, min_videos=min_videos)

    if not top_users:
        await update.message.reply_text(
            "📉 <b>Classifica vuota!</b>\n"
            f"Servono almeno {min_videos} video votati per generare le statistiche.",
            parse_mode="HTML"
        )
        return

    # --- Costruzione Messaggio TOP ---
    text = "🏆 <b>TOP POSTER (Qualità)</b>\n<i>Chi invia i video migliori?</i>\n\n"
    medals = ["🥇", "🥈", "🥉"]

    for i, (name, count, avg) in enumerate(top_users):
        icon = medals[i] if i < 3 else "▪️"
        text += f"{icon} <b>{name}</b>: {avg:.2f} ⭐ ({count} video)\n"

    # --- Costruzione Sezione SHAME 💩 ---
    if worst_user:
        w_name, w_count, w_avg = worst_user

        # Controlliamo che il peggiore non sia anche il primo in classifica
        # (succede se c'è solo un utente in totale)
        if len(top_users) > 1 or top_users[0][0] != w_name:
            text += "\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            text += "🍅 <b>LAST PLACE OF SHAME</b> 🍅\n"
            text += f"<i>Qualcuno banni questo utente...</i>\n\n"
            text += f"💩 <b>{w_name}</b>: {w_avg:.2f} ⭐ ({w_count} video)"

    text += f"\n\n<i>(Minimo {min_videos} video per apparire)</i>"

    await update.message.reply_text(text, parse_mode="HTML")
# ---------------------------------------------------------
# Registrazione handler
# ---------------------------------------------------------
def register_handlers(app):
    link_filter = filters.TEXT & filters.Regex(r'https?://')
    video_filter = filters.VIDEO

    app.add_handler(MessageHandler(link_filter, handle_link))
    app.add_handler(MessageHandler(video_filter, handle_id))
    app.add_handler(CallbackQueryHandler(rate_callback, pattern="^rate:"))
    app.add_handler(CommandHandler("classifica", cmd_classifica))
