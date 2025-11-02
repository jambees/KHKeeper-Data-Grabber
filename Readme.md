# KH Keeper value scraping
This Project uses a Python script and Seleneium libraries to log into the Reef Factory cloud website and read the current KH value from the web page. It then can send this value out on an MQTT topic for consumption by other services (eg. Home Assistant)

There are two methods to set this up. One is using a virtual machine, the other is using an LXC container in proxmox. I'd recommend the LXC container method if you use Proxmox as this requires much fewer resources as it shares the Proxmox host's linux kernel.

## Install/setup steps - Method 1 (Virtual Machine)
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
python3 scrape-mqtt.py
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

## Install/setup steps - Method 2 (Proxmox LXC container)

This method uses less resources than a VM on your host.

From proxmox host (console rather than ssh as some scripts don't like running over ssh), run PVE helper script (from https://community-scripts.github.io/ProxmoxVE/scripts) to install ubuntu LXC:
```
bash -c "$(curl -fsSL https://raw.githubusercontent.com/community-scripts/ProxmoxVE/main/ct/ubuntu.sh)"
```

Create the LXC, select advanced install method. Most settings are self-explanatory, but key settings are:
```
- unprivileged
- 4GB disk (2GB disk is too small for the necessary packages)
- 512MB memory (256mb memory not big enough to unpack chrome installation)
- disable ipv6 
```

Edit LXC container config file /etc/pve/lxc/[lxc id].conf to allow chrome network access - add the following at the end of your LXC .conf file:
```
lxc.apparmor.profile: unconfined
lxc.cap.drop:
lxc.cgroup2.devices.allow: a
lxc.mount.auto: proc:rw sys:rw
```

Then reboot the lxc container. From proxmox host shell:
```
pct reboot [lxc_id]
```

ssh to new LXC container:
```
ssh root@[LXC container IP]
```

Paste the following script in (this will install PIP, necessary python packages and chrome browser):
```
set -e

# -----------------------------
# 1️⃣ Update & install dependencies
# -----------------------------
apt update
apt install -y wget unzip curl jq python3-pip \
libnss3 libxi6 libxcomposite1 libxcursor1 \
libxdamage1 libxrandr2 libxss1 libxshmfence1 \
libglib2.0-0 libfontconfig1 fonts-liberation \
libappindicator3-1 xdg-utils

# Upgrade pip and install Selenium
python3 -m pip install --upgrade --ignore-installed selenium
pip install python-dotenv
pip install paho-mqtt

# -----------------------------
# 2️⃣ Install Google Chrome
# -----------------------------
if ! command -v google-chrome >/dev/null 2>&1; then
    wget -O /tmp/google-chrome-stable_current_amd64.deb \
        https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
    apt install -y /tmp/google-chrome-stable_current_amd64.deb
fi

# -----------------------------
# 3️⃣ Install matching ChromeDriver
# -----------------------------
CHROME_VERSION=$(google-chrome --version | awk '{print $3}')
MAJOR_VERSION=$(echo "$CHROME_VERSION" | cut -d'.' -f1)
echo "Detected Chrome version: $CHROME_VERSION (major $MAJOR_VERSION)"

LATEST_DRIVER=$(curl -s https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json \
  | jq -r --arg MV "$MAJOR_VERSION" '
      .versions
      | map(select(.version | startswith($MV + ".")))
      | last
      | .downloads.chromedriver[]?
      | select(.platform == "linux64")
      | .url
    ')

if [ -z "$LATEST_DRIVER" ]; then
    echo "❌ Could not find ChromeDriver for version $MAJOR_VERSION"
    exit 1
fi

echo "Downloading ChromeDriver from $LATEST_DRIVER"
wget -O /tmp/chromedriver.zip "$LATEST_DRIVER"
unzip -o /tmp/chromedriver.zip -d /tmp/
mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver
chmod +x /usr/local/bin/chromedriver

# -----------------------------
# 4️⃣ Create Selenium test script
# -----------------------------
cat <<'EOF' > /root/test_selenium.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--headless=new")          # modern headless mode
options.add_argument("--no-sandbox")            # required in LXC/root
options.add_argument("--disable-dev-shm-usage") # avoid /dev/shm issues
options.add_argument("--disable-gpu")
options.add_argument("--remote-debugging-port=9222")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-software-rasterizer")

service = Service("/usr/local/bin/chromedriver")
driver = webdriver.Chrome(service=service, options=options)

driver.get("https://www.google.com")
print("Page title:", driver.title)
driver.quit()
EOF

echo "✅ Setup complete! Test with:"
echo "python3 /root/test_selenium.py"
```


Next, test that Selenium and Chrome are installed and working properly:

```
python3 test_selenium.py
```

You should get "Page title: Google" returned

Install scrape-mqtt.py script and .env supporting credentials file into /root
```
cd /root
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
python3 scrape-mqtt.py
```

It should print some progress status messages at each step. If there are errors, try to use the status messages to see where the script got to before it broke to give a clue as to where the problem may be. It's quite likely it'll be something wrong in your .env file.

## Scheduling for automatic retrieval of KH value
Set up cron schedules to call the script. I'd suggest 45mins after each of your scheduled tests as this allows enough time for a re-measurement should the device attempt this:  
```
crontab -e
```

Add lines as below - one for each run of the KH Keeper (change 10 below to the hour of the measurement. The script will get the reading 45 mins after the measurement to allow for re-measurement). Add multiple copies with different hour setting for each scheduled test. In the example below it will run at 10:45am every day.  
```
45 10 * * * pyhton3 /root/scrape-mqtt.py
```


Final crontab list example:
```
45 5 * * * python3 /root/scrape-mqtt.py
45 8 * * * python3 /root/scrape-mqtt.py
45 11 * * * python3 /root/scrape-mqtt.py
45 14 * * * python3 /root/scrape-mqtt.py
45 17 * * * python3 /root/scrape-mqtt.py
45 23 * * * python3 /root/scrape-mqtt.py
```

The above schedules cover KH Keeper measurements at 5am, 8am, 11am, 2pm, 5pm and 11pm with enough time for the measurement and a re-measurement if necessary.

Save and exit


## Final note - Please be responsible with how frequently you make calls to the Reef Factory website. Only make the bare minimum calls you need to achieve your goals.
