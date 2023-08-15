from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from time import sleep
import pandas as pd
import smtplib 
from email.message import EmailMessage
import schedule 

from flightinfo import flight_input

def find_cheapest_flights(flight_info):
    chromedriver_path = '/Applications/chromedriver-mac-x64'
    service = Service(executable_path=chromedriver_path)
    #options = webdriver.ChromeOptions()
    #options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(service=service)

    leaving_from = flight_info["Depature"]
    going_to = flight_info["Arrival"]
    date = flight_info["Date"]

    #going to website 
    website = "https://expedia.com"
    driver.get(website)
    sleep(50)

    #click on flights 
    flight_path = '//a[@aria-controls = "search_form_product_selector_flights"]'
    flight_element = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, flight_path))
    )
    flight_element.click()
    sleep(1)

    #click on one way 
    oneway_path = '//a[@aria-controls = "FlightSearchForm_ONE_WAY"]'
    oneway_element = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, oneway_path))
    )
    oneway_element.click()
    sleep(1)


    #change depature location
    leaving_from_xpath = '//button[@aria-label = "Leaving from"]'
    leaving_from_element = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, leaving_from_xpath))
    )
    leaving_from_element.click()
    sleep(2)

    textbox_xpath = '//input[@id="origin_select"]'
    textbox = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, textbox_xpath))
    )
    textbox.clear()
    textbox.send_keys(leaving_from)
    sleep(2)
    textbox.send_keys(Keys.DOWN, Keys.RETURN)
    sleep(1)


    #change destination 
    going_to_xpath = '//button[@aria-label = "Going to"]'
    going_to_element = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, going_to_xpath))
    )
    going_to_element.click()
    sleep(2)

    textbox_xpath = '//*[@id="destination_select"]'
    textbox = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, textbox_xpath))
    )
    textbox.clear()
    textbox.send_keys(going_to)
    sleep(2)

    textbox.send_keys(Keys.DOWN, Keys.RETURN)
    sleep(2)


    #clicking calendar 
    calandar_xpath = '//button[@class = "uitk-faux-input uitk-form-field-trigger"]'
    calandar_element = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, calandar_xpath))
    )
    calandar_element.click()
    sleep(2)



    #click the calendar date 
    trip_date_xpath = '//button[contains(@aria-label, "{}")]'.format(date)
    departing_date_element = ""
    while departing_date_element == "":
        try:
            departing_date_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, trip_date_xpath))
            )
            departing_date_element.click()
        except:
            departing_date_element = ""
            next_arrow = '//button[@data-stid = "date-picker-paging"][2]' 
            driver.find_element("xpath", next_arrow).click()
            sleep(1)

    done_button = '//button[@data-stid = "apply-date-picker"]'
    driver.find_element("xpath", done_button).click()

    #complete the search 
    searchbutton = '//button[@id = "search_button"]'
    driver.find_element("xpath", searchbutton).click()
    sleep(20)
    
    #checking the nonstop box 
    nonstop_xpath = '//*[starts-with(@id, "NUM_OF_STOPS-0-")]'
    if len(driver.find_elements("xpath", nonstop_xpath)) > 0:
        driver.find_element("xpath", nonstop_xpath).click()
        sleep(5)
        res = []
        flightinfo_xpath = "//span[contains(text(), 'Select and show fare information ')]"
        flights = driver.find_elements("xpath", flightinfo_xpath)
        if len(flights) > 0:
            if len(flights) < 5:
                for flight in flights:
                    text = flight.text 
                    price = "Price: " + text.split(",")[3].split("$")[1].split(" ")[0] + "$"
                    res.append((text.split(",")[0].split("for")[-1].title()[0:-7], text.split(",")[1].title().replace("At", ":"), text.split(",")[2].title().replace("At", ":"), price))
            else:
                for flight in flights[0:5]:
                    text = flight.text 
                    price = "Price: " + text.split(",")[3].split("$")[1].split(" ")[0] + "$"
                    res.append((text.split(",")[0].split("for")[-1].title()[0:-7], text.split(",")[1].title().replace("At", ":"), text.split(",")[2].title().replace("At", ":"), price))
            driver.quit()
            return res 
        else:
            print("No flights matching criteria")
            driver.quit()
            return res
    else:
        print("Coulden't find any nonstop flights")
        driver.quit()
        return []



def send_email(flight_information_map):
    flight_info = find_cheapest_flights(flight_information_map)

    df = pd.DataFrame(flight_info)
    if df.empty:
        print("Dataframe is empty")
        return
    else:
        email = open(r'logincredentials/username.txt').read()
        pw = open(r'logincredentials/pw.txt').read()

        msg = EmailMessage()
        msg['Subject'] = "Scraped Flight Info! {} --> {}, Departing: {}".format(flight_information_map['Departure'], flight_information_map['Arrival'], flight_information_map['Date'])
        msg['From'] = email 
        msg['To'] = email 

        msg.add_alternative('''\
            <!DOCTYPE html>
            <html>
                <body>
                    {}
                </body>
            </html>'''.format(df.to_html()), subtype="html")

        with smtplib.SMTP_SSL('smtp.gmail.com',465) as smtp:
            smtp.login(email,pw)
            smtp.send_message(msg)



schedule.clear()
schedule.every(6).hours.do(send_email(flight_input))

while True:
    schedule.run_pending()
    sleep(1)





