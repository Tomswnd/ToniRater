import sqlite3
import os
import datetime

# Percorso assoluto per evitare errori se lanci il bot da cartelle diverse
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'tonirater.db')

def _get_conn():
    """Funzione helper per ottenere una connessione al database."""
    # check_same_thread=False permette di usare la connessione in un contesto async
    return sqlite3.connect(DB_PATH, check_same_thread=False)

async def upsert_user(user_id: int, first_name: str, username: str):
    """
    Inserisce l'utente nel DB se non esiste, oppure aggiorna i dati se è cambiato.
    """
    if not user_id:
        return

    with _get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (user_id, first_name, username)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                first_name = excluded.first_name,
                username = excluded.username
        """, (user_id, first_name, username))
        conn.commit()


import datetime  # <--- AGGIUNGI QUESTO IN CIMA AL FILE (se non c'è già)


async def register_video(chat_id: int, message_id: int, sender_id: int):
    """
    Salva i metadati del video appena viene inviato.
    Serve per sapere chi è l'autore (e impedire l'autovoto).
    """
    with _get_conn() as conn:
        cursor = conn.cursor()
        timestamp = datetime.datetime.now().isoformat()

        # Usiamo INSERT OR IGNORE: se per assurdo il video fosse già lì,
        # non fa nulla e non rompe il programma.
        cursor.execute("""
            INSERT OR IGNORE INTO videos (chat_id, message_id, sender_id, sent_at)
            VALUES (?, ?, ?, ?)
        """, (chat_id, message_id, sender_id, timestamp))

        conn.commit()


async def add_rating(chat_id: int, message_id: int, user_id: int, vote: int):
    """
    Aggiunge il voto nel DB.
    Ritorna True se il voto è stato registrato, False se bloccato (es. autovoto).
    """
    if vote < 1 or vote > 5:
        return False

    with _get_conn() as conn:
        cursor = conn.cursor()

        # 1. CONTROLLO AUTOVOTO
        # Cerchiamo chi è il mandante di questo messaggio in questa chat
        cursor.execute(
            "SELECT sender_id FROM videos WHERE chat_id = ? AND message_id = ?",
            (chat_id, message_id)
        )
        row = cursor.fetchone()

# TODO: TOGLIERE IL COMMENTO PRIMA DI COMMITTARE
        if row:
            sender_id = row[0]
            if sender_id == user_id:
                # L'utente sta provando a votarsi da solo!
                return False

        # 2. REGISTRAZIONE VOTO
        timestamp = datetime.datetime.now().isoformat()
        cursor.execute("""
            INSERT OR REPLACE INTO votes (chat_id, message_id, voter_id, rating, voted_at)
            VALUES (?, ?, ?, ?, ?)
        """, (chat_id, message_id, user_id, vote, timestamp))

        conn.commit()
        return True


async def get_stats(chat_id: int, message_id: int):
    """
    Restituisce una tupla: (numero_voti, media).
    """
    with _get_conn() as conn:
        cursor = conn.cursor()

        # SQL calcola direttamente numero voti e media
        cursor.execute("""
            SELECT COUNT(*), AVG(rating)
            FROM votes
            WHERE chat_id = ? AND message_id = ?
        """, (chat_id, message_id))

        row = cursor.fetchone()

        # Se non ci sono risultati (improbabile con COUNT, ma per sicurezza)
        if not row:
            return 0, 0.0

        count = row[0]
        avg = row[1]

        # Se nessuno ha votato, avg sarà None. Lo trasformiamo in 0.0
        if count == 0 or avg is None:
            return 0, 0.0

        return count, round(avg, 2)


async def should_delete(chat_id: int, message_id: int):
    """
    Ritorna True se il video va eliminato:
    - almeno 3 voti
    - media <= 2
    """
    count, avg = await get_stats(chat_id, message_id)
    return count >= 3 and avg <= 2.0


async def get_leaderboard(chat_id: int, min_videos=3, limit=3):
    """
    Restituisce la top 10 degli utenti con la media voti più alta.
    Regola: Devono aver mandato almeno 'min_videos'.
    Return: lista di tuple (nome, numero_video, media_voti)
    """
    with _get_conn() as conn:
        cursor = conn.cursor()

        # Questa query fa tutto il lavoro sporco:
        # 1. Unisce VIDEO e VOTI per calcolare la media
        # 2. Unisce con USERS per prendere il nome
        # 3. Filtra per chat_id
        # 4. Raggruppa per mittente (sender_id)
        # 5. Tiene solo chi ha mandato almeno min_videos
        # 6. Ordina per media decrescente

        query = """
        SELECT 
            u.first_name, 
            COUNT(DISTINCT v.message_id) as video_count, 
            AVG(vo.rating) as average_score
        FROM videos v
        JOIN votes vo ON v.chat_id = vo.chat_id AND v.message_id = vo.message_id
        JOIN users u ON v.sender_id = u.user_id
        WHERE v.chat_id = ?
        GROUP BY v.sender_id
        HAVING video_count >= ?
        ORDER BY average_score DESC
        LIMIT ?
        """

        cursor.execute(query, (chat_id, min_videos, limit))
        return cursor.fetchall()


async def get_worst_user(chat_id: int, min_videos=3):
    """
    Trova l'utente con la media voti PEGGIORE.
    Regola: Deve aver mandato almeno 'min_videos'.
    """
    with _get_conn() as conn:
        cursor = conn.cursor()

        query = """
        SELECT 
            u.first_name, 
            COUNT(DISTINCT v.message_id) as video_count, 
            AVG(vo.rating) as average_score
        FROM videos v
        JOIN votes vo ON v.chat_id = vo.chat_id AND v.message_id = vo.message_id
        JOIN users u ON v.sender_id = u.user_id
        WHERE v.chat_id = ?
        GROUP BY v.sender_id
        HAVING video_count >= ?
        ORDER BY average_score ASC
        LIMIT 1
        """

        cursor.execute(query, (chat_id, min_videos))
        return cursor.fetchone()