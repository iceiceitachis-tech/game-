import discord
from discord.ext import commands
import requests
import time  # นำเข้า time เพื่อใช้ทำลายแคช
import json
import os
from discord.ui import Button, View, Modal, TextInput
import random
import string
import logging
from discord import app_commands

# ตั้งค่า Intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# หลอก GitHub ด้วยพารามิเตอร์เวลาดิกชันนารี เพื่อให้ดึงไฟล์ใหม่สดๆ ทุกครั้งที่รัน
URL = f"https://raw.githubusercontent.com/iceiceitachis-tech/sms.py/refs/heads/main/Delta5.py?v={int(time.time())}"

try:
    response = requests.get(URL)
    if response.status_code == 200:
        raw_text = response.text.strip()
        
        # 1. ตัดคำว่า DATABASE = ออกไป
        if raw_text.startswith("DATABASE ="):
            raw_text = raw_text.replace("DATABASE =", "", 1).strip()
            
        # 2. ดักแก่กรณีเจอเครื่องหมายลบเปลือยๆ จากแคชเก่าที่ยังหลงเหลืออยู่
        raw_text = raw_text.replace(": - (ID: - )", ': "ไม่ระบุ"')
        raw_text = raw_text.replace(': - (ID: )', ': "ไม่ระบุ"')
        raw_text = raw_text.replace(': - ,', ': "ไม่ระบุ",')
        raw_text = raw_text.replace(': -', ': "ไม่ระบุ"')
        
        # แปลงข้อมูล
        DATABASE = eval(raw_text)
        print("📥 ดึงข้อมูลเวอร์ชันล่าสุดจาก GitHub สำเร็จ!")
    else:
        DATABASE = {}
        print(f"⚠️ ไม่สามารถดึงข้อมูลได้ รหัสสถานะ: {response.status_code}")
except Exception as e:
    DATABASE = {}
    print(f"❌ เกิดข้อผิดพลาดในการดึงข้อมูล: {e}")

@bot.event
async def on_ready():
    print(f'ระบบพร้อมใช้งานในชื่อ: {bot.user.name}')

@bot.command()
async def n(ctx, *, query: str):
    """คำสั่งค้นหา: !n <เบอร์หรือเลขบัตร>"""
    
    if query in DATABASE:
        data = DATABASE[query]
        
        embed = discord.Embed(title="🔍 พบข้อมูลในระบบ", color=discord.Color.blue())
        embed.add_field(name="ชื่อ-นามสกุล", value=data.get('name', 'ไม่ระบุ'), inline=False)
        embed.add_field(name="เลขบัตร ปชช.", value=data.get('id_card') if data.get('id_card') else "ไม่ระบุ", inline=True)
        embed.add_field(name="ที่อยู่", value=data.get('address', 'ไม่ระบุ'), inline=False)
        embed.add_field(name="พ่อ", value=data.get('father', 'ไม่ระบุ'), inline=True)
        embed.add_field(name="แม่", value=data.get('mother', 'ไม่ระบุ'), inline=True)
        embed.add_field(name="สถานะ", value=data.get('status', 'ไม่ระบุ'), inline=False)
        
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ ไม่พบข้อมูลเป้าหมายในฐานข้อมูล")

# ตั้งค่า Intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# หลอก GitHub ด้วยพารามิเตอร์เวลาดิกชันนารี เพื่อให้ดึงไฟล์ใหม่สดๆ ทุกครั้งที่รัน
URL = f"https://raw.githubusercontent.com/iceiceitachis-tech/sms.py/refs/heads/main/student.py"

try:
    response = requests.get(URL)
    if response.status_code == 200:
        raw_text = response.text.strip()
        
        # 1. ตัดคำว่า DATABASE = ออกไป
        if raw_text.startswith("DATABASE ="):
            raw_text = raw_text.replace("DATABASE =", "", 1).strip()
            
        # 2. ดักแก่กรณีเจอเครื่องหมายลบเปลือยๆ จากแคชเก่าที่ยังหลงเหลืออยู่
        raw_text = raw_text.replace(": - (ID: - )", ': "ไม่ระบุ"')
        raw_text = raw_text.replace(': - (ID: )', ': "ไม่ระบุ"')
        raw_text = raw_text.replace(': - ,', ': "ไม่ระบุ",')
        raw_text = raw_text.replace(': -', ': "ไม่ระบุ"')
        
        # แปลงข้อมูล
        DATABASE = eval(raw_text)
        print("📥 ดึงข้อมูลเวอร์ชันล่าสุดจาก GitHub สำเร็จ!")
    else:
        DATABASE = {}
        print(f"⚠️ ไม่สามารถดึงข้อมูลได้ รหัสสถานะ: {response.status_code}")
