import random
from datetime import datetime
from flask import Flask, redirect, render_template_string, request, session, url_for

app = Flask(__name__)
app.secret_key = "somice_express_secret_key_12345"

# Mock Databases in memory
USERS = {}  # username: {password, name, phone, email, type}
PARCELS = []  # list of dicts
EMPLOYEES = []  # list of dicts pending
APPROVED_EMPLOYEES = {}  # username: {role, province, ...}
CONTACT_INFO = {
    "facebook": "SomIce Express Official",
    "tiktok": "@somice_express",
    "phone": "02-123-4567",
}

PROVINCES_76 = [
    "กรุงเทพมหานคร",
    "กระบี่",
    "กาญจนบุรี",
    "กาฬสินธุ์",
    "กำแพงเพชร",
    "ขอนแก่น",
    "จันทบุรี",
    "ฉะเชิงเทรา",
    "ชลบุรี",
    "ชัยนาท",
    "ชัยภูมิ",
    "ชุมพร",
    "เชียงราย",
    "เชียงใหม่",
    "ตรัง",
    "ตราด",
    "ตาก",
    "นครนายก",
    "นครปฐม",
    "นครพนม",
    "นครราชสีมา",
    "นครศรีธรรมราช",
    "นครสวรรค์",
    "นนทบุรี",
    "นราธิวาส",
    "น่าน",
    "บึงกาฬ",
    "บุรีรัมย์",
    "ปทุมธานี",
    "ประจวบคีรีขันธ์",
    "ปราจีนบุรี",
    "ปัตตานี",
    "พระนครศรีอยุธยา",
    "พะเยา",
    "พังงา",
    "พัทลุง",
    "พิจิตร",
    "พิษณุโลก",
    "เพชรบุรี",
    "เพชรบูรณ์",
    "แพร่",
    "ภูเก็ต",
    "มหาสารคาม",
    "มุกดาหาร",
    "แม่ฮ่องสอน",
    "ยโสธร",
    "ยะลา",
    "ร้อยเอ็ด",
    "ระนอง",
    "ระยอง",
    "ราชบุรี",
    "ลพบุรี",
    "ลำปาง",
    "ลำพูน",
    "เลย",
    "ศรีสะเกษ",
    "สกลนคร",
    "สงขลา",
    "สตูล",
    "สมุทรปราการ",
    "สมุทรสงคราม",
    "สมุทรสาคร",
    "สระแก้ว",
    "สระบุรี",
    "สิงห์บุรี",
    "สุโขทัย",
    "สุพรรณบุรี",
    "สุราษฎร์ธานี",
    "สุรินทร์",
    "หนองคาย",
    "หนองบัวลำภู",
    "อ่างทอง",
    "อำนาจเจริญ",
    "อุดรธานี",
    "อุตรดิตถ์",
    "อุทัยธานี",
    "อุบลราชธานี",
]

BASE_STYLE = """
<style>
    body { background-color: #FFF9E6; font-family: Tahoma, sans-serif; color: #333333; margin: 0; padding: 0; }
    .container { max-width: 800px; margin: 30px auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
    h1, h2, h3 { color: #D4A017; }
    input, select, textarea { width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; }
    button, .btn { background-color: #FFC107; color: black; font-weight: bold; padding: 10px 15px; border: none; border-radius: 6px; cursor: pointer; text-decoration: none; display: inline-block; text-align: center; }
    button:hover, .btn:hover { background-color: #FFA000; }
    .btn-dark { background-color: #333333; color: white; }
    .btn-danger { background-color: #F44336; color: white; }
    .btn-success { background-color: #4CAF50; color: white; }
    table { width: 100%; border-collapse: collapse; margin-top: 15px; }
    th, td { border: 1px solid #ddd; padding: 10px; text-align: left; font-size: 14px; }
    th { background-color: #FFE082; }
    .nav { background: #FFC107; padding: 15px; display: flex; justify-content: space-between; align-items: center; font-weight: bold; }
    .nav a { color: #333; text-decoration: none; margin: 0 10px; }
    .alert { padding: 10px; background: #FFECB3; margin-bottom: 15px; border-radius: 6px; }
</style>
"""


