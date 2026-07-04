import os
import time
import shutil
import threading
from flask import Flask, request, jsonify, render_template_string, send_from_directory
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)

execution_logs = []
bot_status = "idle"  # idle, running, completed, failed
downloaded_filename = None

def log_message(message):
    print(message)
    execution_logs.append(message)

def open_meesho_seller_thread(username, password):
    global execution_logs, bot_status, downloaded_filename
    bot_status = "running"
    downloaded_filename = None
    execution_logs.clear()
    
    log_message("[+] Supplier Browser (Headless Mode) open ho raha hai...")
    
    download_dir = "/tmp/meesho_downloads"
    if os.path.exists(download_dir):
        shutil.rmtree(download_dir)
    os.makedirs(download_dir)

    chrome_prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    }

    options = webdriver.ChromeOptions()
    options.binary_location = "/usr/bin/google-chrome" # Docker fixed path
    options.add_argument("--headless=new")  
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    options.add_experimental_option("prefs", chrome_prefs)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    try:
        driver = webdriver.Chrome(options=options)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })

        # ================= STEP 1: LOGIN =================
        log_message("[+] Meesho Seller portal par jaa rahe hain...")
        driver.get("https://supplier.meesho.com/panel/v3/new/root/login")
        wait = WebDriverWait(driver, 15)

        log_message("[+] Credentials fill kiye jaa rahe hain...")
        email_field = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='text' or @name='email_or_phone']")))
        email_field.clear()
        email_field.send_keys(username)

        password_field = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='password' or @name='password']")))
        password_field.clear()
        password_field.send_keys(password)

        time.sleep(1)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        log_message("[====== SUCCESS ======>] Login button click ho gaya hai.")
        
        time.sleep(10)

        checkbox_xpaths = ["//thead//input[@type='checkbox']", "//th//input[@type='checkbox']", "//input[@type='checkbox']"]

        # ================= STEP 2: PENDING ORDERS =================
        log_message("[+] Direct Pending link par jaa rahe hain...")
        driver.get("https://supplier.meesho.com/panel/v3/new/fulfillment/z7l5i/orders/pending")
        time.sleep(6)

        log_message("[+] Pending orders check aur select kar rahe hain...")
        select_all_pending = None
        for xpath in checkbox_xpaths:
            try:
                select_all_pending = WebDriverWait(driver, 4).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                break
            except: continue

        if select_all_pending:
            if not select_all_pending.is_selected():
                driver.execute_script("arguments[0].click();", select_all_pending)
                log_message("[+] Sabhi pending orders ko select kar liya gaya hai.")
            time.sleep(2)

            accept_btn_xpaths = ["//button[contains(., 'Accept Selected')]", "//*[contains(text(), 'Accept') or contains(text(), 'Ready to Ship')]"]
            accept_clicked = False
            for btn_xpath in accept_btn_xpaths:
                try:
                    accept_btn = driver.find_element(By.XPATH, btn_xpath)
                    driver.execute_script("arguments[0].click();", accept_btn)
                    accept_clicked = True
                    break
                except: continue
            
            if accept_clicked:
                log_message("[=>] Sabhi pending orders bulk me Accept ho gaye!")
                time.sleep(8)
            else:
                log_message("[-] Bulk Accept button nahi mila.")
        else:
            log_message("[💡 INFO] Koi bhi pending order nahi mila.")

        # ================= STEP 3: READY TO SHIP (DOWNLOAD) =================
        log_message("[+] Direct Ready to Ship link par jaa rahe hain...")
        driver.get("https://supplier.meesho.com/panel/v3/new/fulfillment/z7l5i/orders/ready-to-ship")
        time.sleep(6)

        log_message("[+] Un-downloaded labels ko select kar rahe hain...")
        select_all_rts = None
        for rts_xpath in checkbox_xpaths:
            try:
                select_all_rts = WebDriverWait(driver, 4).until(EC.element_to_be_clickable((By.XPATH, rts_xpath)))
                break
            except: continue

        if select_all_rts:
            if not select_all_rts.is_selected():
                driver.execute_script("arguments[0].click();", select_all_rts)
                log_message("[+] Saare RTS orders select ho gaye.")
            time.sleep(2)

            download_btn_xpaths = ["//button[contains(., 'Download Selected Labels')]", "//button[contains(., 'Download')]"]
            download_clicked = False
            for btn_xpath in download_btn_xpaths:
                try:
                    download_btn = driver.find_element(By.XPATH, btn_xpath)
                    driver.execute_script("arguments[0].click();", download_btn)
                    download_clicked = True
                    log_message("[====== SUCCESS ======>] Saare naye labels download ho rahe hain!")
                    time.sleep(8)  
                    break
                except: continue
                
            if not download_clicked:
                log_message("[-] Bulk Download button nahi mil paya.")
        else:
            log_message("[💡 INFO] RTS section me koi pending label nahi mila.")
        
        driver.quit()

        files = os.listdir(download_dir)
        if files:
            log_message(f"[🎉 FINISHED] Download completed! File name: {files[0]}")
            downloaded_filename = files[0]
            bot_status = "completed"
        else:
            log_message("[⚠️ FINISHED] Process complete, koi file download nahi hui.")
            bot_status = "no_file"

    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        log_message(f"[X] Error aaya: {str(e)}")
        bot_status = "failed"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Meesho Automation Hub</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; background-color: #1a1a2e; color: #fff; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .container { background: #162447; padding: 30px; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.3); width: 100%; max-width: 500px; text-align: center; }
        h2 { color: #e43f5a; margin-bottom: 20px; font-weight: 600; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #1f4068; background: #1f4068; color: white; border-radius: 6px; box-sizing: border-box; font-size: 14px; }
        button { width: 100%; padding: 14px; background-color: #e43f5a; color: white; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; font-weight: bold; margin-top: 15px; transition: 0.3s; }
        button:disabled { background-color: #555; cursor: not-allowed; }
        #terminal { background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 15px; margin-top: 20px; height: 180px; overflow-y: auto; text-align: left; font-family: 'Courier New', monospace; font-size: 13px; color: #38bdf8; display: none; }
        .log-line { margin-bottom: 6px; border-left: 3px solid #e43f5a; padding-left: 8px; }
        #download-area { display: none; margin-top: 20px; padding: 15px; background: #10b981; color: white; border-radius: 6px; font-weight: bold; }
        #download-area a { color: white; text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Meesho Automation Bot</h2>
        <div id="form-panel">
            <input type="text" id="username" placeholder="Enter Email or Phone Number" required>
            <input type="password" id="password" placeholder="Enter Meesho Password" required>
            <button id="start-btn" onclick="startAutomation()">Start Automation System</button>
        </div>

        <div id="terminal"></div>
        <div id="download-area">🎉 Done! <a id="dl-link" href="#" target="_blank">Click here to Download Labels PDF</a></div>
    </div>

    <script>
        let statusInterval;

        function startAutomation() {
            const user = document.getElementById("username").value;
            const pass = document.getElementById("password").value;
            if(!user || !pass) { alert("Please enter credentials!"); return; }

            document.getElementById("start-btn").disabled = true;
            document.getElementById("start-btn").innerText = "Processing System...";
            document.getElementById("terminal").style.display = "block";

            // Async hit karenge backend ko
            fetch('/run-automation', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: user, password: pass })
            })
            .then(res => res.json())
            .then(data => {
                // Logs aur status check karna shuru
                statusInterval = setInterval(checkStatus, 1500);
            })
            .catch(err => {
                alert("Trigger Failed!");
            });
        }

        function checkStatus() {
            // Logs sync
            fetch('/get-logs')
            .then(res => res.json())
            .then(data => {
                const term = document.getElementById("terminal");
                term.innerHTML = "";
                data.logs.forEach(log => {
                    term.innerHTML += `<div class='log-line'>${log}</div>`;
                });
                term.scrollTop = term.scrollHeight;

                // Status logic check
                if (data.status === "completed") {
                    clearInterval(statusInterval);
                    document.getElementById("start-btn").innerText = "Completed!";
                    const dlArea = document.getElementById("download-area");
                    document.getElementById("dl-link").href = "/download-file/" + data.file;
                    dlArea.style.display = "block";
                    window.location.href = "/download-file/" + data.file;
                } else if (data.status === "failed" || data.status === "no_file") {
                    clearInterval(statusInterval);
                    document.getElementById("start-btn").disabled = false;
                    document.getElementById("start-btn").innerText = "Start Automation System";
                    alert("Automation stopped or error occurred. Check logs.");
                }
            });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/get-logs')
def get_logs():
    return jsonify({
        "logs": execution_logs,
        "status": bot_status,
        "file": downloaded_filename
    })

@app.route('/run-automation', methods=['POST'])
def run_bot():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    
    # Threading use kar rahe hain taaki backend bina rukawat background me chalta rahe
    t = threading.Thread(target=open_meesho_seller_thread, args=(username, password))
    t.start()
    
    return jsonify({"status": "triggered"})

@app.route('/download-file/<filename>')
def download_file(filename):
    return send_from_directory("/tmp/meesho_downloads", filename, as_attachment=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