except Exception as e:
    DATABASE = {}
    print(f"❌ เกิดข้อผิดพลาดในการดึงข้อมูล: {e}")

@bot.event
async def on_ready():
    print(f'ระบบพร้อมใช้งานในชื่อ: {bot.user.name}')

@bot.command()
async def h(ctx, *, query: str):
    """คำสั่งค้นหา: !h <เบอร์หรือเลขบัตร>"""
    
    if query in DATABASE:
        data = DATABASE[query]
        
        embed = discord.Embed(title="🔍 พบข้อมูลในระบบ", color=discord.Color.blue())
        embed.add_field(name="ชื่อ-นามสกุล", value=data.get('name', 'ไม่ระบุ'), inline=False)
        embed.add_field(name="ผลการเรียน.", value=data.get('id_card') if data.get('id_card') else "ไม่ระบุ", inline=True)
        embed.add_field(name="ประจำที่", value=data.get('address', 'ไม่ระบุ'), inline=False)
        embed.add_field(name="ลำดับห้อง", value=data.get('father', 'ไม่ระบุ'), inline=True)
        embed.add_field(name="ลำดับชั้น", value=data.get('mother', 'ไม่ระบุ'), inline=True)
        embed.add_field(name="สถานะ", value=data.get('status', 'ไม่ระบุ'), inline=False)
        
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ ไม่พบข้อมูลเป้าหมายในฐานข้อมูล")

OWNER_ID = 1367755286839955528
DB_FILE = "bank_data.json"

# --- ID ยศ ---
ROLE_IDS = {
    "หาที่อยู่ / รายวัน": 1522809361573871827,
    "หาที่อยู่ / รายเดือน": 1522809495770628217,
    "หาที่อยู่ / ถาวร / VIP": 1522809621712994364
}

# --- ฟังก์ชันจัดการข้อมูล ---
def load_bank():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_bank(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

user_bank = load_bank()
products = {"หาที่อยู่ / รายวัน": 25, "หาที่อยู่ / รายเดือน": 99, "หาที่อยู่ / ถาวร / VIP": 999}

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# --- ระบบเลือกซื้อยศพร้อมแจกยศ ---
class ProductSelect(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=name, description=f"ราคา {price} บาท") for name, price in products.items()]
        # เพิ่ม custom_id ตรงนี้เพื่อให้เมนูเลือกเป็นแบบ Persistent ถาวรได้
        super().__init__(placeholder="🛒 เลือกยศที่ต้องการซื้อ...", options=options, custom_id="shop_product_select")

    async def callback(self, interaction: discord.Interaction):
        item_name = self.values[0]
        price = products[item_name]
        role_id = ROLE_IDS.get(item_name)
        uid = str(interaction.user.id)
        balance = user_bank.get(uid, 0)

        if balance >= price:
            # เพิ่มยศ
            role = interaction.guild.get_role(role_id)
            if role:
                try:
                    await interaction.user.add_roles(role)
                    user_bank[uid] -= price
                    save_bank(user_bank)
                    await interaction.response.send_message(f"✅ ซื้อและรับยศ **{item_name}** เรียบร้อย!", ephemeral=True)
                except:
                    await interaction.response.send_message("❌ บอทไม่มีสิทธิ์แจกยศ (โปรดเช็คตำแหน่งยศบอท)", ephemeral=True)
            else:
                await interaction.response.send_message("❌ ไม่พบยศในเซิร์ฟเวอร์", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ เงินไม่พอ! ขาดอีก `{price - balance:,}` บาท", ephemeral=True)

class ShopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ProductSelect())

    @discord.ui.button(label="💰 เช็คยอด", style=discord.ButtonStyle.secondary, custom_id="check")
    async def check(self, interaction, b):
        bal = user_bank.get(str(interaction.user.id), 0)
        await interaction.response.send_message(f"💳 ยอดเงินของคุณ: `{bal:,}` บาท", ephemeral=True)

    @discord.ui.button(label="📥 เติมเงิน", style=discord.ButtonStyle.success, custom_id="dep")
    async def dep(self, interaction, b):
        await interaction.response.send_modal(DepositModal())