@app.route("/")
def index():
    return render_template_string(
        BASE_STYLE
        + """
    <div class="container" style="text-align: center; margin-top: 80px;">
        <h1>SomIce Express</h1>
        <p style="font-size: 18px;">สวัสดียินดีต้อนรับสู่ SomIce Express บริการขนส่งพัสดุด่วนทั่วไทย</p>
        <div style="margin: 30px 0;">
            <a href="/login" class="btn" style="font-size: 16px; padding: 12px 25px;">เข้าสู่ระบบ / สมัครสมาชิก</a>
            <a href="/contact" class="btn btn-dark" style="font-size: 16px; padding: 12px 25px; margin-left: 10px;">ช่องทางติดต่อ</a>
        </div>
        <div style="margin-top: 40px; border-top: 1px solid #eee; padding-top: 20px;">
            <a href="/admin/login" style="margin: 0 15px; color: #666; font-weight: bold;">เข้าสู่ระบบ Admin</a>
            <a href="/staff/login" style="margin: 0 15px; color: #E65100; font-weight: bold;">เข้าสู่ระบบพนักงาน</a>
        </div>
    </div>
    """
    )


@app.route("/contact")
def contact():
    return render_template_string(
        BASE_STYLE
        + """
    <div class="container">
        <h2>ช่องทางติดต่อ SomIce Express</h2>
        <ul>
            <li>Facebook: {{ contact.facebook }}</li>
            <li>TikTok: {{ contact.tiktok }}</li>
            <li>เบอร์โทร: {{ contact.phone }}</li>
        </ul>
        <br>
        <a href="/" class="btn btn-dark">กลับหน้าหลัก</a>
    </div>
    """,
        contact=CONTACT_INFO,
    )


