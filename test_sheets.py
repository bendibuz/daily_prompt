import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Set up credentials and client
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("google-creds.json", scope)
client = gspread.authorize(creds)

# Open your sheet
sheet = client.open("Ben's Daily Tasks").sheet1

# Write a test row
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
sheet.append_row([now, "✅ Google Sheets test succeeded!"])

print("Test row added to Google Sheet.")
