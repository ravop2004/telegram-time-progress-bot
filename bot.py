import asyncio
import logging
import os
import threading
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
import random
from flask import Flask

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== QUOTES DATABASE ====================
QUOTES = [
    "Time is the most valuable currency - spend it wisely.",
    "Don't watch the clock; do what it does. Keep going.",
    "The bad news is time flies. The good news is you're the pilot.",
    "Yesterday is history, tomorrow is a mystery, today is a gift.",
    "Each sunrise brings new opportunities; each sunset brings reflection.",
    "Time doesn't change us, it just unfolds us.",
    "The key is not to prioritize what's on your schedule, but to schedule your priorities.",
    "Lost time is never found again.",
    "The night is darkest just before the dawn.",
    "Make each day your masterpiece.",
    "Life is not about waiting for the storm to pass, but learning to dance in the rain.",
    "Just when the caterpillar thought the world was over, it became a butterfly.",
    "After every storm, there is a rainbow of hope.",
    "Life is a journey to be experienced, not a problem to be solved.",
    "Life is like the ocean - it can be calm or rough, but it's always beautiful.",
    "The best time to plant a tree was 20 years ago. The second best time is now.",
    "You are never too old to set another goal or to dream a new dream.",
    "Life begins at the end of your comfort zone.",
    "We are all diamonds in the rough, being polished by life's challenges.",
    "Bloom where you are planted.",
    "The heart that loves is always young.",
    "Happiness is not something ready-made. It comes from your own actions.",
    "Sometimes the smallest step in the right direction ends up being the biggest step of your life.",
    "Even the darkest night will end and the sun will rise.",
    "Alone we can do so little; together we can do so much.",
    "Where words fail, music speaks.",
    "Peace begins with a smile.",
    "You are braver than you believe, stronger than you seem, and smarter than you think.",
    "Every flower must grow through dirt.",
    "The most precious things in life are not things, but moments."
]

# ==================== HELPER FUNCTIONS ====================
def get_progress_bar(percentage, bar_length=20):
    """Create simple progress bar"""
    filled = int(round(bar_length * percentage / 100))
    empty = bar_length - filled
    bar = "█" * filled + "░" * empty
    return bar

def get_year_progress():
    """Calculate year progress percentage"""
    now = datetime.now()
    start = datetime(now.year, 1, 1)
    end = datetime(now.year + 1, 1, 1)
    total_seconds = (end - start).total_seconds()
    elapsed_seconds = (now - start).total_seconds()
    percentage = (elapsed_seconds / total_seconds) * 100
    return min(percentage, 100)

def get_day_progress():
    """Calculate day progress percentage"""
    now = datetime.now()
    start = datetime(now.year, now.month, now.day)
    end = start + timedelta(days=1)
    total_seconds = (end - start).total_seconds()
    elapsed_seconds = (now - start).total_seconds()
    percentage = (elapsed_seconds / total_seconds) * 100
    return min(percentage, 100)

def get_second_progress():
    """Calculate second progress within current minute"""
    now = datetime.now()
    seconds = now.second
    percentage = (seconds / 59) * 100
    return min(percentage, 100)

def get_month_info():
    """Get current month and days left"""
    now = datetime.now()
    month_name = now.strftime("%B")
    
    if now.month == 12:
        next_month = datetime(now.year + 1, 1, 1)
    else:
        next_month = datetime(now.year, now.month + 1, 1)
    
    days_in_month = (next_month - datetime(now.year, now.month, 1)).days
    days_left = days_in_month - now.day
    months_left = 12 - now.month
    
    return month_name, days_left, months_left

def get_random_quote():
    """Get a random quote based on current minute"""
    now = datetime.now()
    minute = now.minute
    quote_index = minute % len(QUOTES)
    return QUOTES[quote_index]

# ==================== MESSAGE GENERATOR ====================
def generate_progress_message():
    """Generate the complete progress message in exact format"""
    # Get all progress data
    year_progress = get_year_progress()
    day_progress = get_day_progress()
    second_progress = get_second_progress()
    month_name, days_left, months_left = get_month_info()
    quote = get_random_quote()
    
    now = datetime.now()
    
    # Generate progress bars
    year_bar = get_progress_bar(year_progress)
    day_bar = get_progress_bar(day_progress)
    second_bar = get_progress_bar(second_progress)
    
    # Format percentages (remove trailing zeros)
    year_percent = f"{year_progress:.6f}".rstrip('0').rstrip('.')
    day_percent = f"{day_progress:.6f}".rstrip('0').rstrip('.')
    second_percent = f"{second_progress:.2f}".rstrip('0').rstrip('.')
    
    # Build message in exact format - PLAIN TEXT (no Markdown)
    message = f"""⏰ LIVE TIME PROGRESS ⏰
══════════════════════

📅 YEAR {now.year} PROGRESS
{year_bar}
{year_percent}% completed

🌞 TODAY'S PROGRESS 
{day_bar}
{day_percent}% completed

⏱️ SECOND PROGRESS
{second_bar}
{second_percent}% completed

══════════════════════
🗓️ MONTH INFORMATION
├ Current Month: {month_name}
├ Days Remaining: {days_left} days
└ Months Remaining: {months_left} months

⏰ CURRENT TIME
├ Date: {now.strftime("%d %b %Y")}
├ Time: {now.strftime("%H:%M:%S")}
└ Second: {now.second}
══════════════════════
💭 QUOTE OF THE MINUTE
{quote}
══════════════════════
🔄 Updates every 5 seconds 
🤖 DevLoper :- @ravi_chad"""
    
    return message