@app.route("/login", methods=["GET", "POST"])
def login_register():
    error = None
    success = None
    if request.method == "POST":
        action = request.form.get("action")
        if action == "register":
            u = request.form.get("username").strip()
            e = request.form.get("email").strip()
            p = request.form.get("phone").strip()
            fn = request.form.get("fullname").strip()
            pwd = request.form.get("password").strip()

            banned_passwords = [
                "12345678",
                "87654321",
                "21436587",
                "abcdefgh",
                "password",
                "11111111",
            ]
            if pwd in banned_passwords or len(pwd) < 6:
                error = "รหัสผ่านง่ายเกินไปหรือห้ามใช้ตามเงื่อนไข (เช่น 12345678, abcdefgh)"
            elif not u or not pwd or not fn:
                error = "กรุณากรอกข้อมูลให้ครบถ้วน"
            elif u in USERS:
                error = "ชื่อผู้ใช้นี้มีคนใช้แล้ว"
            else:
                USERS[u] = {
                    "password": pwd,
                    "name": fn,
                    "phone": p,
                    "email": e,
                }
                session["user"] = u
                return redirect(url_for("dashboard"))
        elif action == "login":
            u = request.form.get("username").strip()
            pwd = request.form.get("password").strip()
            if u in USERS and USERS[u]["password"] == pwd:
                session["user"] = u
                return redirect(url_for("dashboard"))
            else:
                error = "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง"

    return render_template_string(
        BASE_STYLE
        + """
    <div class="container" style="max-width: 600px;">
        <h2>สมาชิก SomIce Express</h2>
        {% if error %}<div class="alert" style="background: #FFCDD2; color: #C62828;">{{ error }}</div>{% endif %}
        
        <div style="display: flex; gap: 20px;">
            <div style="flex: 1; background: #FFF; padding: 15px; border: 1px solid #ddd; border-radius: 8px;">
                <h3>เข้าสู่ระบบ</h3>
                <form method="POST">
                    <input type="hidden" name="action" value="login">
                    <input name="username" placeholder="ชื่อผู้ใช้" required>
                    <input type="password" name="password" placeholder="รหัสผ่าน" required>
                    <button class="btn" style="width: 100%;">เข้าสู่ระบบ</button>
                </form>
            </div>
            
            <div style="flex: 1; background: #FFF; padding: 15px; border: 1px solid #ddd; border-radius: 8px;">
                <h3>สมัครสมาชิก</h3>
                <form method="POST">
                    <input type="hidden" name="action" value="register">
                    <input name="username" placeholder="ชื่อผู้ใช้" required>
                    <input name="email" placeholder="อีเมล">
                    <input name="phone" placeholder="เบอร์โทร">
                    <input name="fullname" placeholder="ชื่อ-นามสกุล" required>
                    <input type="password" name="password" placeholder="รหัสผ่าน (ขั้นต่ำ 6 ตัว)" required>
                    <button class="btn" style="width: 100%;">สมัครสมาชิก</button>
                </form>
            </div>
        </div>
        <br>
        <a href="/" class="btn btn-dark">กลับหน้าหลัก</a>
    </div>
    """,
        error=error,
    )


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect(url_for("login_register"))
    user = session["user"]
    msg = None

    tab = request.args.get("tab", "send")

    if request.method == "POST":
        action = request.form.get("action")
        if action == "create_parcel":
            pid = f"SOM-{random.randint(100000, 999999)}"
            p_data = {
                "id": pid,
                "sender_name": request.form.get("s_name"),
                "sender_phone": request.form.get("s_phone"),
                "sender_addr": request.form.get("s_addr"),
                "receiver_name": request.form.get("r_name"),
                "receiver_phone": request.form.get("r_phone"),
                "receiver_addr": request.form.get("r_addr"),
                "weight": request.form.get("weight"),
                "item_name": request.form.get("item_name"),
                "type": request.form.get("p_type"),
                "cod_price": (
                    request.form.get("cod_price")
                    if request.form.get("p_type") == "เก็บเงินปลายทาง"
                    else "0"
                ),
                "status": "รอดำเนินการ (รอแอดมินเลือกจังหวัด)",
                "province": "ยังไม่ระบุ",
                "courier": "-",
            }
            PARCELS.append(p_data)
            msg = f"สร้างพัสดุสำเร็จ! รหัสพัสดุของคุณคือ: {pid}"
        elif action == "apply_job":
            try:
                dob_y = int(request.form.get("dob_y"))
                if datetime.now().year - dob_y < 25:
                    return render_template_string(
                        BASE_STYLE
                        + """
                    <div class="container">
                        <h3>ขออภัย ระบบกำหนดอายุขั้นต่ำ 25 ปีขึ้นไป</h3>
                        <a href="/dashboard?tab=profile" class="btn">กลับ</a>
                    </div>
                    """
                    )
            except:
                pass

            job_data = {
                "type": request.form.get("job_type"),
                "fname": request.form.get("fname"),
                "lname": request.form.get("lname"),
                "username": request.form.get("j_user"),
                "password": request.form.get("j_pass"),
                "phone": request.form.get("j_phone"),
                "status": "รออนุมัติ",
            }
            EMPLOYEES.append(job_data)
            msg = "ส่งใบสมัครเรียบร้อยแล้ว กรุณารอ Admin ออนุมัติ"
        elif action == "update_profile":
            if request.form.get("name"):
                USERS[user]["name"] = request.form.get("name")
            if request.form.get("password"):
                USERS[user]["password"] = request.form.get("password")
            msg = "แก้ไขโปรไฟล์สำเร็จ"

    # Track search
    track_result = None
    track_id = request.args.get("track_id")
    if track_id:
        for p in PARCELS:
            if p["id"] == track_id.strip():
                track_result = p
                break
        if not track_result:
            track_result = "not_found"

    return render_template_string(
        BASE_STYLE
        + """
    <div class="nav">
        <span>🤖 ยินดีต้อนรับคุณ {{ user_info.name }} (SomIce Express)</span>
        <a href="/logout" style="color: #C62828;">ออกจากระบบ</a>
    </div>
    
    <div class="container" style="max-width: 900px;">
        {% if msg %}<div class="alert">{{ msg }}</div>{% endif %}
        
        <div style="display: flex; gap: 10px; margin-bottom: 20px; border-bottom: 2px solid #FFE082; padding-bottom: 10px;">
            <a href="/dashboard?tab=send" class="btn {% if tab != 'send' %}btn-dark{% endif %}">1. ส่งพัสดุ / ติดตาม</a>
            <a href="/dashboard?tab=calc" class="btn {% if tab != 'calc' %}btn-dark{% endif %}">2. คำนวณค่าพัสดุ</a>
            <a href="/dashboard?tab=shop" class="btn {% if tab != 'shop' %}btn-dark{% endif %}">3. ร้านค้า</a>
            <a href="/dashboard?tab=contact" class="btn {% if tab != 'contact' %}btn-dark{% endif %}">4. แจ้งปัญหา</a>
            <a href="/dashboard?tab=profile" class="btn {% if tab != 'profile' %}btn-dark{% endif %}">5. จัดการฉัน / สมัครงาน</a>
        </div>
        
        {% if tab == 'send' %}
            <h2>รับพัสดุหน้าบ้าน & ติดตามพัสดุ</h2>
            <div style="display: flex; gap: 30px;">
                <div style="flex: 1; background: #fff; padding: 15px; border: 1px solid #ddd; border-radius: 8px;">
                    <h3>สร้างรายการส่งพัสดุ</h3>
                    <form method="POST">
                        <input type="hidden" name="action" value="create_parcel">
                        <h4>ผู้ส่ง</h4>
                        <input name="s_name" placeholder="ชื่อผู้ส่ง" required>
                        <input name="s_phone" placeholder="เบอร์โทรผู้ส่ง" required>
                        <textarea name="s_addr" placeholder="ที่อยู่ผู้ส่ง" required></textarea>
                        
                        <h4>ผู้รับ</h4>
                        <input name="r_name" placeholder="ชื่อผู้รับ" required>
                        <input name="r_phone" placeholder="เบอร์โทรผู้รับ" required>
                        <textarea name="r_addr" placeholder="ที่อยู่ผู้รับ" required></textarea>
                        
                        <h4>รายละเอียดพัสดุ</h4>
                        <input name="weight" placeholder="น้ำหนัก (กก.)" required>
                        <input name="item_name" placeholder="ชื่อสิ่งของ" required>
                        <select name="p_type">
                            <option value="ไม่เก็บเงินปลายทาง">ไม่เก็บเงินปลายทาง</option>
                            <option value="เก็บเงินปลายทาง">เก็บเงินปลายทาง</option>
                        </select>
                        <input name="cod_price" placeholder="ราคาเก็บเงินปลายทาง (ถ้ามี)">
                        <button class="btn" style="width: 100%; margin-top: 10px;">สร้างพัสดุ</button>
                    </form>
                </div>
                
                <div style="flex: 1; background: #fff; padding: 15px; border: 1px solid #ddd; border-radius: 8px;">
                    <h3>ติดตามพัสดุ</h3>
                    <form method="GET">
                        <input type="hidden" name="tab" value="send">
                        <input name="track_id" placeholder="กรอกรหัสพัสดุ เช่น SOM-XXXXXX" value="{{ request.args.get('track_id', '') }}">
                        <button class="btn btn-dark" style="width: 100%;">ค้นหาพัสดุ</button>
                    </form>
                    
                    {% if track_result %}
                        <div style="margin-top: 15px; background: #FFF8E1; padding: 10px; border-radius: 6px;">
                            {% if track_result == 'not_found' %}
                                <p style="color: red;">ไม่พบรหัสพัสดุนี้ในระบบ</p>
                            {% else %}
                                <p><b>รหัส:</b> {{ track_result.id }}</p>
                                <p><b>สถานะ:</b> {{ track_result.status }}</p>
                                <p><b>ผู้ส่ง:</b> {{ track_result.sender_name }}</p>
                                <p><b>ผู้รับ:</b> {{ track_result.receiver_name }} ({{ track_result.receiver_addr }})</p>
                                <p><b>พนักงานขนส่ง:</b> {{ track_result.courier }}</p>
                                {% if track_result.proof_image %}
                                    <p style="color: green;"><b>หลักฐานการส่ง:</b> {{ track_result.proof_image }}</p>
                                {% endif %}
                            {% endif %}
                        </div>
                    {% endif %}
                </div>
            </div>
            
        {% elif tab == 'calc' %}
            <h2>คำนวณค่าพัสดุอัตโนมัติ</h2>
            <form method="POST" id="calcForm" onsubmit="calculateFee(event)">
                <input id="c_dist" placeholder="ระยะทาง (กิโลเมตร)" type="number" required>
                <input id="c_weight" placeholder="น้ำหนักพัสดุ (กก.)" type="number" step="0.1" required>
                <button class="btn">คำนวณค่าบริการ</button>
            </form>
            <div id="calcResult" style="margin-top: 20px; font-size: 16px; font-weight: bold; color: #D4A017;"></div>
            <script>
                function calculateFee(e) {
                    e.preventDefault();
                    let dist = parseFloat(document.getElementById('c_dist').value);
                    let weight = parseFloat(document.getElementById('c_weight').value);
                    let dist_fee = dist > 1000 ? 100 : dist >= 250 ? 75 : dist >= 200 ? 50 : dist >= 100 ? 35 : 25;
                    let weight_fee = weight >= 150 ? 50 : weight > 25 ? 20 : 10;
                    let total = dist_fee + weight_fee;
                    document.getElementById('calcResult').innerText = `ค่าบริการตามระยะทาง (${dist} กม.): ${dist_fee} บาท\nค่าบริการตามน้ำหนัก (${weight} กก.): ${weight_fee} บาท\nรวมค่าบริการทั้งสิ้น: ${total} บาท`;
                }
            </script>
            
        {% elif tab == 'shop' %}
            <h2>ร้านค้าอุปกรณ์แพ็คพัสดุ</h2>
            <ul>
                <li><b>กล่องพัสดุ:</b> ไซส์ 10 (5.-) | ไซส์ 20 (10.-) | ไซส์ 30 (15.-) | ไซส์ 50 (25.-)</li>
                <li><b>เทปใส/เทปพิมพ์ลาย:</b> 1 ม้วน (20.-) | 3 ม้วน (50.-) | 5 ม้วน (100.-)</li>
            </ul>
            
        {% elif tab == 'contact' %}
            <h2>แจ้งปัญหา & ช่องทางติดต่อ</h2>
            <form onsubmit="alert('ส่งปัญหาเรียบร้อยแล้ว ขอบคุณครับ'); return false;">
                <textarea placeholder="กรอกปัญหาที่เจอในระบบ..." required></textarea>
                <button class="btn">ส่งปัญหา</button>
            </form>
            <br>
            <p><b>ช่องทางการติดต่อ:</b> Facebook: {{ contact.facebook }} | TikTok: {{ contact.tiktok }} | โทร: {{ contact.phone }}</p>
            
        {% elif tab == 'profile' %}
            <h2>จัดการโปรไฟล์ & สมัครงานพนักงาน</h2>
            <div style="display: flex; gap: 30px;">
                <div style="flex: 1;">
                    <h3>แก้ไขโปรไฟล์</h3>
                    <form method="POST">
                        <input type="hidden" name="action" value="update_profile">
                        <input name="name" value="{{ user_info.name }}" placeholder="ชื่อจริง" required>
                        <input type="password" name="password" placeholder="รหัสผ่านใหม่">
                        <button class="btn">บันทึก</button>
                    </form>
                </div>
                
                <div style="flex: 1;">
                    <h3>สมัครงานกับ SomIce Express (อายุ 25 ปีขึ้นไป)</h3>
                    <form method="POST">
                        <input type="hidden" name="action" value="apply_job">
                        <select name="job_type">
                            <option value="สมัครพนักงานขนส่ง">สมัครพนักงานขนส่ง</option>
                            <option value="สมัครพนักงานขับรถ">สมัครพนักงานขับรถ</option>
                            <option value="สมัครพนักงานประจำสาขา">สมัครพนักงานประจำสาขา</option>
                        </select>
                        <input name="fname" placeholder="ชื่อจริง" required>
                        <input name="lname" placeholder="นามสกุล" required>
                        <div style="display: flex; gap: 5px;">
                            <select name="dob_d">{% for i in range(1, 32) %}<option value="{{i}}">{{i}}</option>{% endfor %}</select>
                            <select name="dob_m">{% for i in range(1, 13) %}<option value="{{i}}">{{i}}</option>{% endfor %}</select>
                            <select name="dob_y">{% for i in range(1950, 2010) %}<option value="{{i}}">{{i}}</option>{% endfor %}</select>
                     </div>
                        <input name="j_user" placeholder="ชื่อผู้ใช้ทำงาน" required>
                        <input type="password" name="j_pass" placeholder="รหัสผ่าน" required>
                        <input name="j_phone" placeholder="เบอร์โทร" required>
                        <button class="btn" style="background: #FF8F00; color: white; margin-top: 10px;">ส่งใบสมัครงาน</button>
                    </form>
                </div>
            </div>
        {% endif %}
    </div>
    """,
        user_info=USERS[user],
        contact=CONTACT_INFO,
        tab=tab,
        msg=msg,
        track_result=track_result,
    )


