import os
import time
import random
import string
import asyncio
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Application, CommandHandler, CallbackQueryHandler,
                           MessageHandler, ContextTypes, filters, ConversationHandler)

# ═══════════════════════════════════════════
#              الإعدادات
# ═══════════════════════════════════════════
BOT_TOKEN  = "8602079844:AAE_aQAhyrIcO0HgOye3dhAYzQIzxwvM13c"
ADMIN_ID   = 1778665778
ADMIN_USER = "@DevAhmedmo"

ENTER_CODE = 1   # حالة ConversationHandler

# ═══════════════════════════════════════════
#              بيانات المدرسين
# ═══════════════════════════════════════════
DATA = {
    "📖 اللغة العربية":       {"رضا الفاروق": "https://t.me/+HEw-RmGIHm5lNmM0", "محمد صلاح": "https://t.me/+EEW-TCiIRLw3MDg8"},
    "🌍 اللغة الإنجليزية":    {"مي مجدي": "https://t.me/+xhZsZARfnIg4ODg0", "شريف المصري": "https://t.me/+DOaIcPoYn29jYjhk", "عبدالحميد حامد": "https://t.me/+inb7_Vjg6fFjNDVk", "انجلشاوي": "https://t.me/+ZojKLI2COnE4MDc0"},
    "🧬 الأحياء والجيولوجيا": {"جيو ماجد": "https://t.me/+p789CzNA-Yo3YjM0", "أحمد رضوان": "https://t.me/+DW-VMrnjB8VkOTI0", "محمد أيمن": "https://t.me/+cJ7-ZzlLxoRhZmI0", "أحمد الجوهري": "https://t.me/+iRaUEqupleo5NTU0"},
    "⚗️ الكيمياء":            {"جون جهبذ": "https://t.me/+FLSMYhUWNvs0ODdk", "محمد عبدالجواد": "https://t.me/+u0EQ2rkZvYJkOWI0", "خالد صقر": "https://t.me/+PJuw7vinr0tmOWNk"},
    "⚡ الفيزياء":             {"محمد عبدالمعبود": "https://t.me/+4LnGU3IsX_U2MTE0", "د. كيرلس": "https://t.me/+CXri0nffu1Q3MDA0", "محمود مجدي": "https://t.me/+pH5ZV-XHyHU2Yzg0"},
    "📐 الرياضيات":            {"أحمد عصام": "https://t.me/+Vv_VvBH74o00YTc0", "لطفي زهران": "https://t.me/+3sy2vCDouhU3MTdk"},
    "🗺️ التاريخ والجغرافيا":  {"أحمد عادل": "https://t.me/+cdjGouZC49k5MzQ0", "إبراهيم الخديوي": "https://t.me/+x6HaE2EbdSU3M2Q8", "أحمد زهران": "https://t.me/+ZUHl-AONl2JkNTU8", "جمعة السيد": "https://t.me/+JRr99BHWAIo5YjY0"},
    "🇫🇷 اللغة الفرنسية":     {"مسيو حسين الجبلاوي": "https://t.me/+4KXDU0WlAYk3NGZk"},
    "🇩🇪 اللغة الألمانية":    {"هير عبدالمنعم إسماعيل": "https://t.me/+g3iCkdOC5rdiYjc8"},
}

# ═══════════════════════════════════════════
#              Firebase
# ═══════════════════════════════════════════
if not firebase_admin._apps:
    import json as _json
    _key = os.environ.get("FIREBASE_KEY")
    if _key:
        cred = credentials.Certificate(_json.loads(_key))
    else:
        cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

# ═══════════════════════════════════════════
#              Helper Functions
# ═══════════════════════════════════════════
def gen_code(length=10):
    """يولد كود عشوائي"""
    chars = string.ascii_uppercase + string.digits
    return "FM-" + "".join(random.choices(chars, k=length))

def get_user(user_id):
    return db.collection("users").document(str(user_id)).get().to_dict() or {}

def is_active(user_data):
    return user_data.get("is_subscribed") or (time.time() < user_data.get("sub_expiry", 0))

def subjects_keyboard():
    subjects = list(DATA.keys())
    keyboard = []
    for i in range(0, len(subjects), 2):
        row = [InlineKeyboardButton(subjects[i], callback_data=f"sub_{subjects[i]}")]
        if i + 1 < len(subjects):
            row.append(InlineKeyboardButton(subjects[i+1], callback_data=f"sub_{subjects[i+1]}"))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("ℹ️ حالة اشتراكي", callback_data="my_status")])
    return keyboard

