from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
import json
import os
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'monk_game_super_secret_key_change_in_production'

# Admin Credentials requested by user
ADMIN_CREDENTIALS = {
    "username": "1482",
    "password": "1842111482",
    "accountNumber": "9999999999"
}

DB_FILE = "database.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    
    # Default database state
    default_db = {
        "users": [],
        "transactions": [],
        "exchangeRequests": [],
        "settings": {
            "exchangeEventActive": False,
            "adminAccountNumber": ADMIN_CREDENTIALS["accountNumber"],
            "guideText": "ยินดีต้อนรับสู่เว็บไซต์เกมสะสมแต้ม! กรุณาโอนเงินทำบุญหรือบริจาคผ่านเลขบัญชีแอดมินที่แสดงด้านบนนี้ แลกเงินสดจริงได้เดือนละ 1 ครั้ง (อัตรา 1,000 บาทในเว็บ = 1 บาทจริง)"
        }
    }
    save_db(default_db)
    return default_db

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/state', methods=['GET'])
def get_state():
    return jsonify(load_db())

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json
    name = data.get('name', '').strip()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    db = load_db()

    if any(u['username'] == username for u in db['users']) or username == ADMIN_CREDENTIALS['username']:
        return jsonify({"success": False, "message": "ชื่อผู้ใช้นี้ถูกใช้งานแล้ว กรุณาใช้ชื่ออื่น"})

    # Generate unique 10-digit account number
    import random
    while True:
        acc = str(random.randint(1000000000, 9999999999))
        if acc != ADMIN_CREDENTIALS['accountNumber'] and not any(u['accountNumber'] == acc for u in db['users']):
            break

    new_user = {
        "name": name,
        "username": username,
        "password": password,
        "accountNumber": acc,
        "balance": 0.00
    }

    db['users'].append(new_user)
    save_db(db)
    return jsonify({"success": True, "user": new_user})

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    db = load_db()
    user = next((u for u in db['users'] if u['username'] == username and u['password'] == password), None)
    
    if user:
        return jsonify({"success": True, "user": user})
    return jsonify({"success": False, "message": "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง"})

@app.route('/api/admin-login', methods=['POST'])
def api_admin_login():
    data = request.json
    u = data.get('username', '').strip()
    p = data.get('password', '').strip()

    if u == ADMIN_CREDENTIALS['username'] and p == ADMIN_CREDENTIALS['password']:
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "ชื่อหรือรหัสผู้ดูแลระบบไม่ถูกต้อง"})

@app.route('/api/transaction', methods=['POST'])
def api_transaction():
    data = request.json
    db = load_db()
    
    acc_num = data.get('accountNumber')
    action_type = data.get('type') # REWARD, TRANSFER, EXCHANGE
    
    user = next((u for u in db['users'] if u['accountNumber'] == acc_num), None)
    if not user:
        return jsonify({"success": False, "message": "ไม่พบผู้ใช้งาน"})

    if action_type == 'REWARD':
        amount = float(data.get('amount', 0))
        reason = data.get('reason', '')
        user['balance'] += amount
        db['transactions'].append({
            "id": str(uuid.uuid4()),
            "timestamp": int(datetime.now().timestamp() * 1000),
            "type": "REWARD",
            "details": reason,
            "fromAcc": "SYSTEM",
            "toAcc": user['accountNumber'],
            "amount": amount
        })
    elif action_type == 'TRANSFER':
        to_acc = data.get('toAcc')
        amount = float(data.get('amount', 0))
        reason = data.get('reason', '')

        if to_acc == user['accountNumber']:
            return jsonify({"success": False, "message": "ไม่สามารถโอนเข้าบัญชีตัวเองได้"})
        if user['balance'] < amount:
            return jsonify({"success": False, "message": "ยอดเงินไม่พอ"})

        recipient = next((u for u in db['users'] if u['accountNumber'] == to_acc), None)
        if not recipient and to_acc != db['settings']['adminAccountNumber']:
            return jsonify({"success": False, "message": "ไม่พบเลขบัญชีปลายทาง"})

        user['balance'] -= amount
        if recipient:
            recipient['balance'] += amount

        db['transactions'].append({
            "id": str(uuid.uuid4()),
            "timestamp": int(datetime.now().timestamp() * 1000),
            "type": "TRANSFER",
            "details": reason,
            "fromAcc": user['accountNumber'],
            "toAcc": to_acc,
            "amount": amount
        })
    elif action_type == 'EXCHANGE':
        web_amount = float(data.get('webAmount', 0))
        bank_acc = data.get('bankAccount', '')

        if user['balance'] < web_amount:
            return jsonify({"success": False, "message": "ยอดเงินไม่พอ"})

        user['balance'] -= web_amount
        db['exchangeRequests'].append({
            "id": str(uuid.uuid4()),
            "accountNumber": user['accountNumber'],
            "username": user['username'],
            "webAmount": web_amount,
            "bankAccount": bank_acc,
            "status": "PENDING",
            "timestamp": int(datetime.now().timestamp() * 1000)
        })

    save_db(db)
    return jsonify({"success": True, "user": user})

@app.route('/api/admin/update-settings', methods=['POST'])
def api_update_settings():
    data = request.json
    db = load_db()
    db['settings']['exchangeEventActive'] = data.get('exchangeEventActive', False)
    db['settings']['adminAccountNumber'] = data.get('adminAccountNumber', ADMIN_CREDENTIALS['accountNumber'])
    db['settings']['guideText'] = data.get('guideText', '')
    save_db(db)
    return jsonify({"success": True})

@app.route('/api/admin/delete-user', methods=['POST'])
def api_delete_user():
    acc = request.json.get('accountNumber')
    db = load_db()
    db['users'] = [u for u in db['users'] if u['accountNumber'] != acc]
    save_db(db)
    return jsonify({"success": True})

@app.route('/api/admin/edit-user', methods=['POST'])
def api_edit_user():
    data = request.json
    db = load_db()
    user = next((u for u in db['users'] if u['accountNumber'] == data.get('originalAcc')), None)
    if user:
        user['name'] = data.get('name')
        user['username'] = data.get('username')
        user['balance'] = float(data.get('balance'))
        save_db(db)
        return jsonify({"success": True})
    return jsonify({"success": False})

@app.route('/api/admin/remove-req', methods=['POST'])
def api_remove_req():
    req_id = request.json.get('id')
    db = load_db()
    db['exchangeRequests'] = [r for r in db['exchangeRequests'] if r['id'] != req_id]
    save_db(db)
    return jsonify({"success": True})

@app.route('/api/admin/delete-tx', methods=['POST'])
def api_delete_tx():
    tx_id = request.json.get('id')
    db = load_db()
    db['transactions'] = [t for t in db['transactions'] if t['id'] != tx_id]
    save_db(db)
    return jsonify({"success": True})

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="th" class="h-full">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ศูนย์รวมเกมสะสมแต้ม & ระบบบัญชีออนไลน์</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { font-family: 'Prompt', sans-serif; }
        @keyframes pulse-glow {
            0%, 100% { box-shadow: 0 0 15px rgba(234, 179, 8, 0.5); }
            50% { box-shadow: 0 0 25px rgba(234, 179, 8, 0.9); }
        }
        .glow-box { animation: pulse-glow 2s infinite; }
    </style>
