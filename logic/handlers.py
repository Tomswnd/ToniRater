from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters

from logic.rating_manager import add_rating, get_stats, should_delete


# ---------------------------------------------------------
# 1) HANDLER: quando arriva un video nel gruppo
# ---------------------------------------------------------
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    # Prendiamo l'ID del messaggio del video
    video_message_id = message.message_id

    # Testo iniziale del sondaggio
    text = (
        "Vota questo video:\n"
        "Media attuale: — (0 voti)"
    )

    # Bottoni inline con callback_data codificata
    keyboard = [
        [
            InlineKeyboardButton("⭐ 1", callback_data=f"rate:{video_message_id}:1"),
            InlineKeyboardButton("⭐ 2", callback_data=f"rate:{video_message_id}:2"),
            InlineKeyboardButton("⭐ 3", callback_data=f"rate:{video_message_id}:3"),
            InlineKeyboardButton("⭐ 4", callback_data=f"rate:{video_message_id}:4"),
            InlineKeyboardButton("⭐ 5", callback_data=f"rate:{video_message_id}:5"),
        ]
    ]

    # Invia il messaggio di votazione sotto al video
    await message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ---------------------------------------------------------
# 2) HANDLER: quando un utente preme un bottone di voto
# ---------------------------------------------------------
async def rate_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer(text="Voto registrato!")

    # callback_data del tipo: "rate:<message_id>:<voto>"
    _, message_id, vote = query.data.split(":")
    message_id = int(message_id)
    vote = int(vote)

    user_id = query.from_user.id

    # Salva il voto
    await add_rating(message_id, user_id, vote)

    # Calcola media aggiornata
    count, avg = await get_stats(message_id)

    # Controlla se eliminare il video
    if await should_delete(message_id):
        try:
            # Elimina il video (in base al message_id)
            await query.message.chat.delete_message(message_id)

            # Aggiorna il messaggio del sondaggio
            await query.edit_message_text(
                "Video eliminato (media ≤ 2 dopo almeno 3 voti)."
            )
        except Exception:
            # Se Telegram non permette di eliminarlo (es. bot non admin), evita crash
            await query.edit_message_text(
                "Il video dovrebbe essere eliminato, ma il bot non ha i permessi."
            )
        return

    # Altrimenti aggiorna il messaggio con la media aggiornata
    keyboard = [
        [
            InlineKeyboardButton("⭐ 1", callback_data=f"rate:{message_id}:1"),
            InlineKeyboardButton("⭐ 2", callback_data=f"rate:{message_id}:2"),
            InlineKeyboardButton("⭐ 3", callback_data=f"rate:{message_id}:3"),
            InlineKeyboardButton("⭐ 4", callback_data=f"rate:{message_id}:4"),
            InlineKeyboardButton("⭐ 5", callback_data=f"rate:{message_id}:5"),
        ]
    ]

    new_text = (
        "Vota questo video:\n"
        f"Media attuale: {avg:.1f} ⭐ ({count} voti)"
    )

    try:
        await query.edit_message_text(
            new_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception:
        # A volte Telegram non vuole aggiornare messaggi modificati rapidamente
        pass


# ---------------------------------------------------------
# 3) FUNZIONE per collegare gli handler al bot (in main.py)
# ---------------------------------------------------------
def register_handlers(app):
    """
    Registra tutti gli handler necessari nel tuo Application in main.py
    """

    # Quando arriva un video → avvia sondaggio
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))

    # Quando premono un bottone → registra voto
    app.add_handler(CallbackQueryHandler(rate_callback, pattern="^rate:"))
