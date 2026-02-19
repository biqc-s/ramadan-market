import logging
import json
import os
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import cloudinary
import cloudinary.uploader
import qrcode
from io import BytesIO

# الإعدادات (Configuration)
TOKEN = "8158433190:AAGdPs26bOZ1dvhkG4cq27xs6oOp0iW7ZYk" 
DATA_FILE = "data.json" # اسم ملف تخزين البيانات
ADMIN_IDS = [8158433190] # معرف مدير البوت
BASE_URL = "https://your-username.github.io/ramadan-market" # رابط الموقع (يجب تحديثه)

# --- إعدادات Cloudinary (لرفع الصور) ---
# استبدل هذه القيم ببيانات حسابك من Cloudinary
CLOUDINARY_CLOUD_NAME = "duyt3dzdz"
CLOUDINARY_API_KEY = "647178117181471"
CLOUDINARY_API_SECRET = "cSkbTEQocZBBtlTawfApbAgi7To"

cloudinary.config(
  cloud_name = CLOUDINARY_CLOUD_NAME,
  api_key = CLOUDINARY_API_KEY,
  api_secret = CLOUDINARY_API_SECRET
)

# إعداد نظام تسجيل الأحداث (Logging)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# حالات المحادثة (States)
(
    SELECT_ACTION, 
    # خطوات إضافة منتج
    PROD_ENTER_SHOP_ID, PROD_ENTER_NAME, PROD_ENTER_PRICE, PROD_ENTER_CAT, PROD_ENTER_IMAGE,
    # خطوات إضافة متجر
    SHOP_ENTER_ID, SHOP_ENTER_NAME, SHOP_ENTER_TAGLINE, SHOP_ENTER_PHONE,
    # خطوات استخراج الباركود
    QR_ENTER_SHOP_ID
) = range(11)

