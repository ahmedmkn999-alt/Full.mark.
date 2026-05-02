import os
import time
import asyncio
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ═══════════════════════════════════════════
#              الإعدادات الأساسية
# ═══════════════════════════════════════════
BOT_TOKEN = "8602079844:AAE_aQAhyrIcO0HgOye3dhAYzQIzxwvM13c"
ADMIN_ID   = 1778665778
ADMIN_USER = "@DevAhmedmo"

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
#              ربط Firebase
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
#              Flask & PTB
# ═══════════════════════════════════════════
app     = Flask(__name__)
ptb_app = Application.builder().token(BOT_TOKEN).build()


# ────────────────────────────────────────────
# /start
# ────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_ref = db.collection("users").document(str(user.id))
    if not user_ref.get().exists:
        user_ref.set({"username": user.username, "is_subscribed": False, "trial_used": False, "trial_expiry": 0})

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
    keyboard = [[InlineKeyboardButton("🚀  دخول المنصة", callback_data="main_menu")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


# ────────────────────────────────────────────
# القائمة الرئيسية
# ────────────────────────────────────────────
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id   = query.from_user.id
    user_data = db.collection("users").document(str(user_id)).get().to_dict() or {}
    is_active = user_data.get("is_subscribed") or (time.time() < user_data.get("trial_expiry", 0))

    if is_active:
        text = (
            "📚 *اختر المادة اللي عايزها*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "👇 اضغط على المادة للوصول لأفضل المدرسين"
        )
        subjects = list(DATA.keys())
        keyboard = []
        for i in range(0, len(subjects), 2):
            row = [InlineKeyboardButton(subjects[i], callback_data=f"sub_{subjects[i]}")]
            if i + 1 < len(subjects):
                row.append(InlineKeyboardButton(subjects[i + 1], callback_data=f"sub_{subjects[i + 1]}"))
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton("ℹ️  حالة اشتراكي", callback_data="my_status")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        text = (
            "🔒 *أنت غير مشترك حالياً*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "للوصول للمحتوى اختار إحدى الخيارات:\n\n"
            "⏱️ *تجربة مجانية* — 30 دقيقة كاملة\n"
            "💎 *اشتراك كامل* — وصول غير محدود"
        )
        keyboard = [
            [InlineKeyboardButton("⚡  تفعيل التجربة المجانية — 30 دقيقة", callback_data="activate_trial")],
            [InlineKeyboardButton("💎  اشتراك كامل — تواصل مع الأدمن",    url=f"https://t.me/{ADMIN_USER[1:]}")],
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


# ────────────────────────────────────────────
# تفعيل التجربة
# ────────────────────────────────────────────
async def activate_trial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query     = update.callback_query
    user_ref  = db.collection("users").document(str(query.from_user.id))
    user_data = user_ref.get().to_dict() or {}

    if user_data.get("trial_used"):
        await query.answer("❌  استخدمت التجربة من قبل!", show_alert=True)
    else:
        user_ref.update({"trial_used": True, "trial_expiry": time.time() + 1800})
        await query.answer("✅  تم تفعيل 30 دقيقة مجاناً!", show_alert=True)
        await main_menu(update, context)


# ────────────────────────────────────────────
# عرض المدرسين
# ────────────────────────────────────────────
async def show_teachers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query   = update.callback_query
    await query.answer()
    subject  = query.data.replace("sub_", "")
    teachers = DATA.get(subject, {})

    text = (
        f"*{subject}*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👇 اختار المدرس واشترك في قناله"
    )
    keyboard = [[InlineKeyboardButton(f"👨‍🏫  {name}", url=link)] for name, link in teachers.items()]
    keyboard.append([InlineKeyboardButton("◀️  رجوع للمواد", callback_data="main_menu")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


# ────────────────────────────────────────────
# حالة الاشتراك
# ────────────────────────────────────────────
async def my_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query     = update.callback_query
    await query.answer()
    user_data = db.collection("users").document(str(query.from_user.id)).get().to_dict() or {}

    if user_data.get("is_subscribed"):
        status_text = "💎 *مشترك — وصول كامل غير محدود*"
    else:
        expiry    = user_data.get("trial_expiry", 0)
        remaining = int(expiry - time.time())
        if remaining > 0:
            mins = remaining // 60
            secs = remaining % 60
            status_text = f"⏱️ *تجربة نشطة*\nالوقت المتبقي: `{mins:02d}:{secs:02d}`"
        else:
            status_text = "🔴 *غير مشترك* — انتهت التجربة أو لم تُفعَّل"

    text = (
        "📊 *حالة حسابك*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{status_text}"
    )
    keyboard = [
        [InlineKeyboardButton("◀️  رجوع", callback_data="main_menu")],
        [InlineKeyboardButton("💎  اشتراك كامل", url=f"https://t.me/{ADMIN_USER[1:]}")],
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


# ────────────────────────────────────────────
# أمر الأدمن — تفعيل مستخدم يدوياً
# ────────────────────────────────────────────
async def admin_activate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ مش مسموح لك.")
        return
    if not context.args:
        await update.message.reply_text("الاستخدام: /activate <user_id>")
        return
    uid = context.args[0]
    db.collection("users").document(uid).update({"is_subscribed": True})
    await update.message.reply_text(f"✅ تم تفعيل اشتراك `{uid}`", parse_mode="Markdown")


# ═══════════════════════════════════════════
#              تسجيل الـ Handlers
# ═══════════════════════════════════════════
ptb_app.add_handler(CommandHandler("start",    start))
ptb_app.add_handler(CommandHandler("activate", admin_activate))
ptb_app.add_handler(CallbackQueryHandler(main_menu,      pattern="^main_menu$"))
ptb_app.add_handler(CallbackQueryHandler(activate_trial, pattern="^activate_trial$"))
ptb_app.add_handler(CallbackQueryHandler(my_status,      pattern="^my_status$"))
ptb_app.add_handler(CallbackQueryHandler(show_teachers,  pattern="^sub_"))


# ═══════════════════════════════════════════
#              Webhook Routes
# ═══════════════════════════════════════════
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    data   = request.get_json(force=True)
    update = Update.de_json(data, ptb_app.bot)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(ptb_app.initialize())
        loop.run_until_complete(ptb_app.process_update(update))
    finally:
        loop.close()
    return jsonify({"ok": True})

@app.route("/", methods=["GET"])
def index():
    return "✅ FULL MARK Bot — Running 🚀", 200


# ═══════════════════════════════════════════
#              تشغيل محلي (اختياري)
# ═══════════════════════════════════════════
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