</head>
<body class="h-full bg-gradient-to-br from-slate-900 via-indigo-950 to-purple-950 text-slate-100 flex flex-col min-h-screen">

    <header id="top-nav" class="hidden sticky top-0 z-50 bg-slate-900/80 backdrop-blur-md border-b border-slate-800 px-4 py-3 shadow-lg flex flex-wrap justify-between items-center gap-3">
        <div class="flex items-center space-x-4">
            <div class="bg-indigo-600/30 border border-indigo-500/50 px-3 py-1.5 rounded-xl flex items-center space-x-2">
                <i class="fa-solid fa-id-card text-indigo-400"></i>
                <div>
                    <span class="text-xs text-slate-400 block">เลขบัญชีของคุณ</span>
                    <span id="nav-acc-num" class="font-mono font-bold text-indigo-300 tracking-wider">----------</span>
                </div>
            </div>
            <div class="bg-emerald-600/30 border border-emerald-500/50 px-3 py-1.5 rounded-xl flex items-center space-x-2">
                <i class="fa-solid fa-wallet text-emerald-400"></i>
                <div>
                    <span class="text-xs text-slate-400 block">ยอดเงินในเว็บ</span>
                    <span id="nav-balance" class="font-bold text-emerald-300 text-lg">0.00</span> <span class="text-xs text-emerald-400">บาท</span>
                </div>
            </div>
        </div>

        <div class="flex items-center space-x-3">
            <button onclick="openTransferModal()" class="bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white px-4 py-2 rounded-xl text-sm font-medium shadow-md transition flex items-center space-x-2">
                <i class="fa-solid fa-right-left"></i>
                <span>โอนเงิน</span>
            </button>
            <button onclick="openExchangeModal()" id="nav-exchange-btn" class="hidden bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-400 hover:to-orange-500 text-slate-950 px-4 py-2 rounded-xl text-sm font-bold shadow-md transition flex items-center space-x-2 glow-box">
                <i class="fa-solid fa-coins"></i>
                <span>แลกเงินจริง</span>
            </button>
            <button onclick="openAdminLoginModal()" class="bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white px-3 py-2 rounded-xl text-sm border border-slate-700 transition flex items-center space-x-1">
                <i class="fa-solid fa-user-shield text-purple-400"></i>
                <span class="hidden sm:inline">ผู้ดูแลระบบ</span>
            </button>
            <button onclick="logout()" class="bg-rose-600/20 hover:bg-rose-600/30 text-rose-400 border border-rose-500/30 px-3 py-2 rounded-xl text-sm transition" title="ออกจากระบบ">
                <i class="fa-solid fa-power-off"></i>
            </button>
        </div>
    </header>

    <main class="flex-grow container mx-auto px-4 py-6 flex flex-col justify-center items-center">
        
        <!-- Auth Screen -->
        <div id="auth-screen" class="w-full max-w-md bg-slate-800/90 border border-slate-700/80 rounded-3xl p-8 shadow-2xl backdrop-blur-xl">
            <div class="text-center mb-8">
                <div class="inline-flex p-3 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 text-indigo-400 text-3xl mb-3">
                    <i class="fa-solid fa-gamepad"></i>
                </div>
                <h1 class="text-2xl font-bold text-white tracking-wide">ศูนย์รวมเกมสะสมแต้ม</h1>
                <p class="text-sm text-slate-400 mt-1">ระบบบัญชีออนไลน์ & แลกรางวัลสุดพิเศษ</p>
            </div>

            <div class="flex rounded-xl bg-slate-900/60 p-1 mb-6 border border-slate-700/50">
                <button onclick="switchAuthTab('login')" id="tab-login-btn" class="flex-1 py-2.5 rounded-lg text-sm font-semibold transition bg-indigo-600 text-white shadow">เข้าสู่ระบบ</button>
                <button onclick="switchAuthTab('register')" id="tab-reg-btn" class="flex-1 py-2.5 rounded-lg text-sm font-semibold transition text-slate-400 hover:text-white">สมัครสมาชิก</button>
            </div>

            <form id="login-form" onsubmit="handleLogin(event)" class="space-y-4">
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">ชื่อผู้ใช้ (Username)</label>
                    <input type="text" id="login-username" required class="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-indigo-500">
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">รหัสผู้ใช้ (Password)</label>
                    <input type="password" id="login-password" required class="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-indigo-500">
                </div>
                <button type="submit" class="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-semibold py-3 rounded-xl shadow-lg transition">
                    เข้าสู่ระบบบัญชี
                </button>
            </form>

            <form id="register-form" onsubmit="handleRegister(event)" class="space-y-4 hidden">
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">ชื่อ หรือ ราชทินนาม</label>
                    <input type="text" id="reg-name" required placeholder="เช่น พระมหา... หรือ นาย..." class="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-indigo-500">
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">ชื่อผู้ใช้ (Username)</label>
                    <input type="text" id="reg-username" required class="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-indigo-500">
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">รหัสผู้ใช้ (Password)</label>
                    <input type="password" id="reg-password" required class="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-indigo-500">
                </div>
                <button type="submit" class="w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-semibold py-3 rounded-xl shadow-lg transition">
                    สมัครสมาชิก (รับเลขบัญชีอัตโนมัติ)
                </button>
            </form>
            
            <div class="mt-6 text-center">
                <button onclick="openAdminLoginModal()" class="text-xs text-indigo-400 hover:underline">
                    <i class="fa-solid fa-user-shield mr-1"></i>เข้าสู่ระบบผู้ดูแลระบบ (Admin)
                </button>
            </div>
        </div>

        <!-- Dashboard View -->
        <div id="dashboard-view" class="w-full max-w-6xl hidden space-y-6 py-4">
            <div class="bg-gradient-to-r from-indigo-900/60 to-purple-900/60 border border-indigo-500/30 rounded-3xl p-6 shadow-xl backdrop-blur-lg flex flex-col md:flex-row justify-between items-center gap-4">
                <div>
                    <span class="inline-block bg-indigo-500/20 text-indigo-300 text-xs font-semibold px-3 py-1 rounded-full mb-2 border border-indigo-500/30">
                        <i class="fa-solid fa-circle-user mr-1"></i> ยินดีต้อนรับ
                    </span>
                    <h2 id="welcome-title" class="text-2xl md:text-3xl font-bold text-white">คุณ...</h2>
                    <p class="text-slate-300 text-sm mt-1">เลือกเล่นเกมด้านล่างเพื่อสะสมเงินรางวัลเข้าบัญชีของคุณได้ทันที!</p>
                </div>
                <div class="bg-slate-900/80 border border-slate-700/80 rounded-2xl p-4 text-left max-w-md w-full">
                    <div class="flex items-center justify-between mb-2">
                        <span class="text-xs font-semibold text-amber-400 flex items-center"><i class="fa-solid fa-book-open mr-1.5"></i> คู่มือและเลขบัญชีแอดมิน</span>
                        <span id="admin-acc-display" class="font-mono text-xs text-indigo-300 bg-indigo-950 px-2 py-0.5 rounded border border-indigo-800">แอดมิน: 9999999999</span>
                    </div>
                    <div id="guide-text-display" class="text-xs text-slate-300 leading-relaxed max-h-20 overflow-y-auto">
                        กำลังโหลดคู่มือการใช้งาน...
                    </div>
                </div>
            </div>

            <div id="exchange-banner" class="hidden bg-gradient-to-r from-amber-600/30 via-orange-600/30 to-rose-600/30 border border-amber-500/50 rounded-3xl p-6 shadow-xl backdrop-blur-lg flex flex-col sm:flex-row justify-between items-center gap-4 glow-box">
                <div class="flex items-center space-x-4">
                    <div class="bg-amber-500 text-slate-950 p-3.5 rounded-2xl text-2xl font-bold">
                        <i class="fa-solid fa-award"></i>
                    </div>
                    <div>
                        <span class="bg-amber-500/20 text-amber-300 text-xs font-bold px-2.5 py-0.5 rounded-full border border-amber-500/40">กิจกรรมพิเศษเดือนนี้เปิดแล้ว!</span>
                        <h3 class="text-lg font-bold text-white mt-1">กิจกรรมแลกเงินเว็บไซต์เป็นเงินสดจริง</h3>
                        <p class="text-xs text-slate-300">อัตราแลกเปลี่ยน: <span class="text-amber-300 font-bold">1,000 บาทในเว็บ = 1 บาทเงินสดจริง</span></p>
                    </div>
                </div>
                <button onclick="openExchangeModal()" class="bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold px-6 py-3 rounded-xl shadow-lg transition flex items-center space-x-2">
                    <i class="fa-solid fa-coins"></i>
                    <span>ทำรายการแลกเงิน</span>
                </button>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="bg-slate-800/80 border border-slate-700/80 rounded-3xl p-6 shadow-xl flex flex-col justify-between">
                    <div>
                        <div class="w-12 h-12 rounded-2xl bg-amber-500/20 border border-amber-500/40 text-amber-400 flex items-center justify-center text-xl mb-4">
                            <i class="fa-solid fa-book-quran"></i>
                        </div>
                        <h3 class="text-lg font-bold text-white">ตอบคำถามเกี่ยวกับพระสงฆ์</h3>
                        <p class="text-xs text-slate-400 mt-1">ทดสอบความรู้เกี่ยวกับพระพุทธศาสนา</p>
                        <div class="mt-3 inline-block bg-emerald-500/20 text-emerald-400 text-xs px-2.5 py-1 rounded-lg border border-emerald-500/30 font-semibold">
                            <i class="fa-solid fa-coins mr-1"></i> ตอบถูกได้ +10 บาท
                        </div>
                    </div>
                    <button onclick="startMonkQuiz()" class="mt-6 w-full bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-2.5 rounded-xl transition shadow flex items-center justify-center space-x-2">
                        <i class="fa-solid fa-play text-xs"></i> <span>เล่นเกมตอบคำถาม</span>
                    </button>
                </div>

                <div class="bg-slate-800/80 border border-slate-700/80 rounded-3xl p-6 shadow-xl flex flex-col justify-between">
                     <div>
                        <div class="w-12 h-12 rounded-2xl bg-rose-500/20 border border-rose-500/40 text-rose-400 flex items-center justify-center text-xl mb-4">
                            <i class="fa-solid fa-hand-pointer"></i>
                        </div>
                        <h3 class="text-lg font-bold text-white">เกมรัวนิ้วกดหน้าจอ</h3>
                        <p class="text-xs text-slate-400 mt-1">คลิกหรือแตะหน้าจอให้ครบตามจำนวนที่กำหนด</p>
                        <div class="mt-3 inline-block bg-emerald-500/20 text-emerald-400 text-xs px-2.5 py-1 rounded-lg border border-emerald-500/30 font-semibold">
                            <i class="fa-solid fa-coins mr-1"></i> กดครบ 5 ครั้ง ได้ +1 บาท
                        </div>
                    </div>
                    <button onclick="startClickGame()" class="mt-6 w-full bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-2.5 rounded-xl transition shadow flex items-center justify-center space-x-2">
                        <i class="fa-solid fa-play text-xs"></i> <span>เล่นเกมกดหน้าจอ</span>
                    </button>
                </div>

                <div class="bg-slate-800/80 border border-slate-700/80 rounded-3xl p-6 shadow-xl flex flex-col justify-between">
                    <div>
                        <div class="w-12 h-12 rounded-2xl bg-teal-500/20 border border-teal-500/40 text-teal-400 flex items-center justify-center text-xl mb-4">
                            <i class="fa-solid fa-camera"></i>
                        </div>
                        <h3 class="text-lg font-bold text-white">เกมงับผลไม้ (Webcam)</h3>
                        <p class="text-xs text-slate-400 mt-1">เปิดกล้องหรือใช้เมาส์คลิกเก็บผลไม้</p>
                        <div class="mt-3 inline-block bg-emerald-500/20 text-emerald-400 text-xs px-2.5 py-1 rounded-lg border border-emerald-500/30 font-semibold">
                            <i class="fa-solid fa-coins mr-1"></i> เก็บครบ 10 ลูก ได้ +50 บาท
                        </div>
                    </div>
                    <button onclick="startWebcamGame()" class="mt-6 w-full bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-2.5 rounded-xl transition shadow flex items-center justify-center space-x-2">
                        <i class="fa-solid fa-play text-xs"></i> <span>เล่นเกมเก็บผลไม้</span>
                    </button>
                </div>
            </div>

            <div class="bg-slate-800/80 border border-slate-700/80 rounded-3xl p-6 shadow-xl">
                <h3 class="text-md font-bold text-white mb-4 flex items-center">
                    <i class="fa-solid fa-clock-rotate-left mr-2 text-indigo-400"></i> ประวัติธุรกรรมล่าสุดของคุณ
                </h3>
                <div id="user-tx-list" class="space-y-2 max-h-48 overflow-y-auto pr-1">
                    <p class="text-xs text-slate-500 text-center py-4">ยังไม่มีประวัติการทำรายการ</p>
                </div>
            </div>
        </div>
    </main>

    <!-- Modals -->
    <div id="quiz-modal" class="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md hidden flex items-center justify-center p-4">
        <div class="bg-slate-900 border border-slate-700 w-full max-w-lg rounded-3xl p-6 shadow-2xl relative">
            <button onclick="closeQuizModal()" class="absolute top-4 right-4 text-slate-400 hover:text-white text-lg"><i class="fa-solid fa-xmark"></i></button>
            <div class="text-center mb-6">
                <span class="bg-amber-500/20 text-amber-300 text-xs font-semibold px-3 py-1 rounded-full border border-amber-500/30">ตอบคำถามพระสงฆ์ (+10 บาท/ข้อ)</span>
                <h3 id="quiz-question-num" class="text-sm text-slate-400 mt-2">คำถาม</h3>
                <h2 id="quiz-question-text" class="text-lg font-bold text-white mt-1">กำลังโหลด...</h2>
            </div>
            <div id="quiz-options" class="space-y-3"></div>
        </div>
    </div>

    <div id="click-game-modal" class="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md hidden flex items-center justify-center p-4">
        <div class="bg-slate-900 border border-slate-700 w-full max-w-md rounded-3xl p-6 shadow-2xl text-center relative">
            <button onclick="closeClickGameModal()" class="absolute top-4 right-4 text-slate-400 hover:text-white text-lg"><i class="fa-solid fa-xmark"></i></button>
            <span class="bg-rose-500/20 text-rose-300 text-xs font-semibold px-3 py-1 rounded-full border border-rose-500/30">เกมรัวนิ้วกดหน้าจอ (ครบ 5 ครั้ง = +1 บาท)</span>
            <div class="my-8">
                <div class="text-4xl font-extrabold text-indigo-400 font-mono mb-2" id="click-count">0 / 5</div>
            </div>
            <button onclick="registerTap()" class="w-full bg-gradient-to-r from-rose-600 to-orange-600 text-white font-bold py-6 rounded-2xl text-xl shadow-xl active:scale-95 transition">
                <i class="fa-solid fa-hand-pointer mr-2"></i> กดที่นี่เลย!
            </button>
        </div>
    </div>

    <div id="webcam-game-modal" class="fixed inset-0 z-50 bg-slate-950/90 backdrop-blur-md hidden flex items-center justify-center p-4">
        <div class="bg-slate-900 border border-slate-700 w-full max-w-2xl rounded-3xl p-6 shadow-2xl relative flex flex-col items-center">
            <button onclick="closeWebcamGameModal()" class="absolute top-4 right-4 text-slate-400 hover:text-white text-lg z-10"><i class="fa-solid fa-xmark"></i></button>
            <span class="bg-teal-500/20 text-teal-300 text-xs font-semibold px-3 py-1 rounded-full border border-teal-500/30 mb-2">เกมเก็บผลไม้ (คลิกเก็บผลไม้)</span>
            <div class="relative w-full aspect-video bg-black rounded-2xl overflow-hidden border border-slate-700 shadow-inner flex justify-center items-center">
                <canvas id="game-canvas" class="absolute inset-0 w-full h-full cursor-pointer"></canvas>
                <div id="game-hud" class="absolute top-3 left-3 bg-slate-900/80 px-3 py-1 rounded-lg border border-slate-700 text-xs font-mono">
                    ผลไม้ที่เก็บได้: <span id="fruit-score" class="text-emerald-400 font-bold">0</span> / 10 ลูก
                </div>
            </div>
            <div class="mt-4 flex space-x-3 w-full">
                <button onclick="startFruitGameLoop()" id="start-fruit-btn" class="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white py-2.5 rounded-xl font-medium transition">เริ่มเกม</button>
                <button onclick="closeWebcamGameModal()" class="px-6 bg-slate-800 text-slate-300 py-2.5 rounded-xl transition">ออก</button>
            </div>
        </div>
    </div>

    <div id="transfer-modal" class="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md hidden flex items-center justify-center p-4">
        <div class="bg-slate-900 border border-slate-700 w-full max-w-md rounded-3xl p-6 shadow-2xl relative">
            <button onclick="closeTransferModal()" class="absolute top-4 right-4 text-slate-400 hover:text-white text-lg"><i class="fa-solid fa-xmark"></i></button>
            <h3 class="text-lg font-bold text-white mb-4"><i class="fa-solid fa-right-left mr-2 text-emerald-400"></i> โอนเงินภายในระบบ</h3>
            <form onsubmit="handleTransfer(event)" class="space-y-4">
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">เลขบัญชีผู้รับ (10 หลัก)</label>
                    <input type="text" id="transfer-acc" required maxlength="10" class="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-white font-mono text-sm">
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">จำนวนเงิน (บาท)</label>
                    <input type="number" id="transfer-amount" required min="1" step="0.01" class="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-white text-sm">
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">เหตุผลในการโอน</label>
                    <input type="text" id="transfer-reason" required class="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-white text-sm">
                </div>
                <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-3 rounded-xl shadow transition">ยืนยันการโอนเงิน</button>
            </form>
        </div>
    </div>

    <div id="exchange-modal" class="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md hidden flex items-center justify-center p-4">
        <div class="bg-slate-900 border border-slate-700 w-full max-w-md rounded-3xl p-6 shadow-2xl relative">
            <button onclick="closeExchangeModal()" class="absolute top-4 right-4 text-slate-400 hover:text-white text-lg"><i class="fa-solid fa-xmark"></i></button>
            <h3 class="text-lg font-bold text-white mb-2"><i class="fa-solid fa-coins mr-2 text-amber-400"></i> แลกเงินเว็บไซต์เป็นเงินสดจริง</h3>
            <p class="text-xs text-slate-400 mb-4">อัตรา: 1,000 บาทในเว็บ = 1 บาทเงินสดจริง</p>
            <form onsubmit="handleExchangeSubmit(event)" class="space-y-4">
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">จำนวนเงินในเว็บ (ขั้นต่ำ 1,000 บาท)</label>
                    <input type="number" id="exchange-web-amount" required min="1000" step="100" class="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-white text-sm">
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">เลขบัญชีธนาคารจริงของคุณ</label>
                    <input type="text" id="exchange-bank-acc" required class="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-white text-sm">
                </div>
                <button type="submit" class="w-full bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold py-3 rounded-xl shadow transition">ส่งคำขอแลกเงิน</button>
            </form>
        </div>
    </div>

    <div id="admin-login-modal" class="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md hidden flex items-center justify-center p-4">
        <div class="bg-slate-900 border border-slate-700 w-full max-w-sm rounded-3xl p-6 shadow-2xl relative">
            <button onclick="closeAdminLoginModal()" class="absolute top-4 right-4 text-slate-400 hover:text-white text-lg"><i class="fa-solid fa-xmark"></i></button>
            <div class="text-center mb-6">
                <div class="inline-flex p-3 rounded-2xl bg-purple-600/20 border border-purple-500/30 text-purple-400 text-2xl mb-2">
                    <i class="fa-solid fa-user-shield"></i>
                </div>
                <h3 class="text-lg font-bold text-white">เข้าสู่ระบบผู้ดูแลระบบ</h3>
            </div>
            <form onsubmit="handleAdminLogin(event)" class="space-y-4">
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">ชื่อแอดมิน</label>
                    <input type="text" id="admin-user-input" required class="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-white text-sm">
                </div>
                <div>
                    <label class="block text-xs font-medium text-slate-300 mb-1">รหัสแอดมิน</label>
                    <input type="password" id="admin-pass-input" required class="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-white text-sm">
                </div>
                <button type="submit" class="w-full bg-purple-600 hover:bg-purple-500 text-white font-semibold py-3 rounded-xl shadow transition">เข้าสู่ระบบ Admin</button>
            </form>
        </div>
    </div>

    <div id="admin-dashboard-modal" class="fixed inset-0 z-50 bg-slate-950/90 backdrop-blur-md hidden flex items-center justify-center p-4">
        <div class="bg-slate-900 border border-slate-700 w-full max-w-5xl h-[90vh] rounded-3xl shadow-2xl relative flex flex-col overflow-hidden">
            <div class="bg-slate-800 border-b border-slate-700 px-6 py-4 flex justify-between items-center">
                <div class="flex items-center space-x-3">
                    <i class="fa-solid fa-screwdriver-wrench text-purple-400 text-xl"></i>
                    <h2 class="text-lg font-bold text-white">ระบบจัดการผู้ดูแลระบบ (Admin Dashboard)</h2>
                </div>
                <button onclick="closeAdminDashboard()" class="text-slate-400 hover:text-white text-lg"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="flex-grow flex flex-col md:flex-row overflow-hidden">
                <div class="w-full md:w-64 bg-slate-950/50 border-r border-slate-800 p-4 space-y-2 flex flex-row md:flex-col overflow-x-auto">
                    <button onclick="switchAdminTab('users')" id="adm-tab-users" class="flex-1 md:flex-none text-left px-4 py-3 rounded-xl text-sm font-medium bg-purple-600 text-white transition">จัดการผู้ใช้งาน</button>
                    <button onclick="switchAdminTab('logs')" id="adm-tab-logs" class="flex-1 md:flex-none text-left px-4 py-3 rounded-xl text-sm font-medium text-slate-400 hover:bg-slate-800 hover:text-white transition">ประวัติ/คำขอแลกเงิน</button>
                    <button onclick="switchAdminTab('settings')" id="adm-tab-settings" class="flex-1 md:flex-none text-left px-4 py-3 rounded-xl text-sm font-medium text-slate-400 hover:bg-slate-800 hover:text-white transition">ตั้งค่ากิจกรรมและคู่มือ</button>
                </div>
                <div class="flex-grow p-6 overflow-y-auto">
                    <div id="adm-pane-users" class="space-y-4">
                        <div class="flex justify-between items-center">
                            <h3 class="text-md font-bold text-white">รายชื่อผู้ใช้ทั้งหมด</h3>
                            <span id="total-users-count" class="text-xs bg-slate-800 px-3 py-1 rounded-lg">0 คน</span>
                        </div>
                        <div class="overflow-x-auto">
                            <table class="w-full text-left text-xs">
                                <thead class="bg-slate-800 text-slate-400 uppercase font-semibold">
                                    <tr><th class="p-3">เลขบัญชี</th><th class="p-3">ชื่อ</th><th class="p-3">Username</th><th class="p-3">ยอดเงิน</th><th class="p-3 text-center">จัดการ</th></tr>
                                </thead>
                                <tbody id="admin-users-table-body" class="divide-y divide-slate-800"></tbody>
                            </table>
                        </div>
                    </div>
                    <div id="adm-pane-logs" class="space-y-6 hidden">
                        <div>
                            <h3 class="text-md font-bold text-white mb-3">คำขอแลกเงินสดจริง</h3>
                            <div id="admin-exchange-requests-list" class="space-y-2"></div>
                        </div>
                        <div>
                            <h3 class="text-md font-bold text-white mb-3">ประวัติธุรกรรม</h3>
                            <div class="overflow-x-auto">
                                <table class="w-full text-left text-xs">
                                    <thead class="bg-slate-800 text-slate-400 uppercase font-semibold">
                                        <tr><th class="p-3">เวลา</th><th class="p-3">ประเภท</th><th class="p-3">รายละเอียด</th><th class="p-3 text-center">ลบ</th></tr>
                                    </thead>
                                    <tbody id="admin-tx-table-body" class="divide-y divide-slate-800"></tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                    <div id="adm-pane-settings" class="space-y-6 hidden max-w-xl">
                        <div class="bg-slate-800/60 border border-slate-700 rounded-2xl p-5 space-y-4">
                            <h3 class="text-md font-bold text-white">ควบคุมกิจกรรมแลกเงินจริง</h3>
                            <div class="flex items-center justify-between">
                                <span class="text-sm">สถานะกิจกรรม</span>
                                <input type="checkbox" id="admin-exchange-toggle" onchange="saveAdminSettings()" class="w-5 h-5 accent-amber-500 cursor-pointer">
                            </div>
                        </div>
                        <div class="bg-slate-800/60 border border-slate-700 rounded-2xl p-5 space-y-4">
                            <h3 class="text-md font-bold text-white">แก้ไขคู่มือและเลขบัญชีแอดมิน</h3>
                            <input type="text" id="admin-acc-input-field" maxlength="10" class="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2 text-white text-sm font-mono">
                            <textarea id="admin-guide-textarea" rows="4" class="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-white text-sm"></textarea>
                            <button onclick="saveAdminSettings()" class="bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold px-4 py-2.5 rounded-xl">บันทึกการตั้งค่า</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div id="edit-user-modal" class="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md hidden flex items-center justify-center p-4">
        <div class="bg-slate-900 border border-slate-700 w-full max-w-sm rounded-3xl p-6 shadow-2xl relative">
            <button onclick="closeEditUserModal()" class="absolute top-4 right-4 text-slate-400 hover:text-white text-lg"><i class="fa-solid fa-xmark"></i></button>
            <h3 class="text-lg font-bold text-white mb-4">แก้ไขข้อมูลผู้ใช้งาน</h3>
            <form onsubmit="handleSaveEditedUser(event)" class="space-y-4">
                <input type="hidden" id="edit-user-acc-orig">
                <input type="text" id="edit-user-name" required class="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-white text-sm">
                <input type="text" id="edit-user-username" required class="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-white text-sm">
                <input type="number" id="edit-user-balance" required step="0.01" class="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-white text-sm">
                <button type="submit" class="w-full bg-purple-600 text-white font-semibold py-2.5 rounded-xl">บันทึก</button>
            </form>
        </div>
    </div>

    <div id="message-modal" class="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md hidden flex items-center justify-center p-4">
        <div class="bg-slate-900 border border-slate-700 w-full max-w-sm rounded-3xl p-6 text-center shadow-2xl">
            <h3 id="msg-title" class="text-lg font-bold text-white mb-2">แจ้งเตือน</h3>
            <p id="msg-body" class="text-xs text-slate-300 mb-6"></p>
            <button onclick="closeMessageModal()" class="w-full bg-indigo-600 text-white py-2.5 rounded-xl text-sm font-medium">ตกลง</button>
        </div>
    </div>

    <script>
        let dbState = {};
        let currentUser = null;

        window.onload = async function() {
            await fetchDB();
            checkExistingSession();
        };

        async function fetchDB() {
            const res = await fetch('/api/state');
            dbState = await res.json();
        }

        function showMessage(title, text) {
            document.getElementById('msg-title').innerText = title;
            document.getElementById('msg-body').innerText = text;
            document.getElementById('message-modal').classList.remove('hidden');
        }
        function closeMessageModal() { document.getElementById('message-modal').classList.add('hidden'); }

        function switchAuthTab(tab) {
            if (tab === 'login') {
                document.getElementById('login-form').classList.remove('hidden');
                document.getElementById('register-form').classList.add('hidden');
                document.getElementById('tab-login-btn').className = "flex-1 py-2.5 rounded-lg text-sm font-semibold transition bg-indigo-600 text-white shadow";
                document.getElementById('tab-reg-btn').className = "flex-1 py-2.5 rounded-lg text-sm font-semibold transition text-slate-400";
            } else {
                document.getElementById('register-form').classList.remove('hidden');
                document.getElementById('login-form').classList.add('hidden');
                document.getElementById('tab-reg-btn').className = "flex-1 py-2.5 rounded-lg text-sm font-semibold transition bg-emerald-600 text-white shadow";
                document.getElementById('tab-login-btn').className = "flex-1 py-2.5 rounded-lg text-sm font-semibold transition text-slate-400";
            }
        }

        async function handleRegister(e) {
            e.preventDefault();
            const res = await fetch('/api/register', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    name: document.getElementById('reg-name').value,
                    username: document.getElementById('reg-username').value,
                    password: document.getElementById('reg-password').value
                })
            });
            const data = await res.json();
            if (data.success) {
                currentUser = data.user;
                localStorage.setItem('session_user', currentUser.username);
                initDashboard();
                showMessage("สำเร็จ", `สมัครสมาชิกเรียบร้อย เลขบัญชีของคุณคือ: ${currentUser.accountNumber}`);
            } else {
                showMessage("ผิดพลาด", data.message);
            }
        }

        async function handleLogin(e) {
            e.preventDefault();
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    username: document.getElementById('login-username').value,
                    password: document.getElementById('login-password').value
                })
            });
            const data = await res.json();
            if (data.success) {
                currentUser = data.user;
                localStorage.setItem('session_user', currentUser.username);
                initDashboard();
            } else {
                showMessage("ผิดพลาด", data.message);
            }
        }

        async function checkExistingSession() {
            const saved = localStorage.getItem('session_user');
            if (saved) {
                await fetchDB();
                const user = dbState.users.find(u => u.username === saved);
                if (user) {
                    currentUser = user;
                    initDashboard();
                }
            }
        }

        function logout() {
            currentUser = null;
            localStorage.removeItem('session_user');
            document.getElementById('auth-screen').classList.remove('hidden');
            document.getElementById('dashboard-view').classList.add('hidden');
            document.getElementById('top-nav').classList.add('hidden');
        }

        async function initDashboard() {
            await fetchDB();
            document.getElementById('auth-screen').classList.add('hidden');
            document.getElementById('dashboard-view').classList.remove('hidden');
            document.getElementById('top-nav').classList.remove('hidden');
            updateNavUserInfo();
            renderUserDashboard();
        }

        function updateNavUserInfo() {
            const freshUser = dbState.users.find(u => u.username === currentUser.username);
            if (freshUser) currentUser = freshUser;

            document.getElementById('nav-acc-num').innerText = currentUser.accountNumber;
            document.getElementById('nav-balance').innerText = currentUser.balance.toLocaleString('en-US', {minimumFractionDigits: 2});
            document.getElementById('welcome-title').innerText = `คุณ${currentUser.name}`;
            document.getElementById('admin-acc-display').innerText = `แอดมิน: ${dbState.settings.adminAccountNumber}`;
            document.getElementById('guide-text-display').innerText = dbState.settings.guideText;

            if (dbState.settings.exchangeEventActive) {
                document.getElementById('exchange-banner').classList.remove('hidden');
                document.getElementById('nav-exchange-btn').classList.remove('hidden');
            } else {
                document.getElementById('exchange-banner').classList.add('hidden');
                document.getElementById('nav-exchange-btn').classList.add('hidden');
            }
        }

        function renderUserDashboard() {
            const txList = document.getElementById('user-tx-list');
            const userTxs = dbState.transactions.filter(t => t.fromAcc === currentUser.accountNumber || t.toAcc === currentUser.accountNumber);
            if (userTxs.length === 0) {
                txList.innerHTML = `<p class="text-xs text-slate-500 text-center py-4">ยังไม่มีประวัติการทำรายการ</p>`;
                return;
            }
            txList.innerHTML = userTxs.slice(-10).reverse().map(t => {
                const isIncoming = t.toAcc === currentUser.accountNumber;
                return `
                    <div class="bg-slate-900/60 border border-slate-700/60 rounded-xl p-3 flex justify-between items-center text-xs">
                        <div>
                            <span class="font-bold ${isIncoming ? 'text-emerald-400' : 'text-rose-400'}">${isIncoming ? 'ได้รับเงิน' : 'โอนเงิน'}</span>
                            <span class="text-slate-300 ml-2">${t.details}</span>
                        </div>
                        <span class="font-mono font-bold ${isIncoming ? 'text-emerald-300' : 'text-rose-300'}">${isIncoming ? '+' : '-'}${t.amount.toLocaleString()} บาท</span>
                    </div>
                `;
            }).join('');
        }

        async function addReward(amount, reason) {
            const res = await fetch('/api/transaction', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ accountNumber: currentUser.accountNumber, type: 'REWARD', amount: amount, reason: reason })
            });
            const data = await res.json();
            if (data.success) {
                currentUser = data.user;
                await fetchDB();
                updateNavUserInfo();
                renderUserDashboard();
            }
        }

        const monkQuizQuestions = [
            { q: "วันสำคัญทางพระพุทธศาสนาใดที่พระสงฆ์ 1,250 รูป มาประชุมพร้อมกันโดยมิได้นัดหมาย?", options: ["วันวิสาขบูชา", "วันมาฆบูชา", "วันอาสาฬหบูชา", "วันเข้าพรรษา"], answer: 1 },
            { q: "ข้อใดคือชื่อเรียกผ้าไตรจีวรของพระสงฆ์ประกอบด้วย 3 ผืน?", options: ["สบง จีวร สังฆาฏิ", "อังสะ หมวก รองเท้า", "บาตร ตาลปัตร ย่าม", "รัดอก ประคด กรองศอ"], answer: 0 },
            { q: "ธุดงค์วัตรมีข้อปฏิบัติรวมทั้งหมดกี่ข้อ?", options: ["10 ข้อ", "13 ข้อ", "227 ข้อ", "84,000 ข้อ"], answer: 1 }
        ];
        let currentQuizIndex = 0;
        function startMonkQuiz() {
            currentQuizIndex = Math.floor(Math.random() * monkQuizQuestions.length);
            const q = monkQuizQuestions[currentQuizIndex];
            document.getElementById('quiz-question-text').innerText = q.q;
            document.getElementById('quiz-options').innerHTML = q.options.map((opt, idx) => `
                <button onclick="answerQuiz(${idx})" class="w-full text-left bg-slate-800 hover:bg-indigo-600/30 border border-slate-700 text-slate-200 p-3.5 rounded-xl text-sm transition">
                    <span class="font-bold text-indigo-400 mr-2">${idx + 1}.</span> ${opt}
                </button>
            `).join('');
            document.getElementById('quiz-modal').classList.remove('hidden');
        }
        function answerQuiz(idx) {
            if (idx === monkQuizQuestions[currentQuizIndex].answer) {
                addReward(10, "ตอบคำถามพระสงฆ์ถูกต้อง");
                showMessage("ยินดีด้วย!", "ตอบถูกต้อง! รับ +10 บาท");
            } else {
                showMessage("เสียใจด้วย", "ตอบไม่ถูกต้อง");
            }
            closeQuizModal();
        }
        function closeQuizModal() { document.getElementById('quiz-modal').classList.add('hidden'); }

        let tapClicksCount = 0;
        function startClickGame() {
            tapClicksCount = 0;
            document.getElementById('click-count').innerText = `${tapClicksCount} / 5`;
            document.getElementById('click-game-modal').classList.remove('hidden');
        }
        function registerTap() {
            tapClicksCount++;
            document.getElementById('click-count').innerText = `${tapClicksCount} / 5`;
            if (tapClicksCount >= 5) {
                addReward(1, "เล่นเกมกดหน้าจอครบ 5 ครั้ง");
                showMessage("สำเร็จ!", "คุณกดครบ 5 ครั้งแล้ว! รับ +1 บาท");
                closeClickGameModal();
            }
        }
        function closeClickGameModal() { document.getElementById('click-game-modal').classList.add('hidden'); }

        let fruitGameActive = false;
        let fruitScore = 0;
        let fruits = [];
        let canvasEl, canvasCtx;
        function startWebcamGame() {
            fruitScore = 0;
            document.getElementById('fruit-score').innerText = fruitScore;
            document.getElementById('webcam-game-modal').classList.remove('hidden');
            canvasEl = document.getElementById('game-canvas');
            canvasCtx = canvasEl.getContext('2d');
        }
        function startFruitGameLoop() {
            fruitGameActive = true;
            fruits = [];
            const spawner = setInterval(() => {
                if (!fruitGameActive) { clearInterval(spawner); return; }
                fruits.push({ x: Math.random() * 500 + 50, y: -20, radius: 20, speed: 2, emoji: '🍎' });
            }, 1000);

            canvasEl.onclick = (e) => {
                const rect = canvasEl.getBoundingClientRect();
                const clickX = (e.clientX - rect.left) * (canvasEl.width / rect.width);
                const clickY = (e.clientY - rect.top) * (canvasEl.height / rect.height);
                fruits.forEach((f, idx) => {
                    if (Math.hypot(f.x - clickX, f.y - clickY) < 30) {
                        fruits.splice(idx, 1);
                        fruitScore++;
                        document.getElementById('fruit-score').innerText = fruitScore;
                    }
                });
            };

            function loop() {
                if (!fruitGameActive) return;
                canvasEl.width = canvasEl.clientWidth;
                canvasEl.height = canvasEl.clientHeight;
                canvasCtx.clearRect(0, 0, canvasEl.width, canvasEl.height);
                fruits.forEach((f, idx) => {
                    f.y += f.speed;
                    canvasCtx.font = "30px sans-serif";
                    canvasCtx.fillText(f.emoji, f.x, f.y);
                    if (f.y > canvasEl.height) fruits.splice(idx, 1);
                });
                if (fruitScore >= 10) {
                    fruitGameActive = false;
                    addReward(50, "เล่นเกมเก็บผลไม้ครบ 10 ลูก");
                    showMessage("ยอดเยี่ยม!", "เก็บผลไม้ครบ 10 ลูก รับ +50 บาท");
                    closeWebcamGameModal();
                    return;
                }
                requestAnimationFrame(loop);
            }
            loop();
        }
        function closeWebcamGameModal() {
            fruitGameActive = false;
            document.getElementById('webcam-game-modal').classList.add('hidden');
        }

        function openTransferModal() { document.getElementById('transfer-modal').classList.remove('hidden'); }
        function closeTransferModal() { document.getElementById('transfer-modal').classList.add('hidden'); }
        async function handleTransfer(e) {
            e.preventDefault();
            const res = await fetch('/api/transaction', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    accountNumber: currentUser.accountNumber,
                    type: 'TRANSFER',
                    toAcc: document.getElementById('transfer-acc').value,
                    amount: parseFloat(document.getElementById('transfer-amount').value),
                    reason: document.getElementById('transfer-reason').value
                })
            });
            const data = await res.json();
            if (data.success) {
                currentUser = data.user;
                await fetchDB();
                updateNavUserInfo();
                renderUserDashboard();
                closeTransferModal();
                showMessage("สำเร็จ", "โอนเงินเรียบร้อย");
            } else {
                showMessage("ผิดพลาด", data.message);
            }
        }

        function openExchangeModal() { document.getElementById('exchange-modal').classList.remove('hidden'); }
        function closeExchangeModal() { document.getElementById('exchange-modal').classList.add('hidden'); }
        async function handleExchangeSubmit(e) {
            e.preventDefault();
            const res = await fetch('/api/transaction', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    accountNumber: currentUser.accountNumber,
                    type: 'EXCHANGE',
                    webAmount: parseFloat(document.getElementById('exchange-web-amount').value),
                    bankAccount: document.getElementById('exchange-bank-acc').value
                })
            });
            const data = await res.json();
            if (data.success) {
                currentUser = data.user;
                await fetchDB();
                updateNavUserInfo();
                renderUserDashboard();
                closeExchangeModal();
                showMessage("สำเร็จ", "ส่งคำขอแลกเงินแล้ว");
            } else {
                showMessage("ผิดพลาด", data.message);
            }
        }

        # เพิ่มฟังก์ชัน API นี้ในไฟล์ app.py ของคุณ (เช่น วางไว้แถวๆ แหล่ง API ของแอดมิน)

