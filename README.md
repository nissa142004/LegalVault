# LegalVault

This project has a Flask backend and a React + Vite frontend.

## Requirements

- Python 3.12
- Node.js 18+
- MongoDB running locally, or a valid MongoDB connection in the backend .env file

## 1) Start the backend

Open a terminal in the project root:

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

If port 5000 is already in use, run the backend on another port:

```bash
FLASK_PORT=5001 python app.py
```

If you want to use the default port, just run:

```bash
python app.py
```

Check the backend:

```bash
curl http://127.0.0.1:5001/api/status
```

You should see JSON like:

```json
{
  "service": "LegalVault Backend",
  "status": "ok",
  "mongodb": "connected"
}
```

## 2) Start the frontend

Open a second terminal in the project root:

```bash
cd frontend
npm install
VITE_API_BASE_URL=http://127.0.0.1:5001 npm run dev -- --host 0.0.0.0 --port 5173
```

Then open the app in your browser:

```text
http://localhost:5173
```

### Frontend notes

- The frontend talks to the backend through `VITE_API_BASE_URL`.
- In this project setup, the API is expected on port `5001` because port `5000` is often already in use by another local service.
- If your backend runs on a different port, change the URL like this:

```bash
VITE_API_BASE_URL=http://127.0.0.1:YOUR_PORT npm run dev -- --host 0.0.0.0 --port 5173
```

## 3) Train and evaluate the classifier

Activate the backend virtual environment:

```bash
cd backend
source .venv/bin/activate
```

Train the legal document category classifier:

```bash
python scripts/train_classifier.py \
  --dataset /Users/nisindusathsara/Desktop/data/real_legal_dataset_2000_training_only.csv
```

The dataset must contain `text` and `label` columns. The command prints training accuracy, test accuracy, precision, recall, F1-score, and a confusion matrix. It saves the trained model and evaluation metrics to:

```text
backend/ml/artifacts/legal_category_model.joblib
backend/ml/artifacts/evaluation.json
```

To inspect the saved metrics later:

```bash
python -m json.tool ml/artifacts/evaluation.json
```

Use `test_accuracy` or `accuracy` as the main accuracy measure. For example, `0.85` means 85% accuracy on the independent test set. Test accuracy is more useful than training accuracy because the model did not train on those test samples.

## 4) Stop the app

Press Ctrl + C in each terminal to stop the backend and frontend.

## 5) Troubleshooting

- If Flask says port `5000` is already in use, use a different port like `5001`.
- If MongoDB is not running, the backend health check will fail.
- If the frontend cannot connect, make sure the backend is running and `VITE_API_BASE_URL` matches the backend URL.
