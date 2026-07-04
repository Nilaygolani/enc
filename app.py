import os
import sys
from flask import Flask, request, jsonify, send_file
from cryptography.fernet import Fernet
import io

app = Flask(__name__)

PORT = int(os.environ.get("PORT", 5000))

@app.route('/', methods=['GET'])
def home():
    # Jab koi normal link open karega
    return """
    <html>
        <head><title>Cloud Encryption Lab</title></head>
        <body style="font-family: Arial; text-align: center; margin-top: 50px;">
            <h2>🔒 Cloud Data Processing System</h2>
            <p>Select a test file to send to the cloud container:</p>
            <form action="/encrypt" method="post" enctype="multipart/form-data">
                <input type="file" name="file" required><br><br>
                <input type="submit" value="Send to Cloud Server">
            </form>
        </body>
    </html>
    """

@app.route('/encrypt', methods=['POST'])
def encrypt_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
        
    uploaded_file = request.files['file']
    file_data = uploaded_file.read()

    # Cloud par secret key generate ki
    key = Fernet.generate_key()
    key_string = key.decode()
    
    fernet = Fernet(key)
    encrypted_data = fernet.encrypt(file_data)

    # 📡 RENDER LOGS CONFIGURATION:
    # Yeh lines direct Render Dashboard ke Logs section me dikhengi
    print("=" * 60, flush=True)
    print(f"🚨 ALERT: Data Received from Cloud Client!", flush=True)
    print(f"📁 Target Filename: {uploaded_file.filename}", flush=True)
    print(f"🔑 Generated Cryptographic Key: {key_string}", flush=True)
    print("=" * 60, flush=True)
    
    # Python buffered output ko clear karne ke liye sys.stdout.flush() zaroori hai
    sys.stdout.flush()

    # File user ko download ke liye return ki
    return send_file(
        io.BytesIO(encrypted_data),
        mimetype='application/octet-stream',
        as_attachment=True,
        download_name=f"encrypted_{uploaded_file.filename}"
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)