# ==================== EDIT MESSAGE FUNCTION ====================
async def update_message_continuously(chat_id: int, message_id: int, context: CallbackContext):
    """Continuously edit the same message with updated progress"""
    while context.chat_data.get(f'is_running_{chat_id}', False):
        try:
            # Generate new message
            new_message = generate_progress_message()
            
            # Edit the existing message - PLAIN TEXT (no parse_mode)
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=new_message
                # NO parse_mode parameter - using plain text
            )
            
            # Wait for 5 seconds to avoid flood control
            await asyncio.sleep(5)
            
        except Exception as e:
            error_msg = str(e)
            
            # If message editing fails, stop the loop
            if "message to edit not found" in error_msg or "Message can't be edited" in error_msg:
                logger.info(f"Stopping updates for chat {chat_id}")
                context.chat_data[f'is_running_{chat_id}'] = False
                break
            
            # If flood control error, wait longer
            if "Flood control" in error_msg or "429" in error_msg or "Too Many Requests" in error_msg:
                logger.warning("Flood control detected, waiting 30 seconds")
                await asyncio.sleep(30)
            else:
                logger.error(f"Error: {error_msg}")
                await asyncio.sleep(10)

# ==================== BOT HANDLERS ====================
async def start(update: Update, context: CallbackContext):
    """Send welcome message"""
    user = update.effective_user
    welcome_msg = f"""👋 Welcome {user.first_name}!

I'm Live Time Progress Bot ⏳

I show real-time progress with simple bars.

Commands:
/progress - Start live updates
/stop - Stop updates
/stats - Show current stats
/help - Show help

Click /progress to begin! 🚀"""
    
    await update.message.reply_text(welcome_msg)

async def progress(update: Update, context: CallbackContext):
    """Start the live progress updates"""
    chat_id = update.effective_chat.id
    
    # Check if already running
    if context.chat_data.get(f'is_running_{chat_id}', False):
        await update.message.reply_text("⏳ Live progress is already running! Use /stop to end it.")
        return
    
    # Send initial message
    initial_msg = generate_progress_message()
    msg = await update.message.reply_text(initial_msg)
    
    # Store message ID and set running flag
    context.chat_data[f'last_msg_id_{chat_id}'] = msg.message_id
    context.chat_data[f'is_running_{chat_id}'] = True
    
    # Start the continuous update loop
    asyncio.create_task(
        update_message_continuously(
            chat_id, 
            msg.message_id, 
            context
        )
    )
    
    info_msg = """✅ Live Progress Started!

The progress is now updating every 5 seconds!

Use /stop to end updates."""
    
    await update.message.reply_text(info_msg)

async def stop(update: Update, context: CallbackContext):
    """Stop the live progress updates"""
    chat_id = update.effective_chat.id
    
    if context.chat_data.get(f'is_running_{chat_id}', False):
        context.chat_data[f'is_running_{chat_id}'] = False
        await update.message.reply_text("⏹️ Live Progress Stopped\n\nUse /progress to start again!")
    else:
        await update.message.reply_text("ℹ️ No active live progress found.\nUse /progress to start one!")

async def stats(update: Update, context: CallbackContext):
    """Show current stats once"""
    message = generate_progress_message()
    await update.message.reply_text(message)

async def help_command(update: Update, context: CallbackContext):
    """Send help message"""
    help_text = """🤖 Live Time Progress Bot Help

Commands:
/start - Welcome message
/progress - Start live updates
/stop - Stop live updates
/stats - Show current stats
/help - Show this help

Features:
• Year progress with percentage
• Day progress with percentage  
• Second progress tracking
• Month information
• Quotes change every minute
• Updates every 5 seconds

Enjoy watching time progress! ⏳"""
    
    await update.message.reply_text(help_text)

# ==================== WEB SERVER FOR RENDER ====================
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Telegram Bot is running! ⏳"

@app.route('/health')
def health():
    return "OK", 200

def run_flask():
    """Run Flask web server"""
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ==================== BOT RUN FUNCTION ====================
def run_bot():
    """Run the bot"""
    # Get Token from Environment Variable
    TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
    
    # Create Application
    application = Application.builder().token(TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("progress", progress))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("help", help_command))
    
    # Start the Bot
    print("🤖 Bot is starting...")
    print("⏳ Live Time Progress Bot")
    print("📊 Exact format matching")
    print("🔄 5-second updates")
    print("📝 Plain text mode (no Markdown)")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

# ==================== MAIN FUNCTION ====================
def main():
    """Main function to run both Flask and bot"""
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print(f"🌐 Flask server started on port {os.environ.get('PORT', 10000)}")
    
    # Run bot in main thread
    run_bot()

if __name__ == '__main__':
    main()