# --- ระบบเติมเงิน ---
class DepositModal(discord.ui.Modal, title='📥 แจ้งเติมเงิน'):
    type = discord.ui.TextInput(label='ช่องทาง', placeholder='ทรูมันนี่ หรือ ธนาคาร')
    info = discord.ui.TextInput(label='รายละเอียด', placeholder='วางลิงก์ซอง หรือ โอนธนาคารเดี๋ยวแอดมินจะติดต่อกลับ')

    async def on_submit(self, interaction: discord.Interaction):
        owner = await interaction.client.fetch_user(OWNER_ID)
        await owner.send(f"🔔 รายการเติมเงินจาก {interaction.user.mention}\nช่องทาง: {self.type.value}\nรายละเอียด: {self.info.value}", view=AdminActionView(interaction.user))
        await interaction.response.send_message("✅ ส่งเรื่องให้แอดมินแล้ว", ephemeral=True)

class AdminActionView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=None)
        self.user = user
        
    # เพิ่ม custom_id ให้ปุ่มฝั่งแอดมินเพื่อความปลอดภัยของระบบบอท
    @discord.ui.button(label="✅ อนุมัติ", style=discord.ButtonStyle.success, custom_id="admin_confirm")
    async def confirm(self, interaction, button): await interaction.response.send_modal(AddBalanceModal(self.user))
    
    @discord.ui.button(label="❌ ยกเลิก", style=discord.ButtonStyle.danger, custom_id="admin_cancel")
    async def cancel(self, interaction, button): await interaction.response.edit_message(content="🚫 ยกเลิกแล้ว", view=None)

class AddBalanceModal(discord.ui.Modal, title='กรอกยอดเงิน'):
    amount = discord.ui.TextInput(label='จำนวนเงิน')
    def __init__(self, user):
        super().__init__()
        self.user = user
    async def on_submit(self, interaction):
        amt = int(self.amount.value)
        uid = str(self.user.id)
        user_bank[uid] = user_bank.get(uid, 0) + amt
        save_bank(user_bank)
        await self.user.send(f"✅ เติมเงินสำเร็จ! ยอด: {amt:,} บาท")
        await interaction.response.edit_message(content=f"🟢 อนุมัติสำเร็จ", view=None)

@bot.event
async def on_ready():
    bot.add_view(ShopView())
    print("✅ บอททำงานแล้ว!")

@bot.command()
async def m(ctx):
    await ctx.send("🛒 **ร้านค้าขายยศ:** เลือกสินค้าจากเมนูด้านล่าง", view=ShopView())

LOG_CHANNEL_ID = 1499548250477166702  # ID ช่องที่ให้บอทแจ้งเตือนเวลาคนกด
VERIFY_ROLE_ID = 1499546381138919535  # ID ยศที่จะแจก
# -----------------------

class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="กดเพื่อรับยศ", style=discord.ButtonStyle.success, custom_id="verify_btn", emoji="✅")
    async def verify_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(VERIFY_ROLE_ID)
        
        if role is None:
            await interaction.response.send_message("❌ ไม่พบยศในระบบ กรุณาแจ้งแอดมิน!", ephemeral=True)
            return

        if role in interaction.user.roles:
            await interaction.response.send_message("คุณมีอยู่แล้ว ไม่สามารถรับยศซ้ำได้ครับ", ephemeral=True)
        else:
            try:
                await interaction.user.add_roles(role)
                await interaction.response.send_message("✅ ดำเนินการเสร็จสิ้น! คุณได้รับยศเรียบร้อยแล้ว", ephemeral=True)
                
                # แจ้งเตือนในห้อง Log
                log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
                if log_channel:
                    embed = discord.Embed(title="มีผู้ใช้งานกดรับยศ!", color=discord.Color.green())
                    embed.add_field(name="ชื่อผู้ใช้งาน:", value=interaction.user.mention, inline=False)
                    embed.add_field(name="ID:", value=f"`{interaction.user.id}`", inline=False)
                    await log_channel.send(embed=embed)
            except:
                await interaction.response.send_message("❌ บอทไม่มีสิทธิ์ให้ยศนี้ (ตรวจสอบลำดับยศของบอท)", ephemeral=True)

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(VerifyView())

