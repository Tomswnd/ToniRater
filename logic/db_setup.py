import sqlite3
import os

# Definiamo il percorso del database
# ".." ci permette di salire di una cartella (da /logic a /ToniRater) e andare in /data
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'tonirater.db')


def init_db():
    """Crea il database e le tabelle necessarie se non esistono."""

    # Assicuriamoci che la cartella /data esista
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    print(f"🔄 Connessione al database in: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # --- 1. Tabella UTENTI (Anagrafica) ---
    # Serve per memorizzare chi sono gli utenti (utile per le classifiche)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,  -- ID univoco di Telegram
            first_name TEXT,              -- Nome dell'utente
            username TEXT                 -- Username (@...)
        )
    ''')

    # --- 2. Tabella VIDEO (I messaggi inviati) ---
    # Serve per sapere CHI ha mandato il video e QUANDO
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            chat_id INTEGER,              -- ID del gruppo
            message_id INTEGER,           -- ID del messaggio video
            sender_id INTEGER,            -- ID di chi ha mandato il video
            sent_at TEXT,                 -- Data di invio
            PRIMARY KEY (chat_id, message_id)
        )
    ''')

    # --- 3. Tabella VOTI (Le valutazioni) ---
    # Serve per memorizzare i voti. PK composta per evitare voti doppi.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            chat_id INTEGER,              -- ID del gruppo
            message_id INTEGER,           -- ID del video votato
            voter_id INTEGER,             -- ID di chi sta votando
            rating INTEGER NOT NULL,      -- Voto (1-5)
            voted_at TEXT,                -- Data del voto
            PRIMARY KEY (chat_id, message_id, voter_id)
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Database inizializzato con successo!")


if __name__ == "__main__":
    # Questo blocco viene eseguito solo se lanci il file direttamente
    init_db()