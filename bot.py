from telegram.ext import ApplicationBuilder
from config import BOT_TOKEN
from logic.handlers import register_handlers
from logic.db_setup import init_db

# 2. Inizializza il DB prima di avviare l'app
print("⚙️ Verifica database in corso...")
init_db()
# Crea l'applicazione del bot
app = ApplicationBuilder().token(BOT_TOKEN).build()

# Registra tutti gli handler (video + callback inline)
register_handlers(app)

print("🤖 Bot avviato! In ascolto dei messaggi...")

# Avvia polling
app.run_polling()
