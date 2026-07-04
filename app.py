import os
import time
from flask import Flask, request, jsonify, render_template_string
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import traceback

app = Flask(__name__)

def open_meesho_seller(username, password):
    print("\n[+] Supplier Browser open ho raha hai...")
    download_dir = "/tmp"
    chrome_prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    }

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")  # Render par background me chalane ke liye zaroori hai
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.binary_location = "/usr/bin/google-chrome" 
    
    options.add_experimental_option("prefs", chrome_prefs)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    try:
        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=options)
        
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })

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
        time.sleep(10)  # Waiting for login / OTP bypass if any

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
        return "Automation completed successfully! Labels processed."

    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        return f"Error occurred: {str(e)}"

# Frontend UI (Login Form) jo Render link par dikhega
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Meesho Automation Hub</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f7f6; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-container { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); width: 100%; max-width: 400px; text-align: center; }
        h2 { color: #ff2e63; margin-bottom: 20px; }
        input[type="text"], input[type="password"] { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background-color: #ff2e63; color: white; border: none; border-radius: 4px; font-size: 16px; cursor: pointer; font-weight: bold; }
        button:hover { background-color: #e02454; }
        .info { font-size: 12px; color: #666; margin-top: 15px; }
    </style>
</head>
<body>
    <div class="login-container">
        <h2>Meesho Automation Bot</h2>
        <form action="/run-automation" method="POST">
            <input type="text" name="username" placeholder="Enter Email or Phone Number" required>
            <input type="password" name="password" placeholder="Enter Meesho Password" required>
            <button type="submit">Start Automation</button>
        </form>
        <p class="info">Note: Click karne ke baad background me processing start ho jayegi.</p>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    # Jab aap link par click karenge toh yeh HTML Form dikhega
    return render_template_string(HTML_TEMPLATE)

@app.route('/run-automation', methods=['POST'])
def run_bot():
    username = request.form.get("username")
    password = request.form.get("password")
    
    if not username or not password:
        return "<h3>Error: Username or Password cannot be empty!</h3><a href='/'>Go Back</a>"
        
    # Automation trigger hoga
    result = open_meesho_seller(username, password)
    
    if "Error" in result:
        return f"<h3>Automation Failed!</h3><p>{result}</p><a href='/'>Try Again</a>"
    return f"<h3>Success!</h3><p>{result}</p><a href='/'>Go Back</a>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