# --- دوال مساعدة للبيانات (Data Helpers) ---
def load_data():
    """تحميل البيانات من ملف JSON"""
    if not os.path.exists(DATA_FILE):
        return {"shops": {}}
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    """حفظ البيانات إلى ملف JSON"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- معالجات الأحداث (Handlers) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نقطة البداية: القائمة الرئيسية"""
    user = update.effective_user
    
    keyboard = [
        [InlineKeyboardButton("🏪 إضافة متجر جديد", callback_data='btn_add_shop')],
        [InlineKeyboardButton("➕ إضافة منتج لمتجر", callback_data='btn_add_product')],
        [InlineKeyboardButton("📱 استخراج باركود", callback_data='btn_get_qr')],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data='btn_stats')],
        [InlineKeyboardButton("❌ إلغاء", callback_data='btn_cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    msg_text = f"مرحباً {user.first_name} في لوحة التحكم 🌙\nاختر عملية:"
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(msg_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(msg_text, reply_markup=reply_markup)
        
    return SELECT_ACTION

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة أزرار القائمة الرئيسية"""
    query = update.callback_query
    await query.answer()
    choice = query.data
    
    if choice == 'btn_add_product':
        await query.edit_message_text(
            "📝 إضافة منتج جديد\n\nأدخل *معرف المتجر (Shop ID)*:\n(يمكنك إيجاده في رابط المتجر ?v=...)",
            parse_mode='Markdown'
        )
        return PROD_ENTER_SHOP_ID
    
    elif choice == 'btn_add_shop':
        await query.edit_message_text(
            "🏪 إضافة متجر جديد\n\nأدخل *معرف فريد للمتجر* (بالإنجليزي وبدون مسافات):\nمثال: `shop3` أو `umm_khalid`",
            parse_mode='Markdown'
        )
        return SHOP_ENTER_ID
        
    elif choice == 'btn_get_qr':
        await query.edit_message_text(
            "📱 استخراج QR Code\n\nأدخل *معرف المتجر (Shop ID)* الذي تريد الباركود له:",
            parse_mode='Markdown'
        )
        return QR_ENTER_SHOP_ID

    elif choice == 'btn_stats':
        data = load_data()
        shops = data.get("shops", {})
        shop_count = len(shops)
        prod_count = sum(len(s.get("products", [])) for s in shops.values())
        
        stats_msg = (
            f"📊 *إحصائيات السوق الرمضاني*\n\n"
            f"عدد المتاجر المسجلة: {shop_count}\n"
            f"إجمالي المنتجات: {prod_count}\n\n"
            f"المتاجر الحالية:\n" + 
            "\n".join([f"- {s['name']} (`{sid}`)" for sid, s in shops.items()])
        )
        
        keyboard = [[InlineKeyboardButton("🔙 عودة للقائمة", callback_data='back_to_main')]]
        await query.edit_message_text(stats_msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
        return SELECT_ACTION

    elif choice == 'btn_cancel':
        await query.edit_message_text("👋 تم الإغلاق. اكتب /start للبدء من جديد.")
        return ConversationHandler.END
    
    elif choice == 'back_to_main':
        return await start(update, context)

# --- تدفق استخراج الباركود (QR Code Flow) ---
async def qr_get_shop_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    shop_id = update.message.text.strip()
    data = load_data()
    
    if shop_id not in data.get("shops", {}):
        await update.message.reply_text("❌ متجر غير موجود. تأكد من المعرف وحاول مجدداً (أو /cancel):")
        return QR_ENTER_SHOP_ID
    
    shop_name = data['shops'][shop_id]['name']
    target_url = f"{BASE_URL}/?v={shop_id}"
    
    # Generate QR
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(target_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Send image
    bio = BytesIO()
    bio.name = f"{shop_id}_qr.png"
    img.save(bio, 'PNG')
    bio.seek(0)
    
    await update.message.reply_photo(
        photo=bio,
        caption=f"📱 *باركود متجر: {shop_name}*\n\nالرابط: {target_url}",
        parse_mode='Markdown'
    )
    return ConversationHandler.END

# --- تدفق إضافة متجر (Add Shop Flow) ---
async def shop_get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    shop_id = update.message.text.strip()
    data = load_data()
    
    # Validation
    if shop_id in data.get("shops", {}):
        await update.message.reply_text("❌ هذا المعرف مستخدم سابقاً! اختر معرفاً آخر:")
        return SHOP_ENTER_ID
    if not shop_id.isidentifier():
        await update.message.reply_text("❌ المعرف يجب أن يحتوي على أحرف إنجليزية وأرقام و _ فقط (بدون مسافات). حاول مرة أخرى:")
        return SHOP_ENTER_ID
        
    context.user_data['new_shop_id'] = shop_id
    await update.message.reply_text(f"✅ المعرف: `{shop_id}`\n\nالآن أدخل *اسم المتجر الظاهر* (مثال: مطبخ السعادة):", parse_mode='Markdown')
    return SHOP_ENTER_NAME

async def shop_get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_shop_name'] = update.message.text.strip()
    await update.message.reply_text("أدخل *وصف مختصر* للمتجر (Tagline):", parse_mode='Markdown')
    return SHOP_ENTER_TAGLINE

async def shop_get_tagline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_shop_desc'] = update.message.text.strip()
    await update.message.reply_text("أدخل *رقم الواتساب* (مع مفتاح الدولة، مثال: 9665...):", parse_mode='Markdown')
    return SHOP_ENTER_PHONE

async def shop_get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    
    # Save Shop
    data = load_data()
    sid = context.user_data['new_shop_id']
    
    data['shops'][sid] = {
        "name": context.user_data['new_shop_name'],
        "tagline": context.user_data['new_shop_desc'],
        "phone": phone,
        "categories": [],
        "products": []
    }
    save_data(data)
    
    await update.message.reply_text(
        f"🎉 *تم إنشاء المتجر بنجاح!*\n\n"
        f"👤 الاسم: {data['shops'][sid]['name']}\n"
        f"🔗 الرابط الخاص: `?v={sid}`\n\n"
        f"استخدم /start لإضافة منتجات الآن.",
        parse_mode='Markdown'
    )
    return ConversationHandler.END

# --- تدفق إضافة منتج (Add Product Flow) ---
async def prod_get_shop_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    shop_id = update.message.text.strip()
    data = load_data()
    
    if shop_id not in data.get("shops", {}):
        await update.message.reply_text("❌ متجر غير موجود. تأكد من المعرف وحاول مجدداً (أو /cancel):")
        return PROD_ENTER_SHOP_ID
    
    context.user_data['target_shop_id'] = shop_id
    await update.message.reply_text(f"✅ متجر: {data['shops'][shop_id]['name']}\n\nأدخل *اسم المنتج*:", parse_mode='Markdown')
    return PROD_ENTER_NAME

async def prod_get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['p_name'] = update.message.text
    await update.message.reply_text("أدخل *السعر* (أرقام فقط):", parse_mode='Markdown')
    return PROD_ENTER_PRICE

async def prod_get_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = float(update.message.text)
        context.user_data['p_price'] = val
        await update.message.reply_text("أدخل *التصنيف* (مثال: مقبلات، حلويات):", parse_mode='Markdown')
        return PROD_ENTER_CAT
    except:
        await update.message.reply_text("❌ الرجاء إدخال رقم صحيح.")
        return PROD_ENTER_PRICE

async def prod_get_cat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['p_cat'] = update.message.text.strip()
    
    # Ask for image
    await update.message.reply_text(
        "📷 *هل تريد إضافة صورة للمنتج؟*\n\n"
        "- أرسل الصورة الآن (Compress/Photo).\n"
        "- أو أرسل كلمة *تخطي* لعدم إضافة صورة.",
        parse_mode='Markdown'
    )
    return PROD_ENTER_IMAGE

async def prod_handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة رفع الصورة وحفظ المنتج"""
    
    image_url = ""
    
    # Check if user sent a photo or text
    if update.message.photo:
        await update.message.reply_text("⏳ جاري رفع الصورة إلى السحابة...")
        try:
            # Get largest photo
            photo = update.message.photo[-1]
            file = await context.bot.get_file(photo.file_id)
            
            # Create temp dir
            os.makedirs("temp_upload", exist_ok=True)
            temp_path = f"temp_upload/{uuid.uuid4()}.jpg"
            await file.download_to_drive(temp_path)
            
            # Upload to Cloudinary
            response = cloudinary.uploader.upload(temp_path)
            image_url = response['secure_url']
            
            # Cleanup
            os.remove(temp_path)
            
        except Exception as e:
            logger.error(f"Image upload error: {e}")
            await update.message.reply_text(f"⚠️ حدث خطأ أثناء رفع الصورة: {e}")
            image_url = ""
    
    elif update.message.text and "تخطي" in update.message.text:
        image_url = ""
    else:
        await update.message.reply_text("⚠️ الرجاء إرسال صورة أو كلمة 'تخطي'.")
        return PROD_ENTER_IMAGE

    # Final Save
    data = load_data()
    shop_id = context.user_data['target_shop_id']
    
    # Create Product
    pid = str(uuid.uuid4())[:8]
    new_prod = {
        "id": pid,
        "name": context.user_data['p_name'],
        "description": "...", 
        "price": context.user_data['p_price'],
        "image": image_url, # يستخدم رابط السحابة (Cloudinary)
        "category": context.user_data['p_cat']
    }
    
    # إضافة المنتج للقائمة
    data['shops'][shop_id]['products'].append(new_prod)
    
    # إضافة التصنيف إذا كان جديداً
    if new_prod['category'] not in data['shops'][shop_id]['categories']:
        data['shops'][shop_id]['categories'].append(new_prod['category'])
        
    save_data(data)
    
    msg_extra = "🖼️ مع صورة" if image_url else "بدون صورة"
    
    await update.message.reply_text(f"✅ تم إضافة *{new_prod['name']}* ({msg_extra}) بنجاح!", parse_mode='Markdown')
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛑 تم إلغاء العملية.")
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()
    
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECT_ACTION: [CallbackQueryHandler(menu_handler)],
            
            # Shop States
            SHOP_ENTER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, shop_get_id)],
            SHOP_ENTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, shop_get_name)],
            SHOP_ENTER_TAGLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, shop_get_tagline)],
            SHOP_ENTER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, shop_get_phone)],
            
            # Product States
            PROD_ENTER_SHOP_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, prod_get_shop_id)],
            PROD_ENTER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, prod_get_name)],
            PROD_ENTER_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, prod_get_price)],
            PROD_ENTER_CAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, prod_get_cat)],
            PROD_ENTER_IMAGE: [MessageHandler(filters.PHOTO | filters.TEXT, prod_handle_image)],

            # حالة الباركود
            QR_ENTER_SHOP_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, qr_get_shop_id)],
        },
        fallbacks=[CommandHandler('cancel', cancel), CommandHandler('start', start)]
    )
    
    app.add_handler(conv)
    print("Bot is running... (البوت يعمل الآن)")
    app.run_polling()

if __name__ == "__main__":
    main()