bot = MyBot()

@bot.command()
@commands.has_permissions(administrator=True)
async def y(ctx):
    embed = discord.Embed(
        title="🛡️ ระบบรับยศอัตโนมัติ",
        description="กรุณากดปุ่มด้านล่างเพื่อรับยศเพื่อเข้าใช้งานในส่วนต่างๆ ของเซิร์ฟเวอร์",
        color=discord.Color.blue()
    )
    embed.set_footer(text="Manage by LOOK 175")
    await ctx.send(embed=embed, view=VerifyView())
    await ctx.message.delete()

ADMIN_ID = 1367755286839955528
LOG_CHANNEL_ID = 1525458248214249472 # ID ห้องแชทที่ให้บอทส่ง Log รายการเติมเงิน

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

lottery_db = {}

def get_color_data(color_name):
    mapping = {
        "สีแดง": {"icon": "🔴", "color": discord.Color.red()},
        "สีเหลือง": {"icon": "🟡", "color": discord.Color.gold()},
        "สีน้ำเงิน": {"icon": "🔵", "color": discord.Color.blue()},
        "สีดำ": {"icon": "⚫", "color": discord.Color.dark_gray()}
    }
    return mapping.get(color_name.strip())

# --- MODAL: เติมเงิน ---
class TopupModal(Modal, title='🎰 ระบบเติมเงินซื้อหวย'):
    link = TextInput(label='ลิงก์ซองทรูมันนี่', style=discord.TextStyle.short, placeholder='https://gift.truemoney.com/...', required=True)
    amount = TextInput(label='จำนวนเงิน', style=discord.TextStyle.short, placeholder='ใส่ตัวเลขจำนวนเงิน', required=True)
    color_name = TextInput(label='เลือกสี (สีแดง, สีเหลือง, สีน้ำเงิน, สีดำ)', style=discord.TextStyle.short, placeholder='เช่น สีแดง', required=True)

    async def on_submit(self, interaction: discord.Interaction):
        color_data = get_color_data(self.color_name.value)
        if not color_data:
            return await interaction.response.send_message("❌ กรุณาระบุสีให้ถูกต้อง: สีแดง, สีเหลือง, สีน้ำเงิน, หรือ สีดำ", ephemeral=True)

        lotto_id = ''.join(random.choices(string.digits, k=5))
        lottery_db[lotto_id] = {"amount": self.amount.value, "color": self.color_name.value, "user": interaction.user.name}

        # Embed สวยๆ สำหรับแอดมิน
        embed = discord.Embed(title="💰 มีรายการเติมเงินใหม่!", color=discord.Color.green())
        embed.add_field(name="👤 ผู้เล่น", value=interaction.user.mention, inline=False)
        embed.add_field(name="🔗 ลิงก์ซอง", value=self.link.value, inline=False)
        embed.add_field(name="💵 จำนวนเงิน", value=f"{self.amount.value} บาท", inline=True)
        embed.add_field(name="🎨 สีที่เลือก", value=self.color_name.value, inline=True)
        embed.add_field(name="🎫 รหัสหวย", value=f"**{lotto_id}**", inline=True)
        
        # ส่งเข้าห้อง Log
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel: await log_channel.send(embed=embed)
        
        # ส่ง DM หาแอดมิน
        admin = await bot.fetch_user(ADMIN_ID)
        if admin: await admin.send(embed=embed)

        await interaction.response.send_message(f"✅ ส่งข้อมูลสำเร็จ! รหัสหวยของคุณคือ: **{lotto_id}**", ephemeral=True)

