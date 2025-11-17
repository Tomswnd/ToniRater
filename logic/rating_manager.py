import json
import os
import asyncio

RATINGS_FILE = "data/ratings.json"

# Lock per impedire scritture simultanee
file_lock = asyncio.Lock()


# -----------------------------
# Utilità base: lettura/scrittura JSON
# -----------------------------
async def load_ratings():
    """Carica il JSON dei voti. Se non esiste, lo crea vuoto."""
    if not os.path.exists(RATINGS_FILE):
        return {}

    async with file_lock:
        try:
            with open(RATINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            # Se il file si corrompe lo resettiamo
            return {}


async def save_ratings(data: dict):
    """Salva l'intero dizionario ratings in modo atomico."""
    async with file_lock:
        temp_file = RATINGS_FILE + ".tmp"

        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

        # Sovrascrivi atomicamente
        os.replace(temp_file, RATINGS_FILE)


# -----------------------------
# API principali
# -----------------------------
async def add_rating(message_id: int, user_id: int, vote: int):
    """
    Aggiunge o aggiorna un voto.
    Ogni utente può votare 1 volta per messaggio.
    """
    if vote < 1 or vote > 5:
        return  # voto non valido

    data = await load_ratings()
    msg_id_str = str(message_id)
    user_id_str = str(user_id)

    if msg_id_str not in data:
        data[msg_id_str] = {}

    data[msg_id_str][user_id_str] = vote

    await save_ratings(data)


async def get_stats(message_id: int):
    """
    Restituisce (numero_voti, media)
    """
    data = await load_ratings()
    msg_id_str = str(message_id)

    if msg_id_str not in data or len(data[msg_id_str]) == 0:
        return 0, 0.0

    votes = list(data[msg_id_str].values())
    count = len(votes)
    avg = sum(votes) / count

    return count, avg


async def should_delete(message_id: int):
    """
    Ritorna True se il video va eliminato:
    - almeno 3 voti
    - media <= 2
    """
    count, avg = await get_stats(message_id)
    return count >= 3 and avg <= 2