# --- ADMIN PANEL ---
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        if (
            request.form.get("username") == "1428"
            and request.form.get("password") == "148222"
        ):
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            error = "ชื่อหรือรหัสผ่าน Admin ไม่ถูกต้อง"
    return render_template_string(
        BASE_STYLE
        + """
    <div class="container" style="max-width: 400px; margin-top: 100px;">
        <h2>เข้าสู่ระบบ Admin</h2>
        {% if error %}<div class="alert" style="background: #FFCDD2; color: #C62828;">{{ error }}</div>{% endif %}
        <form method="POST">
            <input name="username" placeholder="ชื่อ Admin (1428)" required>
            <input type="password" name="password" placeholder="รหัส Admin (148222)" required>
            <button class="btn btn-dark" style="width: 100%;">เข้าสู่ระบบ</button>
        </form>
        <br><a href="/" class="btn" style="width: 100%;">กลับหน้าหลัก</a>
    </div>
    """,
        error=error,
    )


@app.route("/admin/dashboard", methods=["GET", "POST"])
def admin_dashboard():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    msg = None
    if request.method == "POST":
        action = request.form.get("action")
        if action == "assign_province":
            idx = int(request.form.get("parcel_idx"))
            prov = request.form.get("province")
            PARCELS[idx]["province"] = prov
            PARCELS[idx][
                "status"
            ] = f"รอพนักงานสาขา/ขนส่งจังหวัด {prov} รับไปดำเนินการ"
            msg = f"บันทึกพัสดุไปจังหวัด {prov} เรียบร้อย"
        elif action == "approve_emp":
            idx = int(request.form.get("emp_idx"))
            status = request.form.get("status")
            emp = EMPLOYEES[idx]
            emp["status"] = status
            if status == "อนุมัติแล้ว":
                APPROVED_EMPLOYEES[emp["username"]] = emp
            msg = "จัดการสถานะพนักงานเรียบร้อย"

    sub_tab = request.args.get("sub_tab", "parcels")
    return render_template_string(
        BASE_STYLE
        + """
    <div class="nav">
        <span>🛠️ ระบบ Admin Panel (SomIce Express)</span>
        <a href="/logout" style="color: #C62828;">ออกจากระบบ</a>
    </div>
    
    <div class="container" style="max-width: 1000px;">
        {% if msg %}<div class="alert">{{ msg }}</div>{% endif %}
        
        <div style="display: flex; gap: 10px; margin-bottom: 20px;">
            <a href="/admin/dashboard?sub_tab=parcels" class="btn {% if sub_tab != 'parcels' %}btn-dark{% endif %}">1. จัดการพัสดุ (76 จังหวัด)</a>
            <a href="/admin/dashboard?sub_tab=emps" class="btn {% if sub_tab != 'emps' %}btn-dark{% endif %}">2. อนุมัติพนักงาน</a>
        </div>
        
        {% if sub_tab == 'parcels' %}
            <h2>รายการพัสดุทั้งหมด</h2>
            <table>
                <tr><th>รหัสพัสดุ</th><th>ผู้ส่ง</th><th>ผู้รับ</th><th>สถานะปัจจุบัน</th><th>เลือกจังหวัด</th></tr>
                {% for p in parcels %}
                <tr>
                    <td>{{ p.id }}</td>
                    <td>{{ p.sender_name }}</td>
                    <td>{{ p.receiver_name }}</td>
                    <td>{{ p.status }}</td>
                    <td>
                        <form method="POST" style="display: flex; gap: 5px; margin: 0;">
                            <input type="hidden" name="action" value="assign_province">
                            <input type="hidden" name="parcel_idx" value="{{ loop.index0 }}">
                            <select name="province">
                                {% for prov in provinces %}
                                <option value="{{ prov }}" {% if p.province == prov %}selected{% endif %}>{{ prov }}</option>
                                {% endfor %}
                            </select>
                            <button class="btn" style="padding: 5px 10px;">บันทึก</button>
                        </form>
                    </td>
                </tr>
                {% endfor %}
            </table>
            
        {% elif sub_tab == 'emps' %}
            <h2>รายการสมัครพนักงาน</h2>
            <table>
                <tr><th>ชื่อ-นามสกุล</th><th>ตำแหน่ง</th><th>ชื่อผู้ใช้</th><th>สถานะ</th><th>จัดการ</th></tr>
                {% for e in employees %}
                <tr>
                    <td>{{ e.fname }} {{ e.lname }}</td>
                    <td>{{ e.type }}</td>
                    <td>{{ e.username }}</td>
                    <td>{{ e.status }}</td>
                    <td>
                        <form method="POST" style="display: inline;">
                            <input type="hidden" name="action" value="approve_emp">
                            <input type="hidden" name="emp_idx" value="{{ loop.index0 }}">
                            <input type="hidden" name="status" value="อนุมัติแล้ว">
                            <button class="btn btn-success" style="padding: 5px 10px;">ยอมรับ</button>
                        </form>
                        <form method="POST" style="display: inline;">
                            <input type="hidden" name="action" value="approve_emp">
                            <input type="hidden" name="emp_idx" value="{{ loop.index0 }}">
                            <input type="hidden" name="status" value="ไม่ยอมรับ">
                            <button class="btn btn-danger" style="padding: 5px 10px;">ปฏิเสธ</button>
                        </form>
                    </td>
                </tr>
                {% endfor %}
            </table>
        {% endif %}
    </div>
    """,
        parcels=PARCELS,
        employees=EMPLOYEES,
        provinces=PROVINCES_76,
        sub_tab=sub_tab,
        msg=msg,
    )