# --- MODAL: ตรวจรางวัล ---
class CheckRewardModal(Modal, title='🎰 ตรวจสอบรางวัล'):
    lotto_id = TextInput(label='รหัสหวย 5 หลัก', placeholder='เช่น 12345', min_length=5, max_length=5, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        if self.lotto_id.value not in lottery_db:
            return await interaction.response.send_message("❌ ไม่พบรหัสนี้ในระบบ", ephemeral=True)

        data = lottery_db[self.lotto_id.value]
        colors = ["สีแดง", "สีเหลือง", "สีน้ำเงิน", "สีดำ"]
        result = random.choices(colors, weights=[50, 30, 15, 5])[0]
        
        is_win = (data['color'] == result)
        embed = discord.Embed(title="🎰 ผลการออกรางวัล", color=discord.Color.gold() if is_win else discord.Color.red())
        embed.description = f"**{result}** ออกแล้ว!"
        embed.add_field(name="สถานะ", value="✅ ถูกรางวัล" if is_win else "❌ ไม่ถูกรางวัล", inline=False)
        
        if is_win:
            embed.add_field(name="ขั้นตอนรับเงิน", value=f"กดปุ่มติดต่อแอดมิน <@{ADMIN_ID}>", inline=False)
        
        del lottery_db[self.lotto_id.value]
        await interaction.response.send_message(embed=embed, ephemeral=True)

# --- UI หลัก ---
class LotteryView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='เติมเงิน / ซื้อหวย', style=discord.ButtonStyle.green, emoji='💰')
    async def topup(self, i, b): await i.response.send_modal(TopupModal())

    @discord.ui.button(label='ดูรางวัล', style=discord.ButtonStyle.primary, emoji='🎲')
    async def check(self, i, b): await i.response.send_modal(CheckRewardModal())

    @discord.ui.button(label='ติดต่อรับเงิน', style=discord.ButtonStyle.danger, emoji='📱')
    async def contact(self, i, b): await i.response.send_message(f"ติดต่อรับเงินที่นี่: <@{ADMIN_ID}>", ephemeral=False)

@bot.command()
async def หวย(ctx):
    embed = discord.Embed(
        title="🎰 หวยสีนำโชค [Lottery System]",
        description="🔴 โดนแดก | 🟡 x1 | 🔵 x2 | ⚫ x10\n\nเลือกสีที่ชอบ แล้วเติมเงินเพื่อเสี่ยงโชค!",
        color=discord.Color.purple()
    )
    embed.set_footer(text="ระบบบอร์ดหวยอัตโนมัติ")
    await ctx.send(embed=embed, view=LotteryView())

OWNER_ID = 1367755286839955528 
ROLE_STAFF_ID = 1499551551545675787 # <-- อย่าลืมเปลี่ยน ID ยศแอดมินธนาคารที่นี่

# ลิงก์ GIF ที่อัปเดตล่าสุด
MY_GIF_URL = "https://cdn.discordapp.com/attachments/1469995624027127911/1475110969209393324/standard_1.gif?ex=699c4ba5&is=699afa25&hm=e1a249237d6005a292b90cef4b0aba4429aaf2144a741f629cb0ea2319334637"

# ตัวแปรเก็บยอดเงินในระบบ
user_bank = {}

# --- [ ระบบตรวจสอบสิทธิ์และแบนถาวร ] ---
async def check_staff_and_ban(ctx):
    staff_role = ctx.guild.get_role(ROLE_STAFF_ID)
    if ctx.author.id != OWNER_ID and (staff_role not in ctx.author.roles):
        try:
            await ctx.guild.ban(ctx.author, reason="พยายามใช้คำสั่งแอดมินโดยไม่มีสิทธิ์ (System Auto Ban)")
            await ctx.send(f"🔨 **BAN:** {ctx.author.mention} ถูกแบนถาวรฐานมั่วระบบแอดมิน")
        except: pass
        return False
    return True

