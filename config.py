import os
from dotenv import load_dotenv

load_dotenv()  # legge il .env
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("Errore: la variabile d'ambiente BOT_TOKEN non è impostata!")