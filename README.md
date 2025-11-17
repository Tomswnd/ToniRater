# ToniRater 🤖⭐

[Python >= 3.10] - Bot Telegram per votare video in gruppo.
Gli utenti votano da 1 a 5 ⭐ tramite bottoni inline. 
Se un video riceve almeno 3 voti e la media ≤ 2, il bot lo elimina automaticamente.

---

## 📂 Struttura del progetto

ToniRater/

├── bot.py                  # File principale per avviare il bot

├── config.py               # Legge il token da variabile d'ambiente

├── requirements.txt        # Dipendenze Python

├── logic/

│   ├── __init__.py

│   ├── rating_manager.py   # Gestione voti, media e cancellazione

│   └── handlers.py         # Handler video e callback bottoni

├── data/

│   └── ratings.json        # Dati votazioni (JSON)

└── test/

    ├── __init__.py

    ├── test_rating_manager.py

    └── test_handlers_logic.py

---

## ⚡ Installazione

1. Clona il progetto:

    git clone <url_del_progetto>
    cd ToniRater

2. Crea un virtual environment (opzionale):

    python -m venv venv
    venv\Scripts\activate     # Windows
    source venv/bin/activate  # Linux/Mac

3. Installa le dipendenze:

    py -m pip install -r requirements.txt

---

## 🔒 Configurazione del BOT TOKEN

### 1️⃣ Usare variabili d'ambiente

- **Windows temporaneo (PowerShell)**:

    set BOT_TOKEN="il_tuo_token"
    py bot.py

- **Windows permanente**:
  - Vai su “Variabili d’ambiente” → Nuova variabile utente
  - Nome: `BOT_TOKEN`, Valore: `il_tuo_token`
  - Riavvia PowerShell → py bot.py

- **Linux/Mac temporaneo**:

    export BOT_TOKEN="il_tuo_token"
    python3 bot.py

- **Linux/Mac permanente**:
  - Aggiungi a `~/.bashrc` o `~/.zshrc`:
    
    export BOT_TOKEN="il_tuo_token"
    
  - Poi aggiorna la shell:

    source ~/.bashrc   # oppure source ~/.zshrc

---

### 2️⃣ Usare file `.env` (consigliato)

1. Installa la libreria `python-dotenv`:

    py -m pip install python-dotenv

2. Crea `.env` nella root del progetto:

    BOT_TOKEN=il_tuo_token

3. Aggiorna `config.py`:

    ```python
    from dotenv import load_dotenv
    import os

    load_dotenv()
    BOT_TOKEN = os.getenv("BOT_TOKEN")

    if not BOT_TOKEN:
        raise ValueError("Errore: la variabile d'ambiente BOT_TOKEN non è impostata!")
    ```

4. Aggiungi `.env` a `.gitignore` per non committarlo:

    ```
    .env
    data/ratings.json
    venv/
    __pycache__/
    *.log
    ```

---

## 🚀 Avvio del bot

Nel terminale:

    py bot.py
    # oppure su Linux: python3 bot.py

---

## 🎯 Funzionamento

1. Quando un **video** viene inviato nel gruppo:
   - Il bot crea un messaggio di sondaggio con bottoni ⭐ 1–5
2. Quando un utente vota:
   - il voto viene registrato
   - la **media** e il **numero di voti** vengono aggiornati
3. Se un video riceve almeno 3 voti e media ≤ 2:
   - il video viene eliminato
   - il messaggio viene aggiornato con:
     "Video eliminato (media ≤ 2 dopo almeno 3 voti)"

---

## 🧪 Test del progetto

I test verificano la logica senza Telegram:

    py -m pytest -v

> Richiede `pytest-asyncio` perché le funzioni sono asincrone

---

## ⚙️ Migliorie opzionali

- Bloccare l’autovoto (utente non può votare il proprio video)
- Comando `/stats` per visualizzare le medie
- Pulizia automatica voti vecchi in `ratings.json`
- Log dettagliato dei voti

---

## 💻 Requisiti

- Python ≥ 3.10
- Librerie:
  - python-telegram-bot
  - pytest
  - pytest-asyncio
  - python-dotenv

---

## 📝 Note

- Il bot deve avere **permessi di amministratore** nel gruppo per eliminare i video
- `ratings.json` contiene i voti in questo formato:

    {
      "12345": { "111": 2, "222": 4, "333": 1 }
    }

---

## 🖥️ Avvio automatico su server Linux con `.env`

1. Crea il servizio systemd:

    sudo nano /etc/systemd/system/tonirater.service

Contenuto esempio:

    [Unit]
    Description=ToniRater Bot
    After=network.target

    [Service]
    User=tuo_utente
    WorkingDirectory=/home/tuo_utente/ToniRater
    EnvironmentFile=/home/tuo_utente/ToniRater/.env
    ExecStart=/usr/bin/python3 /home/tuo_utente/ToniRater/bot.py
    Restart=always

    [Install]
    WantedBy=multi-user.target

2. Avvia e abilita il servizio:

    sudo systemctl daemon-reload
    sudo systemctl enable tonirater
    sudo systemctl start tonirater
    sudo systemctl status tonirater