# --- [ ส่วนของ UI บอร์ดธนาคาร ] ---
class AdminConfirmView(discord.ui.View):
    def __init__(self, target_member, amount):
        super().__init__(timeout=None)
        self.target_member = target_member
        self.amount = amount

    @discord.ui.button(label="✅ ยืนยันได้รับเงิน", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_bank[self.target_member.id] = user_bank.get(self.target_member.id, 0) + self.amount
        try: await self.target_member.send(f"✅ ยอดเงินจำนวน **{self.amount:,} บาท** ถูกเติมเข้าบัญชีเรียบร้อย!")
        except: pass
        await interaction.response.edit_message(content=f"🟢 เติมเงินให้ {self.target_member.name} สำเร็จ!", view=None)

class DepositModal(discord.ui.Modal, title='📥 ฝากเงินเข้าระบบ'):
    amount = discord.ui.TextInput(label='จำนวนเงิน (บาท)', placeholder='ใส่ตัวเลข...')
    link = discord.ui.TextInput(label='ลิงก์ซองของขวัญ', placeholder='https://gift.truemoney.com/...')
    async def on_submit(self, interaction: discord.Interaction):
        try: amt = int(self.amount.value)
        except: return await interaction.response.send_message("❌ ใส่เฉพาะตัวเลขเท่านั้น!", ephemeral=True)
        owner = await interaction.client.fetch_user(OWNER_ID)
        view = AdminConfirmView(interaction.user, amt)
        embed = discord.Embed(title="📥 มีรายการฝากใหม่", color=0x2ecc71)
        embed.add_field(name="คนฝาก:", value=interaction.user.mention)
        embed.add_field(name="ยอด:", value=f"**{amt:,} บาท**")
        embed.add_field(name="ลิงก์:", value=f"[คลิกรับซอง]({self.link.value})")
        await owner.send(embed=embed, view=view)
        await interaction.response.send_message("✅ ส่งเรื่องให้ธนาคารแล้ว รอตรวจสอบสักครู่ครับ", ephemeral=True)

class WithdrawModal(discord.ui.Modal, title='📤 ถอนเงินออกจากระบบ'):
    amount = discord.ui.TextInput(label='จำนวนที่ถอน', placeholder='ใส่ตัวเลข...')
    phone = discord.ui.TextInput(label='เบอร์รับเงิน (TrueMoney)', min_length=10, max_length=10)
    async def on_submit(self, interaction: discord.Interaction):
        uid = interaction.user.id
        try: amt = int(self.amount.value)
        except: return await interaction.response.send_message("❌ ใส่ตัวเลขให้ถูกต้อง!", ephemeral=True)
        if amt > user_bank.get(uid, 0): return await interaction.response.send_message("❌ ยอดเงินไม่พอถอน!", ephemeral=True)
        user_bank[uid] -= amt
        owner = await interaction.client.fetch_user(OWNER_ID)
        await owner.send(f"📤 **แจ้งถอน**\nจาก: {interaction.user.mention}\nยอด: **{amt:,}**\nเบอร์: `{self.phone.value}`")
        await interaction.response.send_message("✅ ส่งเรื่องถอนแล้ว รอเงินเข้าใน 1-2 วันครับ", ephemeral=True)

class BankView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="💰 เช็คยอด", style=discord.ButtonStyle.secondary, custom_id="b1")
    async def c(self, interaction, b): await interaction.response.send_message(f"💳 ยอดเงินคงเหลือของคุณ: `{user_bank.get(interaction.user.id, 0):,}` บาท", ephemeral=True)
    @discord.ui.button(label="📥 ฝากเงิน", style=discord.ButtonStyle.success, custom_id="b2")
    async def d(self, interaction, b): await interaction.response.send_modal(DepositModal())
    @discord.ui.button(label="📤 ถอนเงิน", style=discord.ButtonStyle.danger, custom_id="b3")
    async def w(self, interaction, b): await interaction.response.send_modal(WithdrawModal())

# --- [ ตัวบอทหลัก ] ---
class Look175Bot(commands.Bot):
    def __init__(self): super().__init__(command_prefix="!", intents=discord.Intents.all())
    async def setup_hook(self): self.add_view(BankView())

bot = Look175Bot()

@bot.event
async def on_ready():
    print(f'✅ {bot.user.name} ออนไลน์แล้ว! (เวอร์ชั่นอัปเดต 22-02-2026)')

# --- [ รวมคำสั่งทั้งหมด ] ---

# 1. คำสั่งบวกยอดเงิน (อัปเดตตามที่สั่ง: !gh [ID] [จำนวน])
@bot.command(name="gh")
async def gh(ctx, member: discord.Member, amount: int):
    if not await check_staff_and_ban(ctx): return
    user_bank[member.id] = user_bank.get(member.id, 0) + amount # บวกยอดเงิน
    await ctx.send(f"✅ บวกยอดเงินให้ {member.mention} จำนวน **{amount:,} บาท** เรียบร้อย!")