# --- STAFF PANEL ---
@app.route("/staff/login", methods=["GET", "POST"])
def staff_login():
    error = None
    if request.method == "POST":
        u = request.form.get("username").strip()
        pwd = request.form.get("password").strip()
        if u in APPROVED_EMPLOYEES and APPROVED_EMPLOYEES[u]["password"] == pwd:
            session["staff"] = u
            return redirect(url_for("staff_dashboard"))
        else:
            error = (
                "ชื่อหรือรหัสผ่านพนักงานไม่ถูกต้อง หรือยังไม่ได้รับอนุมัติจาก Admin"
            )

    return render_template_string(
        BASE_STYLE
        + """
    <div class="container" style="max-width: 400px; margin-top: 100px;">
        <h2>เข้าสู่ระบบพนักงาน</h2>
        {% if error %}<div class="alert" style="background: #FFCDD2; color: #C62828;">{{ error }}</div>{% endif %}
        <form method="POST">
            <input name="username" placeholder="ชื่อผู้ใช้พนักงาน" required>
            <input type="password" name="password" placeholder="รหัสผ่าน" required>
            <button class="btn" style="width: 100%; background: #FF8F00; color: white;">เข้าสู่ระบบพนักงาน</button>
        </form>
        <br><a href="/" class="btn" style="width: 100%;">กลับหน้าหลัก</a>
    </div>
    """,
        error=error,
    )


