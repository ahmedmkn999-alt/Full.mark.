import os
import time
import firebase_admin
from firebase_admin import credentials, firestore
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- الإعدادات ---
BOT_TOKEN = "8602079844:AAE_aQAhyrIcO0HgOye3dhAYzQIzxwvM13c"
ADMIN_ID = 1778665778
ADMIN_USER = "@DevAhmedmo"

# بيانات المدرسين المستخرجة
DATA = {
    "اللغة العربية": {"رضا الفاروق": "https://t.me/+HEw-RmGIHm5lNmM0", "محمد صلاح": "https://t.me/+EEW-TCiIRLw3MDg8"},
    "اللغة الإنجليزية": {"مي مجدي": "https://t.me/+xhZsZARfnIg4ODg0", "شريف المصري": "https://t.me/+DOaIcPoYn29jYjhk", "عبدالحميد حامد": "https://t.me/+inb7_Vjg6fFjNDVk", "انجلشاوي": "https://t.me/+ZojKLI2COnE4MDc0"},
    "الأحياء والجيولوجيا": {"جيو ماجد": "https://t.me/+p789CzNA-Yo3YjM0", "أحمد رضوان": "https://t.me/+DW-VMrnjB8VkOTI0", "محمد أيمن": "https://t.me/+cJ7-ZzlLxoRhZmI0", "أحمد الجوهري": "https://t.me/+iRaUEqupleo5NTU0"},
    "الكيمياء": {"جون جهبذ": "https://t.me/+FLSMYhUWNvs0ODdk", "محمد عبدالجواد": "https://t.me/+u0EQ2rkZvYJkOWI0", "خالد صقر": "https://t.me/+PJuw7vinr0tmOWNk"},
    "الفيزياء": {"محمد عبدالمعبود": "https://t.me/+4LnGU3IsX_U2MTE0", "د. كيرلس": "https://t.me/+CXri0nffu1Q3MDA0", "محمود مجدي": "https://t.me/+pH5ZV-XHyHU2Yzg0"},
    "الرياضيات": {"أحمد عصام": "https://t.me/+Vv_VvBH74o00YTc0", "لطفي زهران": "https://t.me/+3sy2vCDouhU3MTdk"},
    "التاريخ والجغرافيا": {"أحمد عادل": "https://t.me/+cdjGouZC49k5MzQ0", "إبراهيم الخديوي": "https://t.me/+x6HaE2EbdSU3M2Q8", "أحمد زهران": "https://t.me/+ZUHl-AONl2JkNTU8", "جمعة السيد": "https://t.me/+JRr99BHWAIo5YjY0"},
    "اللغة الفرنسية": {"مسيو حسين الجبلاوي": "https://t.me/+4KXDU0WlAYk3NGZk"},
    "اللغة الألمانية": {"هير عبدالمنعم إسماعيل": "https://t.me/+g3iCkdOC5rdiYjc8"}
}

# --- ربط Firebase ---
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_ref = db.collection('users').document(str(user.id))
    if not user_ref.get().exists:
        user_ref.set({'username': user.username, 'is_subscribed': False, 'trial_used': False, 'trial_expiry': 0})

    text = f"🔥 *أهلاً بك في بوت FULL MARK* 🔥\n\nيا {user.first_name}، منصتك التعليمية المتكاملة لدرجة الـ Full Mark."
    keyboard = [[InlineKeyboardButton("دخول المنصة ➡️", callback_data="main_menu")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    user_data = db.collection('users').document(str(user_id)).get().to_dict()
    
    is_active = user_data.get('is_subscribed') or (time.time() < user_data.get('trial_expiry', 0))

    if is_active:
        keyboard = []
        subjects = list(DATA.keys())
        for i in range(0, len(subjects), 2):
            row = [InlineKeyboardButton(subjects[i], callback_data=f"sub_{subjects[i]}")]
            if i+1 < len(subjects): row.append(InlineKeyboardButton(subjects[i+1], callback_data=f"sub_{subjects[i+1]}"))
            keyboard.append(row)
        await query.edit_message_text("📚 *اختر المادة:*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        text = "⚠️ *أنت غير مشترك حالياً!*\nفعل التجربة (30 دقيقة) أو تواصل مع الأدمن."
        keyboard = [
            [InlineKeyboardButton("تفعيل التجربة (30 دقيقة) ⏱️", callback_data="activate_trial")],
            [InlineKeyboardButton("شراء اشتراك 💳", url=f"https://t.me/{ADMIN_USER[1:]}")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def activate_trial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_ref = db.collection('users').document(str(query.from_user.id))
    if user_ref.get().to_dict().get('trial_used'):
        await query.answer("خلصت تجربتك! ❌", show_alert=True)
    else:
        user_ref.update({'trial_used': True, 'trial_expiry': time.time() + 1800})
        await query.answer("تم تفعيل 30 دقيقة! ✅", show_alert=True)
        await main_menu(update, context)

async def show_teachers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    subject = query.data.replace("sub_", "")
    keyboard = [[InlineKeyboardButton(f"👨‍🏫 {n}", url=l)] for n, l in DATA[subject].items()]
    keyboard.append([InlineKeyboardButton("⬅️ عودة", callback_data="main_menu")])
    await query.edit_message_text(f"🎯 مدرسين {subject}:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(main_menu, pattern="main_menu"))
    app.add_handler(CallbackQueryHandler(activate_trial, pattern="activate_trial"))
    app.add_handler(CallbackQueryHandler(show_teachers, pattern="sub_"))
    app.run_polling()

if __name__ == "__main__": main()
