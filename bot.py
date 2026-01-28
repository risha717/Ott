import os
import json
import random
import string
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# ==================== কনফিগারেশন ====================
BOT_TOKEN = "8006015641:AAHMiqhkmtvRmdLMN1Rbz2EnwsIrsGfH8qU"  # আপনার টোকেন
ADMIN_ID = 1858324638  # আপনার আইডি
VIDEO_CHANNEL_ID = -1003872857468  # চ্যানেল আইডি
CHANNEL_USERNAME = "@CineflixOfficialbd"  # চ্যানেল ইউজারনেম

# লগিং সেটআপ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== ডাটাবেজ ক্লাস ====================
class Database:
    def __init__(self):
        self.db_file = "videos.json"
        self.load()
    
    def load(self):
        try:
            with open(self.db_file, "r", encoding="utf-8") as f:
                self.data = json.load(f)
                logger.info(f"✅ ডাটাবেজ লোডেড: {len(self.data.get('videos', {}))} টি ভিডিও")
        except:
            self.data = {"videos": {}, "downloads": {}, "users": {}}
            self.save()
    
    def save(self):
        with open(self.db_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
    
    def add_video(self, message_id, caption=""):
        code = f"v_{random.randint(100000, 999999)}"
        
        self.data["videos"][code] = {
            "message_id": message_id,
            "title": caption[:100] if caption else "ভিডিও",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "views": 0
        }
        self.save()
        logger.info(f"🎬 নতুন ভিডিও যোগ করা হয়েছে: {code}")
        return code
    
    def get_video(self, code):
        return self.data["videos"].get(code)
    
    def increment_view(self, code):
        if code in self.data["videos"]:
            self.data["videos"][code]["views"] = self.data["videos"][code].get("views", 0) + 1
            self.save()

db = Database()

# ==================== বট ফাংশন ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"👤 User started: {user.id} (@{user.username})")
    
    # যদি কোড দিয়ে আসে (মিনি অ্যাপ থেকে)
    if context.args:
        code = context.args[0]
        logger.info(f"🔗 Code received: {code}")
        await handle_video_code(update, context, code)
        return
    
    # স্বাগতম মেসেজ
    await update.message.reply_text(
        f"🎬 *Cineflix Universe Pro* - এ স্বাগতম {user.first_name}!\n\n"
        "🎥 *কিভাবে দেখবেন:*\n"
        "1. আমাদের মিনি অ্যাপ ওপেন করুন\n"
        "2. যেকোনো ভিডিও সিলেক্ট করুন\n"
        "3. WATCH NOW এ ক্লিক করুন\n"
        "4. ভিডিও পেয়ে যাবেন!\n\n"
        "🔗 মিনি অ্যাপ: https://cinaflix-streaming.vercel.app\n\n"
        f"📢 চ্যানেল: {CHANNEL_USERNAME}\n"
        "🤖 বট: @Cinaflix_Streembot\n\n"
        "⚡ *সরাসরি কোড পাঠান:* `v_123456`",
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

async def handle_video_code(update: Update, context: ContextTypes.DEFAULT_TYPE, code: str):
    user = update.effective_user
    
    logger.info(f"🔄 Processing code: {code} for user: {user.id}")
    
    # চ্যানেল চেক
    try:
        member = await context.bot.get_chat_member(VIDEO_CHANNEL_ID, user.id)
        if member.status in ["left", "kicked"]:
            logger.warning(f"❌ User {user.id} not in channel")
            await ask_to_join(update, context, code)
            return
    except Exception as e:
        logger.error(f"❌ Channel check error: {e}")
        await ask_to_join(update, context, code)
        return
    
    # ভিডিও পাঠানো
    await send_video(update, context, code, user.id)

async def ask_to_join(update: Update, context: ContextTypes.DEFAULT_TYPE, code: str):
    keyboard = [
        [InlineKeyboardButton("✅ চ্যানেল জয়েন করুন", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
        [InlineKeyboardButton("🔍 জয়েন করেছি", callback_data=f"joined_{code}")]
    ]
    
    await update.message.reply_text(
        f"🔒 *কন্টেন্ট লক করা আছে!*\n\n"
        f"ভিডিও দেখতে {CHANNEL_USERNAME} চ্যানেলে জয়েন করুন।\n\n"
        f"জয়েন করার পর নিচের বাটনে ক্লিক করুন:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def send_video(update: Update, context: ContextTypes.DEFAULT_TYPE, code: str, user_id: int):
    # ভিডিও কোড চেক
    if code.startswith("v_"):
        video = db.get_video(code)
        
        if not video:
            logger.error(f"❌ Video not found: {code}")
            await update.message.reply_text("❌ ভিডিও পাওয়া যায়নি! কোডটি চেক করুন।")
            return
        
        logger.info(f"🎬 Sending video: {code} (Message ID: {video['message_id']})")
        
        try:
            # ভিডিও ফরওয়ার্ড করুন
            await context.bot.copy_message(
                chat_id=user_id,
                from_chat_id=VIDEO_CHANNEL_ID,
                message_id=video["message_id"],
                caption=f"🎬 {video['title']}\n\n✅ @Cinaflix_Streembot"
            )
            
            # ভিউ কাউন্ট বাড়ান
            db.increment_view(code)
            logger.info(f"✅ Video sent successfully: {code}")
            
        except Exception as e:
            logger.error(f"❌ Failed to send video: {e}")
            await update.message.reply_text("❌ ভিডিও পাঠানো যায়নি! অ্যাডমিনকে জানান।")
    
    elif code.startswith("d_"):
        # ডাউনলোড লিঙ্ক (এখনি লাগবে না)
        await update.message.reply_text("📥 ডাউনলোড লিঙ্ক শীঘ্রই আসবে!")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("joined_"):
        code = query.data.replace("joined_", "")
        user_id = query.from_user.id
        
        # আবার চেক করুন
        try:
            member = await context.bot.get_chat_member(VIDEO_CHANNEL_ID, user_id)
            if member.status in ["left", "kicked"]:
                await query.answer("❌ এখনও জয়েন করেননি!", show_alert=True)
                return
        except:
            await query.answer("❌ এখনও জয়েন করেননি!", show_alert=True)
            return
        
        await query.edit_message_text("✅ জয়েন ভেরিফাইড! ভিডিও পাঠানো হচ্ছে...")
        await send_video(update, context, code, user_id)

# ==================== চ্যানেল হ্যান্ডলার ====================
async def channel_post_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """চ্যানেলে নতুন ভিডিও আসলে অটোমেটিক রেজিস্টার করবে"""
    message = update.channel_post
    
    # শুধু ভিডিও/ডকুমেন্ট হ্যান্ডল করবে
    if message.video or message.document:
        code = db.add_video(message.message_id, message.caption)
        
        # অ্যাডমিনকে নোটিফাই
        try:
            await context.bot.send_message(
                ADMIN_ID,
                f"🎬 *নতুন ভিডিও!*\n\n"
                f"📝 টাইটেল: {message.caption[:50] if message.caption else 'না'}\n"
                f"🔢 কোড: `{code}`\n"
                f"⏰ সময়: {datetime.now().strftime('%H:%M')}\n\n"
                f"📋 Google Sheet এ যোগ করুন: `{code}`",
                parse_mode="Markdown"
            )
            logger.info(f"📨 Admin notified for code: {code}")
        except Exception as e:
            logger.error(f"Failed to notify admin: {e}")

# ==================== অ্যাডমিন কমান্ড ====================
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    videos_count = len(db.data.get("videos", {}))
    total_views = sum(v.get("views", 0) for v in db.data.get("videos", {}).values())
    
    stats_text = f"""
📊 *Cineflix বট স্ট্যাটস*

🎬 মোট ভিডিও: {videos_count}
👁️ মোট ভিউ: {total_views}
📢 চ্যানেল: {CHANNEL_USERNAME}
🤖 বট: @Cinaflix_Streembot

🔄 সর্বশেষ আপডেট: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
    
    await update.message.reply_text(stats_text, parse_mode="Markdown")

async def send_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """সব ইউজারকে মেসেজ পাঠানো"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    if not context.args:
        await update.message.reply_text("❌ ফরম্যাট: /sendall <message>")
        return
    
    message = " ".join(context.args)
    await update.message.reply_text(f"📢 ব্রডকাস্ট মেসেজ:\n\n{message}")

# ==================== মেইন ফাংশন ====================
def main():
    """বট শুরু করুন"""
    app = Application.builder().token(BOT_TOKEN).build()
    
    # কমান্ড হ্যান্ডলার
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("sendall", send_all))
    
    # ক্যালব্যাক হ্যান্ডলার
    app.add_handler(CallbackQueryHandler(callback_handler))
    
    # চ্যানেল পোস্ট হ্যান্ডলার
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL, channel_post_handler))
    
    # সরাসরি টেক্সট মেসেজ (কোডের জন্য)
    async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text.strip()
        if text.startswith("v_") or text.startswith("d_"):
            await handle_video_code(update, context, text)
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # বট শুরু
    print("=" * 50)
    print("🤖 Cineflix Bot Started!")
    print(f"📢 Channel: {CHANNEL_USERNAME}")
    print(f"👑 Admin: {ADMIN_ID}")
    print("✅ Bot is 100% ready!")
    print("=" * 50)
    
    app.run_polling()

if __name__ == "__main__":
    main()
