import os
import time
from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import traceback

app = Flask(__name__)

def open_meesho_seller(username, password):
    print("\n[+] Supplier Browser open ho raha hai...")
    
    download_dir = "/tmp"  # Render par sirf /tmp directory me write permission hoti hai
    chrome_prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    }

    options = webdriver.ChromeOptions()
    # ------ RENDER/HEADLESS SETTINGS ------
    options.add_argument("--headless=new")  # Background me chalane ke liye compulsory hai
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # Render ke environment paths (Hum baki setup build script me karenge)
    options.binary_location = "/usr/bin/google-chrome" 
    
    options.add_argument("--start-maximized")
    options.add_experimental_option("detach", True)
    options.add_experimental_option("prefs", chrome_prefs)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    # Render par ChromeDriverManager ki jagah direct path use karna secure hota hai
    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })

    try:
        # ================= STEP 1: LOGIN =================
        driver.get("https://supplier.meesho.com/panel/v3/new/root/login")
        wait = WebDriverWait(driver, 15)

        email_field = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='text' or @name='email_or_phone']")))
        email_field.clear()
        email_field.send_keys(username)

        password_field = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='password' or @name='password']")))
        password_field.clear()
        password_field.send_keys(password)

        time.sleep(1)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        
        # NOTE: Render headless hai, agar OTP aaya toh ye block ho jayega. 
        # Isliye Meesho account me OTP/Captcha disabled hona chahiye ya 2FA setup script me handle hona chahiye.
        time.sleep(10) 

        checkbox_xpaths = ["//thead//input[@type='checkbox']", "//th//input[@type='checkbox']", "//input[@type='checkbox']"]

        # ================= STEP 2: PENDING ORDERS =================
        driver.get("https://supplier.meesho.com/panel/v3/new/fulfillment/z7l5i/orders/pending")
        time.sleep(6)

        select_all_pending = None
        for xpath in checkbox_xpaths:
            try:
                select_all_pending = WebDriverWait(driver, 4).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                break
            except: continue

        if select_all_pending:
            if not select_all_pending.is_selected():
                driver.execute_script("arguments[0].click();", select_all_pending)
            time.sleep(2)

            accept_btn_xpaths = ["//button[contains(., 'Accept Selected')]", "//button[contains(., 'Accept Order')]"]
            for btn_xpath in accept_btn_xpaths:
                try:
                    accept_btn = driver.find_element(By.XPATH, btn_xpath)
                    driver.execute_script("arguments[0].click();", accept_btn)
                    break
                except: continue
            time.sleep(8)

        # ================= STEP 3: READY TO SHIP (DOWNLOAD) =================
        driver.get("https://supplier.meesho.com/panel/v3/new/fulfillment/z7l5i/orders/ready-to-ship")
        time.sleep(6)

        select_all_rts = None
        for rts_xpath in checkbox_xpaths:
            try:
                select_all_rts = WebDriverWait(driver, 4).until(EC.element_to_be_clickable((By.XPATH, rts_xpath)))
                break
            except: continue

        if select_all_rts:
            if not select_all_rts.is_selected():
                driver.execute_script("arguments[0].click();", select_all_rts)
            time.sleep(2)

            download_btn_xpaths = ["//button[contains(., 'Download Selected Labels')]", "//button[contains(., 'Download')]"]
            for btn_xpath in download_btn_xpaths:
                try:
                    download_btn = driver.find_element(By.XPATH, btn_xpath)
                    driver.execute_script("arguments[0].click();", download_btn)
                    time.sleep(5)
                    break
                except: continue
        
        driver.quit()
        return "Automation completed successfully!"

    except Exception as e:
        driver.quit()
        return f"Error: {str(e)}"

@app.route('/')
def home():
    return "Meesho Automation Bot is Running Live!"

@app.route('/run', methods=['POST'])
def run_bot():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    
    if not username or not password:
        return jsonify({"status": "failed", "message": "Missing credentials"}), 400
        
    result = open_meesho_seller(username, password)
    return jsonify({"status": "done", "message": result})

if __name__ == "__main__":
    # Render dynamic PORT use karta hai
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