# ═══════════════════════════════════════════
#              /start
# ═══════════════════════════════════════════
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user     = update.effective_user
    user_ref = db.collection("users").document(str(user.id))
    if not user_ref.get().exists:
        user_ref.set({"username": user.username, "is_subscribed": False,
                      "trial_used": False, "trial_expiry": 0, "sub_expiry": 0})

    text = (
        "╔══════════════════════════╗\n"
        "║   🏆  *FULL MARK BOT*  🏆   ║\n"
        "╚══════════════════════════╝\n\n"
        f"أهلاً بك يا *{user.first_name}* 👋\n\n"
        "🎯 منصتك التعليمية المتكاملة\n"
        "لتحقيق الدرجة النهائية في كل المواد\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "اضغط الزر أسفله للبدء ⬇️"
    )
    keyboard = [[InlineKeyboardButton("🚀 دخول المنصة", callback_data="main_menu")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# ═══════════════════════════════════════════
#              القائمة الرئيسية
# ═══════════════════════════════════════════
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try: await query.answer()
    except: pass

    user_data = get_user(query.from_user.id)

    if is_active(user_data):
        await query.edit_message_text(
            "📚 *اختر المادة اللي عايزها*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "👇 اضغط على المادة للوصول لأفضل المدرسين",
            reply_markup=InlineKeyboardMarkup(subjects_keyboard()),
            parse_mode="Markdown"
        )
    else:
        keyboard = [
            [InlineKeyboardButton("⚡ تفعيل التجربة المجانية — 30 دقيقة", callback_data="activate_trial")],
            [InlineKeyboardButton("🎟 عندي كود اشتراك",                   callback_data="enter_code")],
            [InlineKeyboardButton("💎 شراء اشتراك — تواصل مع الأدمن",    url=f"https://t.me/{ADMIN_USER[1:]}")],
        ]
        await query.edit_message_text(
            "🔒 *أنت غير مشترك حالياً*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⏱️ *تجربة مجانية* — 30 دقيقة\n"
            "🎟 *كود اشتراك* — 80 يوم وصول كامل\n"
            "💎 *اشتراك مدفوع* — تواصل مع الأدمن",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

# ═══════════════════════════════════════════
#              تفعيل التجربة
# ═══════════════════════════════════════════
async def activate_trial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query     = update.callback_query
    user_ref  = db.collection("users").document(str(query.from_user.id))
    user_data = user_ref.get().to_dict() or {}

    if user_data.get("trial_used"):
        await query.answer("❌ استخدمت التجربة من قبل!", show_alert=True)
        return

    user_ref.update({"trial_used": True, "trial_expiry": time.time() + 1800})
    await query.answer("✅ تم تفعيل 30 دقيقة مجاناً!", show_alert=True)
    try:
        await query.edit_message_text(
            "📚 *اختر المادة اللي عايزها*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "👇 اضغط على المادة للوصول لأفضل المدرسين",
            reply_markup=InlineKeyboardMarkup(subjects_keyboard()),
            parse_mode="Markdown"
        )
    except: pass

# ═══════════════════════════════════════════
#              إدخال الكود
# ═══════════════════════════════════════════
async def enter_code_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try: await query.answer()
    except: pass
    await query.edit_message_text(
        "🎟 *أدخل كود الاشتراك*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "اكتب الكود اللي اشتريته وابعته هنا 👇\n\n"
        "_مثال: FM-ABC123XYZ_",
        parse_mode="Markdown"
    )
    return ENTER_CODE

async def enter_code_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code      = update.message.text.strip().upper()
    user_id   = str(update.effective_user.id)
    code_ref  = db.collection("codes").document(code)
    code_data = code_ref.get()

    if not code_data.exists:
        keyboard = [[InlineKeyboardButton("🔄 حاول تاني", callback_data="enter_code"),
                     InlineKeyboardButton("◀️ رجوع", callback_data="main_menu")]]
        await update.message.reply_text(
            "❌ *الكود غلط أو مش موجود!*\nتأكد من الكود وحاول تاني.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    cd = code_data.to_dict()
    if cd.get("used"):
        await update.message.reply_text(
            "⛔ *الكود ده اتستخدم قبل كده!*\nتواصل مع الأدمن لو في مشكلة.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    # تفعيل الاشتراك 80 يوم
    expiry = time.time() + (80 * 24 * 3600)
    db.collection("users").document(user_id).update({
        "is_subscribed": True,
        "sub_expiry":    expiry,
    })
    code_ref.update({"used": True, "used_by": user_id, "used_at": time.time()})

    keyboard = [[InlineKeyboardButton("🚀 دخول المنصة دلوقتي", callback_data="main_menu")]]
    await update.message.reply_text(
        "🎉 *تم تفعيل اشتراكك بنجاح!*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ الكود: `{code}`\n"
        f"📅 ينتهي بعد: *80 يوم*\n\n"
        "اضغط الزر أسفله لدخول المنصة 👇",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return ConversationHandler.END

# ═══════════════════════════════════════════
#              عرض المدرسين
# ═══════════════════════════════════════════
async def show_teachers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query   = update.callback_query
    try: await query.answer()
    except: pass
    subject  = query.data.replace("sub_", "")
    teachers = DATA.get(subject, {})
    keyboard = [[InlineKeyboardButton(f"👨‍🏫 {n}", url=l)] for n, l in teachers.items()]
    keyboard.append([InlineKeyboardButton("◀️ رجوع للمواد", callback_data="main_menu")])
    await query.edit_message_text(
        f"*{subject}*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👇 اختار المدرس واشترك في قناله",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ═══════════════════════════════════════════
#              حالة الاشتراك
# ═══════════════════════════════════════════
async def my_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query     = update.callback_query
    try: await query.answer()
    except: pass
    user_data = get_user(query.from_user.id)

    if user_data.get("is_subscribed") and time.time() < user_data.get("sub_expiry", 0):
        days = int((user_data["sub_expiry"] - time.time()) / 86400)
        status = f"💎 *مشترك* — متبقي *{days} يوم*"
    elif time.time() < user_data.get("trial_expiry", 0):
        remaining = int(user_data["trial_expiry"] - time.time())
        status = f"⏱️ *تجربة نشطة* — متبقي `{remaining//60:02d}:{remaining%60:02d}`"
    else:
        status = "🔴 *غير مشترك*"

    keyboard = [
        [InlineKeyboardButton("◀️ رجوع",        callback_data="main_menu")],
        [InlineKeyboardButton("💎 شراء اشتراك", url=f"https://t.me/{ADMIN_USER[1:]}")],
    ]
    await query.edit_message_text(
        f"📊 *حالة حسابك*\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n{status}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ═══════════════════════════════════════════
#         لوحة تحكم الأدمن
# ═══════════════════════════════════════════
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    # إحصائيات سريعة
    users_count = len(db.collection("users").get())
    codes_count = len(db.collection("codes").get())
    used_codes  = len([c for c in db.collection("codes").get() if c.to_dict().get("used")])

    keyboard = [
        [InlineKeyboardButton("🎟 توليد كود واحد",      callback_data="admin_gen1")],
        [InlineKeyboardButton("🎟🎟 توليد 5 أكواد",     callback_data="admin_gen5")],
        [InlineKeyboardButton("🎟🎟🎟 توليد 10 أكواد",  callback_data="admin_gen10")],
        [InlineKeyboardButton("📋 عرض الأكواد المتاحة", callback_data="admin_list_codes")],
        [InlineKeyboardButton("👥 عدد المستخدمين",       callback_data="admin_users")],
    ]
    await update.message.reply_text(
        "👑 *لوحة تحكم الأدمن*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 المستخدمين: *{users_count}*\n"
        f"🎟 إجمالي الأكواد: *{codes_count}*\n"
        f"✅ أكواد مستخدمة: *{used_codes}*\n"
        f"🟢 أكواد متاحة: *{codes_count - used_codes}*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def admin_gen_codes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != ADMIN_ID:
        await query.answer("⛔ مش مسموح", show_alert=True)
        return
    await query.answer()

    count = {"admin_gen1": 1, "admin_gen5": 5, "admin_gen10": 10}.get(query.data, 1)
    codes = []
    for _ in range(count):
        code = gen_code()
        db.collection("codes").document(code).set({
            "used": False, "created_at": time.time(), "used_by": None
        })
        codes.append(f"`{code}`")

    await query.edit_message_text(
        f"✅ *تم توليد {count} كود بنجاح!*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        + "\n".join(codes) +
        "\n\n📅 كل كود صالح لـ *80 يوم* من تاريخ التفعيل",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ رجوع للوحة التحكم", callback_data="admin_back")]]),
        parse_mode="Markdown"
    )

async def admin_list_codes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != ADMIN_ID:
        await query.answer("⛔ مش مسموح", show_alert=True)
        return
    await query.answer()

    all_codes = db.collection("codes").where("used", "==", False).limit(20).get()
    if not all_codes:
        text = "📭 *مفيش أكواد متاحة حالياً*\nولّد أكواد جديدة من لوحة التحكم."
    else:
        lines = [f"`{c.id}`" for c in all_codes]
        text  = f"🟢 *الأكواد المتاحة ({len(lines)})*\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n" + "\n".join(lines)

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ رجوع", callback_data="admin_back")]]),
        parse_mode="Markdown"
    )

async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != ADMIN_ID:
        await query.answer("⛔ مش مسموح", show_alert=True)
        return
    await query.answer()

    all_users    = db.collection("users").get()
    active_users = [u for u in all_users if is_active(u.to_dict())]

    await query.edit_message_text(
        f"👥 *إحصائيات المستخدمين*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 إجمالي المستخدمين: *{len(all_users)}*\n"
        f"✅ مشتركين نشطين: *{len(active_users)}*",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ رجوع", callback_data="admin_back")]]),
        parse_mode="Markdown"
    )

async def admin_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🎟 توليد كود واحد",      callback_data="admin_gen1")],
        [InlineKeyboardButton("🎟🎟 توليد 5 أكواد",     callback_data="admin_gen5")],
        [InlineKeyboardButton("🎟🎟🎟 توليد 10 أكواد",  callback_data="admin_gen10")],
        [InlineKeyboardButton("📋 عرض الأكواد المتاحة", callback_data="admin_list_codes")],
        [InlineKeyboardButton("👥 عدد المستخدمين",       callback_data="admin_users")],
    ]
    await query.edit_message_text(
        "👑 *لوحة تحكم الأدمن*\n━━━━━━━━━━━━━━━━━━━━━━━━━━",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ═══════════════════════════════════════════
#              تسجيل الـ Handlers
# ═══════════════════════════════════════════
app     = Flask(__name__)
ptb_app = Application.builder().token(BOT_TOKEN).build()

code_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(enter_code_start, pattern="^enter_code$")],
    states={ENTER_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_code_receive)]},
    fallbacks=[CommandHandler("start", start)],
    per_message=False,
)

ptb_app.add_handler(CommandHandler("start",  start))
ptb_app.add_handler(CommandHandler("admin",  admin_panel))
ptb_app.add_handler(code_conv)
ptb_app.add_handler(CallbackQueryHandler(main_menu,        pattern="^main_menu$"))
ptb_app.add_handler(CallbackQueryHandler(activate_trial,   pattern="^activate_trial$"))
ptb_app.add_handler(CallbackQueryHandler(my_status,        pattern="^my_status$"))
ptb_app.add_handler(CallbackQueryHandler(show_teachers,    pattern="^sub_"))
ptb_app.add_handler(CallbackQueryHandler(admin_gen_codes,  pattern="^admin_gen"))
ptb_app.add_handler(CallbackQueryHandler(admin_list_codes, pattern="^admin_list_codes$"))
ptb_app.add_handler(CallbackQueryHandler(admin_users,      pattern="^admin_users$"))
ptb_app.add_handler(CallbackQueryHandler(admin_back,       pattern="^admin_back$"))

# ═══════════════════════════════════════════
#              Webhook
# ═══════════════════════════════════════════
_initialized = False

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    global _initialized
    data   = request.get_json(force=True)
    update = Update.de_json(data, ptb_app.bot)
    loop   = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        if not _initialized:
            loop.run_until_complete(ptb_app.initialize())
            _initialized = True
        loop.run_until_complete(ptb_app.process_update(update))
    finally:
        loop.close()
    return jsonify({"ok": True})

@app.route("/", methods=["GET"])
def index():
    return "✅ FULL MARK Bot — Running 🚀", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
