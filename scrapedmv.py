import os
import json
import time
import gspread
import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from oauth2client.service_account import ServiceAccountCredentials
from main import extract_times_for_all_locations_firefox, format_results_for_discord

# --- Email Setup ---
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# --- Get Emails from Google Sheet ---
def get_email_list():
    creds_dict = json.loads(os.getenv("GOOGLE_CREDS_JSON"))
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    sheet = client.open("Signup for Alerts Now").sheet1  # Your sheet name here
    email_list = sheet.col_values(6)  # Column F
    return [email for email in email_list if email and "@" in email]

# --- Send Email to a Single Recipient ---
def send_email_alert(message_content, recipient):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = recipient
    msg["Subject"] = "DMV Appointment Alert"

    msg.attach(MIMEText(message_content, "plain"))
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        print(f"Email sent to {recipient}")
    except Exception as e:
        print(f"Failed to send email to {recipient}: {e}")

# --- Main Loop ---
if __name__ == "__main__":
    while True:
        print(f"Running scraper at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run your scraping logic
        results = extract_times_for_all_locations_firefox(
            url="https://skiptheline.ncdot.gov",
            driver_path=os.getenv("GECKODRIVER_PATH"),
            binary_path=os.getenv("FIREFOX_BINARY_PATH"),
            allowed_locations_filter=None,
            filtering_active=False,
            date_filter_enabled=False,
            start_date=None,
            end_date=None,
            time_filter_enabled=False,
            start_time=None,
            end_time=None
        )

        message = format_results_for_discord(results)
        
        if message:
            print("Appointments found. Sending alerts...")
            for email in get_email_list():
                send_email_alert(message, email)
        else:
            print("No appointments found.")

        # Wait 30 minutes + random delay
        sleep_seconds = 1800 + random.randint(10, 30)
        print(f"Sleeping for {sleep_seconds // 60} minutes and {sleep_seconds % 60} seconds...")
        try:
            time.sleep(sleep_seconds)
        except KeyboardInterrupt:
            print("Script interrupted by user. Exiting.")
            break
