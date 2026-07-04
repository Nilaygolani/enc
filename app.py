"""import os
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




    """


import os
from flask import Flask, render_template_string

app = Flask(__name__)

# Port configuration for deployment/local running
PORT = int(os.environ.get("PORT", 5000))

# Standard HTML, CSS, aur JavaScript Frontend Component (Single String Container)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Local Media Container Viewer</title>
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            text-align: center; 
            background-color: #1a1a1a; 
            color: #ffffff;
            padding: 20px; 
            margin: 0;
        }
        .container {
            max-width: 800px;
            margin: 40px auto;
            background: #2d2d2d;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.3);
        }
        .gallery { 
            display: flex; 
            flex-wrap: wrap; 
            justify-content: center; 
            gap: 15px; 
            margin-top: 30px; 
        }
        .gallery img { 
            width: 140px; 
            height: 140px; 
            object-fit: cover; 
            border-radius: 8px; 
            border: 2px solid #444;
            transition: transform 0.2s;
        }
        .gallery img:hover {
            transform: scale(1.05);
            border-color: #007bff;
        }
        .upload-btn { 
            background-color: #007bff; 
            color: white; 
            padding: 12px 24px; 
            border: none; 
            border-radius: 6px; 
            cursor: pointer; 
            font-size: 16px; 
            font-weight: bold;
            box-shadow: 0 4px 6px rgba(0,123,255,0.2);
        }
        .upload-btn:hover {
            background-color: #0056b3;
        }
    </style>
</head>
<body>

    <div class="container">
        <h2>🖼️ Local Media Gallery Viewer</h2>
        <p>Select images from your device storage to render them instantly inside the UI grid:</p>
        
        <input type="file" id="mediaReceiver" accept="image/*" multiple style="display: none;">
        <button class="upload-btn" onclick="document.getElementById('mediaReceiver').click()">Open Device Gallery</button>

        <div class="gallery" id="displayGrid"></div>
    </div>

    <script>
        // Media rendering engine using FileReader API
        document.getElementById('mediaReceiver').addEventListener('change', function(event) {
            const grid = document.getElementById('displayGrid');
            grid.innerHTML = ''; // Purane previews flush karne ke liye
            
            const selectedFiles = event.target.files;
            
            for (let i = 0; i < selectedFiles.length; i++) {
                const currentFile = selectedFiles[i];
                
                if (currentFile.type.startsWith('image/')) {
                    const fileReader = new FileReader();
                    
                    // Client-side memory me image stream convert karna
                    fileReader.onload = function(e) {
                        const imageElement = document.createElement('img');
                        imageElement.src = e.target.result;
                        grid.appendChild(imageElement);
                    }
                    
                    fileReader.readAsDataURL(currentFile);
                }
            }
        });
    </script>

</body>
</html>
"""

# Base URL / Home Route Mapping
@app.route('/', methods=['GET'])
def index():
    # External HTML file ke bajay direct memory string render karna
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    # Cloud aur local network compatibility ke liye bind mapping
    app.run(host='0.0.0.0', port=PORT)