@app.route("/staff/dashboard", methods=["GET", "POST"])
def staff_dashboard():
    if "staff" not in session:
        return redirect(url_for("staff_login"))
    staff_user = session["staff"]
    emp_info = APPROVED_EMPLOYEES[staff_user]
    msg = None

    if request.method == "POST":
        action = request.form.get("action")
        if action == "accept_job":
            idx = int(request.form.get("parcel_idx"))
            PARCELS[idx]["status"] = "กำลังไปรับพัสดุ"
            PARCELS[idx]["courier"] = emp_info["fname"]
            msg = "รับงานสำเร็จ"
        elif action == "print_receipt":
            idx = int(request.form.get("parcel_idx"))
            PARCELS[idx]["status"] = "พัสดุรับเรียบร้อยแล้ว"
            msg = "พิมพ์ใบเสร็จและอัปเดตสถานะสำเร็จ"
        elif action == "deliver_photo":
            idx = int(request.form.get("parcel_idx"))
            PARCELS[idx]["status"] = "จัดส่งสำเร็จ"
            PARCELS[idx]["proof_image"] = "photo_proof_house.png"
            msg = "บันทึกจัดส่งสำเร็จ"

    return render_template_string(
        BASE_STYLE
        + """
    <div class="nav">
        <span>🚚 หน้าพนักงาน: {{ emp.fname }} ({{ emp.type }})</span>
        <a href="/logout" style="color: #C62828;">ออกจากระบบ</a>
    </div>
    
    <div class="container" style="max-width: 900px;">
        {% if msg %}<div class="alert">{{ msg }}</div>{% endif %}
        
        <h2>จัดการงานพัสดุ</h2>
        <table>
            <tr><th>รหัสพัสดุ</th><th>จังหวัด</th><th>ผู้รับ</th><th>สถานะ</th><th>จัดการ</th></tr>
            {% for p in parcels %}
            <tr>
                <td>{{ p.id }}</td>
                <td>{{ p.province }}</td>
                <td>{{ p.receiver_name }}</td>
                <td>{{ p.status }}</td>
                <td>
                    {% if p.status.startswith('รอดำเนินการ') %}
                        <form method="POST" style="margin:0;">
                            <input type="hidden" name="action" value="accept_job">
                            <input type="hidden" name="parcel_idx" value="{{ loop.index0 }}">
                            <button class="btn" style="padding: 5px 10px;">กดรับงาน</button>
                        </form>
                    {% elif p.status == 'กำลังไปรับพัสดุ' %}
                        <form method="POST" style="margin:0; display:inline;">
                            <input type="hidden" name="action" value="print_receipt">
                            <input type="hidden" name="parcel_idx" value="{{ loop.index0 }}">
                            <button class="btn btn-success" style="padding: 5px 10px;">พิมพ์ใบเสร็จ</button>
                        </form>
                        <form method="POST" style="margin:0; display:inline;">
                            <input type="hidden" name="action" value="deliver_photo">
                            <input type="hidden" name="parcel_idx" value="{{ loop.index0 }}">
                            <button class="btn" style="padding: 5px 10px; background: #FF8F00; color: white;">จัดส่งสำเร็จ</button>
                        </form>
                    {% else %}
                        <span>เสร็จสิ้น</span>
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>
    """,
        emp=emp_info,
        parcels=PARCELS,
        msg=msg,
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