# 2. คำสั่งส่งซองคืนลูกค้า (!ghk [ID] [ลิงก์])
@bot.command(name="ghk")
async def ghk(ctx, user_id: int, link: str):
    if not await check_staff_and_ban(ctx): return
    try:
        target = await bot.fetch_user(user_id)
        embed = discord.Embed(title="🏦 LOOK 175 BANK - แจ้งโอนเงิน", color=0x3498db)
        embed.description = f"นี่คือเงินที่คุณได้ถอนครับ กรุณากดที่ซองเพื่อรับเงิน\n\n🔗 **ลิงก์:** {link}"
        embed.set_image(url=MY_GIF_URL)
        await target.send(embed=embed)
        await ctx.send(f"✅ ส่งซองเงินคืนให้ <@{user_id}> เรียบร้อยครับ")
    except: await ctx.send("❌ ส่งไม่สำเร็จ (ID ผิดหรือปิด DM)")

# 3. คำสั่งส่งข้อความลับเข้า DM (!f [ID] [ข้อความ])
@bot.command(name="f")
async def f(ctx, target_id: int, *, msg: str):
    if not await check_staff_and_ban(ctx): return
    try:
        target = await bot.fetch_user(target_id)
        embed = discord.Embed(title="📨 มีข้อความลับส่งถึงคุณ", description=f"```{msg}```", color=0x2f3136)
        embed.set_footer(text="ส่งแบบนิรนามผ่านระบบ Look 175")
        await target.send(embed=embed)
        await ctx.send(f"✅ ส่งข้อความลับไปหา <@{target_id}> แล้ว", delete_after=3)
        await ctx.message.delete()
    except: await ctx.send("❌ ส่งไม่ได้", delete_after=3)

# 4. คำสั่งเปิดบอร์ดธนาคาร (!nk)
@bot.command(name="nk")
@commands.has_permissions(administrator=True)
async def nk(ctx):
    embed = discord.Embed(
        title="🏦 LOOK 175 BANK SYSTEM", 
        description="**ระบบธนาคารอัตโนมัติ**\nถอนเงินรอโอนกลับภายใน 1-2 วันครับ", 
        color=0x3498db
    )
    embed.set_image(url=MY_GIF_URL)
    await ctx.send(embed=embed, view=BankView())
    await ctx.message.delete()

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user.name}")

@bot.tree.command(name="k", description="ส่งข้อความผ่านบอทแบบไม่ระบุตัวตน")
@app_commands.describe(
    channel_id="ID ของช่องที่ต้องการให้บอทส่งข้อความไป",
    message="ข้อความหรือลิงก์ที่ต้องการส่ง"
)
async def k(interaction: discord.Interaction, channel_id: str, message: str):
    if not channel_id.isdigit():
        await interaction.response.send_message("❌ ID ช่องต้องเป็นตัวเลขเท่านั้น", ephemeral=True)
        return

    try:
        target_channel = bot.get_channel(int(channel_id))
        if target_channel is None:
            target_channel = await bot.fetch_channel(int(channel_id))
            
        await target_channel.send(message)
        await interaction.response.send_message("✅ ส่งข้อความเรียบร้อยแล้ว", ephemeral=True)
    except Exception:
        await interaction.response.send_message("❌ ไม่สามารถส่งข้อความได้ กรุณาตรวจสอบ ID ช่องและสิทธิ์ของบอท", ephemeral=True)

import discord
from discord.ext import commands
import datetime

# ตั้งค่า Intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 🛑 ใส่ User ID ของคุณ (ที่เป็นแอดมินรับแจ้งเตือน) ตรงนี้
OWNER_ID = 1367755286839955528 

# --- ปุ่มยกเลิกห้อง (สำหรับผู้ใช้) ---
class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="❌ ปิดห้อง / ยกเลิก", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("❌ กำลังปิดและลบห้องนี้...", ephemeral=True)
        try:
            # สั่งลบช่องแชททันทีโดยไม่ต้องรอ
            await interaction.channel.delete(reason="ผู้ใช้กดปิดห้องสนทนา")
        except:
            pass

