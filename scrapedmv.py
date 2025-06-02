import os
import time
import smtplib
import json
import gspread
from email.mime.text import MIMEText
from oauth2client.service_account import ServiceAccountCredentials
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By

# Set up headless Firefox scraping
def extract_times_for_all_locations_firefox():
    options = Options()
    options.headless = True
    driver = webdriver.Firefox(options=options)

    url = "https://skiptheline.ncdot.gov/"
    print("Navigating to URL:", url)
    driver.get(url)
    time.sleep(3)

    page_text = driver.find_element(By.TAG_NAME, "body").text
    driver.quit()

    if "No appointments" in page_text:
        return []
    else:
        return [page_text]

# Format for email body

def format_results_for_discord(results):
    if not results:
        return "No DMV appointments available at this time."
    return "\n\n".join(results)

# Read emails from Google Sheet (column F)
def get_email_list():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_json = json.loads(os.environ["GOOGLE_CREDS_JSON"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
    client = gspread.authorize(creds)

    sheet = client.open_by_url(os.environ["SHEET_URL"]).sheet1
    emails = sheet.col_values(6)[1:]  # Skip header, column F
    return [email.strip() for email in emails if email.strip() != ""]

# Send alert email

def send_email(to_email, message):
    from_email = os.environ["EMAIL_ADDRESS"]
    password = os.environ["EMAIL_PASSWORD"]

    msg = MIMEText(message)
    msg["Subject"] = "DMV Appointment Alert"
    msg["From"] = from_email
    msg["To"] = to_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(from_email, password)
        server.sendmail(from_email, to_email, msg.as_string())
        print(f"Email sent to: {to_email}")

# Run scraper and send alerts

def run():
    print("Running scraper at", time.strftime("%Y-%m-%d %H:%M:%S"))
    results = extract_times_for_all_locations_firefox()
    message = format_results_for_discord(results)

    for email in get_email_list():
        send_email(email, message)

# Run every 30 minutes in loop
if __name__ == "__main__":
    while True:
        run()
        print("Sleeping for 30 minutes...")
        time.sleep(30 * 60)
