import paho.mqtt.client as mqtt
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import time
import os

# ===== USER SETTINGS =====
load_dotenv()
USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')
LOGIN_URL = "https://www.desktop.reeffactory.com/?state=smartreef"
KHKEEPER_DEVICE_DIV_ID = os.getenv('KHKEEPER_DEVICE_DIV_ID')
KH_DIV_ID = os.getenv('KH_VALUE_DIV_ID')
MQTT_BROKER_IP = os.getenv('MQTT_BROKER_IP')
MQTT_BROKER_PORT = int(os.getenv('MQTT_BROKER_PORT'))
MQTT_BROKER_USERNAME = os.getenv('MQTT_BROKER_USERNAME')
MQTT_BROKER_PASSWORD = os.getenv('MQTT_BROKER_PASSWORD')
MQTT_TOPIC = os.getenv('MQTT_TOPIC')
# =========================

# Chrome in headless mode
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
print("Starting Chrome")
driver = webdriver.Chrome(options=options)

try:
    # 1. Go to login page
    print("Getting login page")
    driver.get(LOGIN_URL)
    print("Getting login url")
    time.sleep(1)  # wait for page to load

    # 2. Fill in login form (adjust selectors as needed)
    driver.find_element(By.NAME, "username").send_keys(USERNAME)
    driver.find_element(By.NAME, "password").send_keys(PASSWORD)

    print("Waiting until login button clickable")
    # Wait until the login div is clickable
    login_div = WebDriverWait(driver, 1).until(EC.element_to_be_clickable((By.ID, "userButtonLogin")))
    print("Clicking the login button")
    login_div.click()


    print("Waiting 2 seconds for dashboard to load")
    # 3. Wait for dashboard to load
    time.sleep(1)  # increase if your dashboard loads slowly
    print("Waiting for KH keeper device page to load")
    KHKeeper_div = WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.ID, KHKEEPER_DEVICE_DIV_ID)))
    KHKeeper_div.click()

    time.sleep(1)
    print("Finding KH value")
    # 4. Find KH value
    kh_element = driver.find_element(By.ID, KH_DIV_ID)
    print(kh_element.text)


    # MQTT broker details
    broker = MQTT_BROKER_IP
    port = MQTT_BROKER_PORT
    topic = MQTT_TOPIC
    value = kh_element.text           # value to publish

    # Create a new MQTT client instance
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    print("Connecting to MQTT broker and publishing messsage")
    # Connect to the broker
    client.username_pw_set(username=MQTT_BROKER_USERNAME, password=MQTT_BROKER_PASSWORD)
    client.connect(broker, port)

    # Publish the value to the topic
    client.publish(topic, value, retain=True)       # retain flag True to persist value over HA restarts rather than unknown

    # Disconnect from the broker
    client.disconnect()

finally:
    driver.quit()