# --- ปุ่มหน้าต่างติดต่อแอดมิน (หลัก) ---
class ContactView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📞 ติดต่อแอดมิน", style=discord.ButtonStyle.success, custom_id="contact_admin_btn", emoji="🎫")
    async def contact_admin(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user

        # ป้องกันการสร้างห้องซ้ำ (เช็คว่ามีห้องชื่อ ticket-ชื่อผู้ใช้ อยู่แล้วหรือยัง)
        existing_channel = discord.utils.get(guild.text_channels, name=f"ticket-{user.name.lower()}")
        if existing_channel:
            await interaction.response.send_message(f"❌ คุณมีห้องสนทนาเปิดอยู่แล้ว: {existing_channel.mention}", ephemeral=True)
            return

        # ดึงข้อมูล Owner (แอดมิน)
        owner = guild.get_member(OWNER_ID)
        
        # ตั้งค่าสิทธิ์การมองเห็นช่อง (เห็นเฉพาะ แอดมิน, ผู้ใช้ที่กด, และตัวบอท)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True)
        }
        
        if owner:
            overwrites[owner] = discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True)

        try:
            # สร้างห้องใหม่ในหมวดหมู่เดิม หรือสร้างใหม่ด้านบนสุด
            category = interaction.channel.category
            ticket_channel = await guild.create_text_channel(
                name=f"ticket-{user.name}",
                category=category,
                overwrites=overwrites,
                topic=f"Ticket ของ {user} (ID: {user.id})"
            )

            # ส่งข้อความต้อนรับในห้อง Ticket พร้อมปุ่มยกเลิก
            embed = discord.Embed(
                title="🎫 ระบบติดต่อแอดมิน",
                description=f"สวัสดีคุณ {user.mention} กรุณาพิมพ์ปัญหาหรือข้อสงสัยของคุณไว้ได้เลย เดี๋ยวแอดมินจะรีบเข้ามาตอบครับ",
                color=discord.Color.blue()
            )
            await ticket_channel.send(content=f"{user.mention} <@!{OWNER_ID}>", embed=embed, view=CloseTicketView())

            # แจ้งเตือนแอดมินส่วนตัว (DM)
            if owner:
                try:
                    dm_embed = discord.Embed(
                        title="🔔 มีคำขอติดต่อแอดมินใหม่!",
                        description=f"ผู้ใช้: **{user}** (`{user.id}`)\nได้เปิดห้องสนทนาใหม่: {ticket_channel.mention}",
                        color=discord.Color.green()
                    )
                    await owner.send(embed=dm_embed)
                except:
                    pass # เผื่อกรณีแอดมินปิดรับ DM

            # ตอบกลับผู้ใช้ว่าสร้างห้องสำเร็จ
            await interaction.response.send_message(f"✅ สร้างห้องส่วนตัวให้เรียบร้อยแล้ว: {ticket_channel.mention}", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"❌ เกิดข้อผิดพลาดในการสร้างห้อง: {e}", ephemeral=True)

# --- คำสั่ง !c สำหรับเรียกหน้าต่างติดต่อ ---
@bot.command()
async def c(ctx):
    # ลบข้อความคำสั่ง !c ทิ้งเพื่อความสะอาด
    try:
        await ctx.message.delete()
    except:
        pass

    embed = discord.Embed(
        title="💬 ศูนย์ช่วยเหลือและติดต่อแอดมิน",
        description="หากต้องการติดต่อทีมงานหรือแจ้งปัญหาการใช้งาน\nกรุณากดปุ่ม **'📞 ติดต่อแอดมิน'** ด้านล่างเพื่อเปิดห้องสนทนาส่วนตัว",
        color=discord.Color.gold()
    )
    embed.set_footer(text="Ice Express Support System")
    
    await ctx.send(embed=embed, view=ContactView())

@bot.event
async def on_ready():
    # ลงทะเบียน View แบบ Persistent เพื่อให้ปุ่มยังใช้งานได้แม้รีสตาร์ทบอท
    bot.add_view(ContactView())
    bot.add_view(CloseTicketView())
    print(f"✅ บอทออนไลน์แล้วในชื่อ: {bot.user.name}")

bot.run(“-”)




