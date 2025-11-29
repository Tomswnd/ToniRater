# ToniRater 🤖⭐

[Python >= 3.10] - Bot Telegram per votare video e link nei gruppi.
Gli utenti votano da 1 a 5 ⭐ tramite bottoni inline. I dati sono salvati su **SQLite** per garantire performance e integrità.
Include un sistema di **classifiche** (Top & Flop users) e cancellazione automatica dei contenuti di bassa qualità.

## ✨ Funzionalità

* **Votazione Inline:** Sondaggi da 1 a 5 stelle sotto ogni video/link.
* **Database SQLite:** Salvataggio persistente di utenti, video e voti.
* **Moderazione Automatica:** Se un video riceve **≥ 3 voti** e ha una media **≤ 2.0**, viene eliminato e sostituito da un avviso.
* **Anti-Autovoto:** Impedisce agli utenti di votare i propri contenuti.
* **Classifiche (`/classifica`):** Mostra la Top 3 degli utenti per qualità e il peggiore ("Last Place of Shame").
* **Supporto Link:** Riconosce video inviati direttamente e link (YouTube, TikTok, Instagram, ecc.) grazie a `yt-dlp`.

---

## 📂 Struttura del progetto

```text
ToniRater/
├── bot.py                # File principale per avviare il bot
├── config.py             # Gestione configurazione e variabili d'ambiente
├── requirements.txt      # Dipendenze Python
├── logic/
│   ├── __init__.py
│   ├── db_setup.py       # Script inizializzazione Database SQLite
│   ├── rating_manager.py # Logica CRUD (Voti, Utenti, Video, Classifiche)
│   └── handlers.py       # Handler messaggi, comandi e callback
├── data/
│   └── tonirater.db      # Database SQLite (generato automaticamente)
└── test/                 # Unit test
```

---

## ⚡ Installazione

1.  **Clona il progetto:**
    ```bash
    git clone <url_del_progetto>
    cd ToniRater
    ```

2.  **Crea un virtual environment (consigliato):**
    ```bash
    # Windows
    python -m venv venv
    venv\Scripts\activate

    # Linux/Mac
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Installa le dipendenze:**
    ```bash
    pip install -r requirements.txt
    ```

---

## 🔒 Configurazione

### 1. Variabili d'Ambiente (`.env`)
Il bot richiede un token Telegram. Crea un file `.env` nella root del progetto:

```ini
BOT_TOKEN=il_tuo_token_telegram_qui
```

### 2. File `.gitignore`
Assicurati di **non** caricare il database o il file .env su Git. Il tuo `.gitignore` dovrebbe contenere:

```text
.env
venv/
__pycache__/
data/*.db
data/*.db-journal
```

---

## 🚀 Avvio del bot

Lancia il bot. Al primo avvio, il database `data/tonirater.db` verrà creato automaticamente.

```bash
python bot.py
```

---

## 🎮 Comandi e Utilizzo

### Votazione
* Basta inviare un **video** o un **link** (YouTube/TikTok/ecc) nel gruppo.
* Il bot risponderà con una tastiera per votare.
* La media e il conteggio voti si aggiornano in tempo reale.

### Comandi Disponibili
* `/classifica` (o `/top`): Mostra gli utenti con la media voti più alta (minimo 3 video inviati) e l'utente con la media peggiore 🍅.

### Regole di Cancellazione
Un contenuto viene rimosso automaticamente se:
1.  Ha ricevuto almeno **3 voti**.
2.  La media voti è **≤ 2.0**.

---

## 🖥️ Deploy su Server Linux (Systemd)

Per eseguire il bot in background e riavviarlo automaticamente.

1.  **Modifica i permessi (Importante per SQLite):**
    L'utente che esegue il bot deve poter scrivere nella cartella `data`.
    ```bash
    mkdir -p data
    # Se il bot gira come tuo_utente, assicurati di essere il proprietario
    chown -R tuo_utente:tuo_utente data/
    ```

2.  **Crea il servizio:**
    ```bash
    sudo nano /etc/systemd/system/tonirater.service
    ```

3.  **Incolla la configurazione:**
    Modifica `tuo_utente` e i percorsi.

    ```ini
    [Unit]
    Description=ToniRater Bot
    After=network.target

    [Service]
    User=tuo_utente
    Group=tuo_utente
    WorkingDirectory=/home/tuo_utente/ToniRater
    EnvironmentFile=/home/tuo_utente/ToniRater/.env
    ExecStart=/home/tuo_utente/ToniRater/venv/bin/python3 bot.py
    Restart=always

    [Install]
    WantedBy=multi-user.target
    ```

4.  **Avvia:**
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable tonirater
    sudo systemctl start tonirater
    ```

---

## 💻 Requisiti Tecnici

* Python ≥ 3.10
* Librerie principali:
    * `python-telegram-bot`
    * `yt-dlp` (per verifica link video)
    * `python-dotenv`
* SQLite (incluso in Python)

## 📝 Note
* Il bot deve essere **Amministratore** del gruppo con permesso di **Eliminare messaggi** per far funzionare la moderazione automatica.