import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import time, telepot, os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import creds


def main():

    url = 'https://gorove.in/tagpartner/dashboard'

    # Following is the template to open Chrome(browser) in background(headless) mode.
    # op = webdriver.ChromeOptions()
    # op.add_argument('headless')
    # driver = webdriver.Chrome(options=op)

    # Heroku Template
    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), options=chrome_options)

    driver.get(url)
    time.sleep(10)

    login_element = driver.find_element_by_xpath('//*[@id="tagpartner_auth"]/div[2]/form/div[1]/input')
    login_element.send_keys(creds.EMAIL_ADDRESS)

    password_element = driver.find_element_by_xpath('//*[@id="tagpartner_auth"]/div[2]/form/div[2]/input')
    password_element.send_keys(creds.PASSWORD)

    submit_button = driver.find_element_by_xpath('//*[@id="tagpartner_auth"]/div[2]/form/button')
    submit_button.click()

    time.sleep(20)
    odometer_reading = driver.find_element_by_xpath('//*[@id="tagpartnerCntr"]/div[3]/div[1]/div/div/div/div/div[2]/div[1]/div/p[2]')
    car_status = driver.find_element_by_xpath('//*[@id="tagpartnerCntr"]/div[3]/div[1]/div/div/div/div/div[2]/div[2]/div/p[2]')

    odometer_reading = odometer_reading.text.split('km') #Converting string to integer so the same can be store in Google Sheets.
    odometer_reading = odometer_reading[0]

    current_reading = [odometer_reading, car_status.text]

    google_api()

    if google_api.previous_reading == current_reading:
        pass
    else:
        km = current_reading[0].split('km')

        KM_Diff = int(km[0]) - int(google_api.previous_reading[0])

        google_api.sheet.update_cell(1, 1, km[0])
        google_api.sheet.update_cell(1, 2, current_reading[1])

        current_odometer_reading = 'Odometer Reading: ' + odometer_reading +'km'
        current_car_status = 'Car Status: ' + car_status.text
        KM_Diff = 'KM Diff: ' + str(KM_Diff)

        current_reading = [current_odometer_reading, current_car_status, KM_Diff]

        rove_dashboard_updates = []

        for i in current_reading:
            rove_dashboard_updates.append(i)

        rove_dashboard_updates = '\n'.join(rove_dashboard_updates)

        ROVE_bot = telepot.Bot(creds.TELEGRAM_ROVE_BOT_ID) # calling ROVE bot

        ROVE_bot.sendMessage(creds.TELEGRAM_ROVE_GROUP_ID, rove_dashboard_updates) # -272776323 is ROVE group ID on Telegram.

        # ROVE_bot.sendMessage(creds.TELEGRAM_MY_PERSONAL_ID, rove_dashboard_updates) # 964309207 is my personal ID on Telegram.

def google_api():

    scope = ["https://spreadsheets.google.com/feeds",
            'https://www.googleapis.com/auth/spreadsheets',
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/drive"]     

    google_creds = ServiceAccountCredentials.from_json_keyfile_dict(creds.keyfile_dict, scope)
    client = gspread.authorize(google_creds)

    google_api.sheet = client.open("ROVE").worksheet('TripLog')

    kms = google_api.sheet.row_values(1)

    car_status = google_api.sheet.col_values(2)

    google_api.previous_reading = [kms[0], car_status[0]]

main()

