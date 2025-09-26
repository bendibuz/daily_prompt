venv\Scripts\Activate.ps1
# pip install -r requirements.txt
uvicorn app.main:app --reload --proxy-headers --forwarded-allow-ips="*"
ngrok http 8000