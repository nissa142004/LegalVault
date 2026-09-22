# LegalVault Backend

## Run the backend

Open a terminal and run:

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
python app.py
```

If port 5000 is already taken, run it on a free port instead:

```bash
cd backend
source .venv/bin/activate
FLASK_PORT=5001 python app.py
```

Check the server:

```bash
curl http://127.0.0.1:5001/api/status
```

You should get a response like:

```json
{
  "service": "LegalVault Backend",
  "status": "ok",
  "mongodb": "connected"
}
```
