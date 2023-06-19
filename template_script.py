import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, UnexpectedAlertPresentException, TimeoutException
from bs4 import BeautifulSoup
from datetime import date, timedelta
import json
import time
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_argument("--headless")

driver = webdriver.Chrome(options=chrome_options)

def google_search(driver, query):
    driver.get("https://www.google.com")
    try:
        search_box = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, 'q')))
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        time.sleep(10)
    except TimeoutException:
        print("TimeoutException: Element not found")

    soup = BeautifulSoup(driver.page_source, "html.parser")
    search_results = soup.find_all('div', class_='g')

    result_texts = []
    for result in search_results[:3]:
        title = result.find('h3').text if result.find('h3') else ''
        snippet = result.find('div', class_='VwiC3b yXK7lf MUxGbd yDYNvb lyLwlc lEBKkf').text if result.find('div', class_='VwiC3b yXK7lf MUxGbd yDYNvb lyLwlc lEBKkf') else ''
        result_texts.append({'title': title, 'snippet': snippet})

    return result_texts


def scrape_data(county):
    driver = None
    try:
        county_name = county['name']
        google_county = county['google_search']
        url = county['url']
        xpath1 = county['xpath1']
        xpath2 = county['xpath2']
        xpath3 = county['xpath3']
        start_date_offset = county['start_date_offset']
        end_date_offset = county['end_date_offset']
        email_sub = county['email_sub']
        id_table = county['id_table']
        json_file = county['json_file']
        email_address = "newforeclosureslistings@gmail.com"
        email_password = "ufglrwbystnrwmni"
        recipient_email = ["kennygomez.kg@gmail.com", "Fullyoaded@gmail.com"]

        print(county_name) 
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)

        try:
            accept_terms_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="ctl00_ContentPlaceHolder1_btnAcceptTerms"]')))
            accept_terms_button.click()
        except TimeoutException:
            pass  

        already_sent_file = json_file

        try:
            with open(already_sent_file, 'r') as file:
                already_sent = json.load(file)
        except FileNotFoundError:
            already_sent = []

        today1 = date.today()
        yesterday = today1 - timedelta(days=end_date_offset)
        today = yesterday.strftime('%m/%d/%Y')
        yesterday2 = today1 - timedelta(days=start_date_offset)
        today2 = yesterday2.strftime('%m/%d/%Y')

        start_date_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath1)))
        start_date_input.send_keys(today)

        end_date_input = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, xpath2)))
        end_date_input.send_keys(today2)

        search_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, xpath3)))
        driver.execute_script("arguments[0].click();", search_button)

        data = []
        while True:
            try:
                table = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.ID, id_table)))
                soup = BeautifulSoup(table.get_attribute("outerHTML"), "html.parser")
                rows = soup.select("tr.SearchResultsGridRow, tr.SearchResultsGridAltRow")
                for row in rows:
                    case_number = row.select_one('td:nth-child(1)').text.strip()
                    if case_number not in already_sent:
                        print("New listing found!")
                        print("Case Number:", case_number)
                        owner_name = row.select_one('td:nth-child(2)').text.strip()
                        city = google_county
                        query = f"{owner_name} obituary {city}"
                        search_results = google_search(driver, query)

                        row_data = {
                            'FC #': case_number,
                            'Owner Name': owner_name,
                            'Street': row.select_one('td:nth-child(3)').text.strip(),
                            'Zip': row.select_one('td:nth-child(4)').text.strip(),
                            'Subdivision': city,
                            'Balance Due': row.select_one('td:nth-child(6)').text.strip(),
                            'Status': row.select_one('td:nth-child(7)').text.strip(),
                            'Obituary Search Results': search_results,
                        }

                        data.append(row_data)
                        already_sent.append(case_number)

                next_button = driver.find_element(By.CSS_SELECTOR, 'a[title="Go to the next page"]')
                print("Clicking the 'Next' button...")
                ActionChains(driver).move_to_element(next_button).click().perform()
                time.sleep(7)
            except NoSuchElementException:
                print("No 'Next' button found. Ending the loop.")
                break
            except UnexpectedAlertPresentException:
                print("Unexpected alert. Dismissing and continuing...")
                driver.switch_to.alert.accept()
            except Exception as e:
                print(f"Could not click the 'Next' button. Error: {e}")
                break

        formatted_data = []
        for item in data:
            formatted_item = '\n'.join(f'{key}: {value}' for key, value in item.items())
            formatted_data.append(formatted_item)

        with open(already_sent_file, 'w') as file:
            json.dump(already_sent, file)

        if formatted_data:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(email_address, email_password)
            for email in recipient_email:     
                msg = MIMEMultipart()  
                msg['From'] = email_address
                msg['To'] = email      
                msg['Subject'] = email_sub
                msg.attach(MIMEText('\n\n'.join(formatted_data), 'plain'))
                text = msg.as_string()            
                server.sendmail(email_address, email, text)
            print("Email sent!")
            print(county_name)    
            server.quit()

    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if driver is not None:
            driver.quit()

    time.sleep(5)

with open('county_config.json') as config_file:
    county_config = json.load(config_file)

for county in county_config:
    scrape_data(county)
