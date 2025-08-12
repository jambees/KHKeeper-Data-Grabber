# KH Keeper value scraping
This Project uses a Python script and Seleneium libraries to log into the Reef Factory cloud website and read the current KH value from the web page. It then can send this value out on an MQTT topic for consumption by other services (eg. Home Assistant)

## Install/setup steps
Install Ubuntu 22.04.4 LTS and select minimal installation and download updates during installing Ubuntu.  

Install SSH server (optional):
```
sudo apt install openssh-server
```

Update packages:
```
sudo apt-get update
sudo apt-get upgrade
sudo apt autoremove
```

Use the following command to turn off the Ubuntu GUI desktop from loading (optional):
```
sudo systemctl set-default multi-user.target
```

Use the following commands to install Python PIP, Selenium, Dotenv and MQTT libraries (may be better not to use sudo to run the get-pip command):
```
wget https://bootstrap.pypa.io/get-pip.py
sudo python3 get-pip.py
pip install selenium
pip install python-dotenv
pip install paho-mqtt
```

Install scrape-mqtt.py script and .env supporting credentials file into /home/[your_user]
```
cd ~
wget https://raw.githubusercontent.com/jambees/KHKeeper-Data-Grabber/refs/heads/main/src/scrape-mqtt.py
wget https://raw.githubusercontent.com/jambees/KHKeeper-Data-Grabber/refs/heads/main/src/.env
```

Edit .env file to set the following variables:
```
USERNAME="[YOUR REEF_FACTORY_LOGIN_EMAIL_ADDRESS]"
PASSWORD="[YOUR _REEF FACTORY LOGIN PASSWORD]"

KHKEEPER_DEVICE_DIV_ID="hardwareName0"
KH_VALUE_DIV_ID="rfkh01KhValue"

MQTT_BROKER_IP="[IP ADDRESS OF YOUR MQTT BROKER]"
MQTT_BROKER_PORT="[PORT OF YOUR MQTT BROKER]"
MQTT_BROKER_USERNAME="[MQTT_BROKER_USERNAME]"
MQTT_BROKER_PASSWORD="[MQTT_BROKER_PASSWORD]"
MQTT_TOPIC="KH_Keeper/KH_value" - This is the topic to publish your KH value on. Adjust as you wish
```
KHKEEPER_DEVICE_DIV_ID="hardwareName0"- This is how my KH Keeper device appears in my dashboard in the navigation bar on the left. You may need to change this and if so you'll need to find the correct div tag id for your device in the HTML page source and set it here.  

KH_VALUE_DIV_ID="rfkh01KhValue" - This is how my KH value appears on my KH Keeper device summary page. I don't know how likely it is that you will need to change this, but if so you'll need to find the correct div tag id in the HTML page source and set it here.

## Testing
Test script manually first:
```
pyhton3 scrape-mqtt.py
```

It should print some progress status messages at each step. If there are errors, try to use the status messages to see where the script got to before it broke to give a clue as to where the problem may be. It's quite likely it'll be something wrong in your .env file.

## Scheduling for automatic retrieval of KH value
Set up cron schedules to call the script. I'd suggest 45mins after each of your scheduled tests as this allows enough time for a re-measurement should the device attempt this:  
```
crontab -e
```

Add lines as below - one for each run of the KH Keeper (change 10 below to the hour of the measurement. The script will get the reading 45 mins after the measurement to allow for re-measurement). Add multiple copies with different hour setting for each scheduled test. In the example below it will run at 10:45am every day.  
```
45 10 * * * pyhton3 /home/[your_user]/scrape-mqtt.py
```


Final crontab list example:
```
45 5 * * * python3 /home/[your_user]/scrape-mqtt.py
45 8 * * * python3 /home/[your_user]/scrape-mqtt.py
45 11 * * * python3 /home/[your_user]/scrape-mqtt.py
45 14 * * * python3 /home/[your_user]/scrape-mqtt.py
45 17 * * * python3 /home/[your_user]/scrape-mqtt.py
45 23 * * * python3 /home/[your_user]/scrape-mqtt.py
```

The above schedules cover KH Keeper measurements at 5am, 8am, 11am, 2pm, 5pm and 11pm with enough time for the measurement and a re-measurement if necessary.