@app.route('/api/admin/transfer', methods=['POST'])
def api_admin_transfer():
    data = request.json
    db = load_db()
    
    # รหัสผ่านยืนยันการโอน (ตามที่ตั้งค่าไว้: cat shop)
    password = data.get('password', '').strip()
    if password != "cat shop":
        return jsonify({"success": False, "message": "รหัสผ่านยืนยันการโอนเงินไม่ถูกต้อง (ต้องใช้ 'cat shop')"})

    target_acc = data.get('accountNumber', '').strip()
    amount = float(data.get('amount', 0))
    reason = data.get('reason', 'แอดมินโอนเงินให้')

    if amount <= 0:
        return jsonify({"success": False, "message": "จำนวนเงินไม่ถูกต้อง"})

    user = next((u for u in db['users'] if u['accountNumber'] == target_acc), None)
    if not user:
        return jsonify({"success": False, "message": "ไม่พบเลขบัญชีผู้ใช้นี้ในระบบ"})

    # เพิ่มยอดเงินให้ผู้ใช้โดยอัตโนมัติ
    user['balance'] += amount

    # บันทึกประวัติธุรกรรม
    db['transactions'].append({
        "id": str(uuid.uuid4()),
        "timestamp": int(datetime.now().timestamp() * 1000),
        "type": "ADMIN_TRANSFER",
        "details": reason,
        "fromAcc": db['settings']['adminAccountNumber'],
        "toAcc": user['accountNumber'],
        "amount": amount
    })

    save_db(db)
    return jsonify({"success": True, "message": f"โอนเงินเข้าบัญชี {target_acc} สำเร็จจำนวน {amount} บาท"})
    
        function openAdminLoginModal() { document.getElementById('admin-login-modal').classList.remove('hidden'); }
        function closeAdminLoginModal() { document.getElementById('admin-login-modal').classList.add('hidden'); }
        async function handleAdminLogin(e) {
            e.preventDefault();
            const res = await fetch('/api/admin-login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    username: document.getElementById('admin-user-input').value,
                    password: document.getElementById('admin-pass-input').value
                })
            });
            const data = await res.json();
            if (data.success) {
                closeAdminLoginModal();
                openAdminDashboard();
            } else {
                showMessage("ผิดพลาด", data.message);
            }
        }

        async function openAdminDashboard() {
            await fetchDB();
            document.getElementById('admin-dashboard-modal').classList.remove('hidden');
            renderAdminUsers();
            renderAdminLogs();
            document.getElementById('admin-exchange-toggle').checked = dbState.settings.exchangeEventActive;
            document.getElementById('admin-acc-input-field').value = dbState.settings.adminAccountNumber;
            document.getElementById('admin-guide-textarea').value = dbState.settings.guideText;
        }
        function closeAdminDashboard() { document.getElementById('admin-dashboard-modal').classList.add('hidden'); if(currentUser) updateNavUserInfo(); }

        function switchAdminTab(tab) {
            ['users', 'logs', 'settings'].forEach(t => {
                document.getElementById(`adm-pane-${t}`).classList.add('hidden');
                document.getElementById(`adm-tab-${t}`).className = "flex-1 md:flex-none text-left px-4 py-3 rounded-xl text-sm font-medium text-slate-400 hover:bg-slate-800 transition";
            });
            document.getElementById(`adm-pane-${tab}`).classList.remove('hidden');
            document.getElementById(`adm-tab-${tab}`).className = "flex-1 md:flex-none text-left px-4 py-3 rounded-xl text-sm font-medium bg-purple-600 text-white transition";
        }

        function renderAdminUsers() {
            const tbody = document.getElementById('admin-users-table-body');
            document.getElementById('total-users-count').innerText = `${dbState.users.length} คน`;
            tbody.innerHTML = dbState.users.map(u => `
                <tr>
                    <td class="p-3 font-mono text-indigo-300">${u.accountNumber}</td>
                    <td class="p-3 font-medium text-white">${u.name}</td>
                    <td class="p-3 text-slate-300">${u.username}</td>
                    <td class="p-3 text-emerald-400 font-bold">${u.balance.toLocaleString()} บาท</td>
                    <td class="p-3 text-center space-x-2">
                        <button onclick="openEditUser('${u.accountNumber}')" class="bg-indigo-600/20 text-indigo-400 px-2 py-1 rounded"><i class="fa-solid fa-pen"></i></button>
                        <button onclick="deleteUser('${u.accountNumber}')" class="bg-rose-600/20 text-rose-400 px-2 py-1 rounded"><i class="fa-solid fa-trash"></i></button>
                    </td>
                </tr>
            `).join('');
        }

        async function deleteUser(acc) {
            if (confirm("ยืนยันการลบ?")) {
                await fetch('/api/admin/delete-user', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({accountNumber: acc}) });
                await fetchDB();
                renderAdminUsers();
            }
        }

        function openEditUser(acc) {
            const u = dbState.users.find(user => user.accountNumber === acc);
            if (!u) return;
            document.getElementById('edit-user-acc-orig').value = acc;
            document.getElementById('edit-user-name').value = u.name;
            document.getElementById('edit-user-username').value = u.username;
            document.getElementById('edit-user-balance').value = u.balance;
            document.getElementById('edit-user-modal').classList.remove('hidden');
        }
        function closeEditUserModal() { document.getElementById('edit-user-modal').classList.add('hidden'); }

        async function handleSaveEditedUser(e) {
            e.preventDefault();
            await fetch('/api/admin/edit-user', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    originalAcc: document.getElementById('edit-user-acc-orig').value,
                    name: document.getElementById('edit-user-name').value,
                    username: document.getElementById('edit-user-username').value,
                    balance: parseFloat(document.getElementById('edit-user-balance').value)
                })
            });
            closeEditUserModal();
            await fetchDB();
            renderAdminUsers();
            if (currentUser && currentUser.accountNumber === document.getElementById('edit-user-acc-orig').value) updateNavUserInfo();
        }

        function renderAdminLogs() {
            document.getElementById('admin-exchange-requests-list').innerHTML = dbState.exchangeRequests.map(r => `
                <div class="bg-slate-950 border border-slate-800 rounded-xl p-3 flex justify-between items-center text-xs">
                    <div>ผู้ใช้: ${r.username} (ขอแลก ${r.webAmount} บาท -> ธนาคาร: ${r.bankAccount})</div>
                    <button onclick="removeReq('${r.id}')" class="bg-slate-800 text-slate-300 px-3 py-1 rounded">ลบ</button>
                </div>
            `).join('') || '<p class="text-xs text-slate-500">ไม่มีคำขอ</p>';

            document.getElementById('admin-tx-table-body').innerHTML = dbState.transactions.slice(-20).reverse().map(t => `
                <tr>
                    <td class="p-3 text-slate-400">${new Date(t.timestamp).toLocaleString('th-TH')}</td>
                    <td class="p-3 font-bold text-indigo-300">${t.type}</td>
                    <td class="p-3 text-slate-200">${t.details} (${t.amount} บาท)</td>
                    <td class="p-3 text-center"><button onclick="deleteTx('${t.id}')" class="bg-rose-600/20 text-rose-400 px-2 py-1 rounded"><i class="fa-solid fa-trash"></i></button></td>
                </tr>
            `).join('') || '<tr><td colspan="4" class="p-center text-slate-500">ไม่มีประวัติ</td></tr>';
        }

        async function removeReq(id) {
            await fetch('/api/admin/remove-req', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({id}) });
            await fetchDB();
            renderAdminLogs();
        }

        async function deleteTx(id) {
            await fetch('/api/admin/delete-tx', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({id}) });
            await fetchDB();
            renderAdminLogs();
        }

        async function saveAdminSettings() {
            await fetch('/api/admin/update-settings', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    exchangeEventActive: document.getElementById('admin-exchange-toggle').checked,
                    adminAccountNumber: document.getElementById('admin-acc-input-field').value,
                    guideText: document.getElementById('admin-guide-textarea').value
                })
            });
            await fetchDB();
            showMessage("สำเร็จ", "บันทึกการตั้งค่าเรียบร้อยแล้ว");
        }
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    load_db()
    print("Starting Flask application...")
    print("Admin Username: 1482")
    print("Admin Password: 1842111482")
    app.run(host='0.0.0.0', port=5000, debug=True)
