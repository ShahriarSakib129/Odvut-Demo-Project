# ODVUT Backend Demo

Simple Flask backend + HTML frontend demo.

## Local test

```bash
pip install -r requirements.txt
python app.py
```

Then open:

http://127.0.0.1:5000

Click **Check Backend**.

## Deployment

This project is prepared for a Python web service using Gunicorn.

Start command:

```bash
gunicorn app:app
```
