import logging
import datetime
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token
TOKEN = "7877721444:AAG-VKYsQrwRdIgzF9iMEFUu1CZ7QfAfA7Q"

# Admin user IDs (Replace with your Telegram user ID)
ADMIN_IDS = [5168899073]  # Replace with your actual Telegram user ID
ADMIN_GROUP_ID = None  # If you want to forward screenshots to a group instead

# UPI ID for payments
UPI_ID = "https://razorpay.me/@rentsub?amount=qGD3mshDEPeNHiCGLSBqZg%3D%3D"  # Replace with your actual UPI ID

# File to store user data
USER_DATA_FILE = "user_data.json"

# Subscription plans - Fixed the structure to include 'name' field
SUBSCRIPTION_PLANS = [
    {"id": "plan_3", "name": "Jio Hotstar", "price": "₹19", "days": 3},
    {"id": "plan_7", "name": "Netflix", "price": "₹49", "days": 7},
    {"id": "plan_15", "name": "Zee5", "price": "₹99", "days": 15},
    {"id": "plan_30", "name": "SonyLiv", "price": "₹199", "days": 30},
]

# Load user data from file
def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as file:
            return json.load(file)
    return {}

# Save user data to file
def save_user_data(data):
    with open(USER_DATA_FILE, "w") as file:
        json.dump(data, file)

# User data structure
user_data = load_user_data()
pending_screenshots = {}

# Check if user has active subscription
def is_subscribed(user_id):
    if str(user_id) in user_data:
        end_date = datetime.datetime.fromisoformat(user_data[str(user_id)]["end_date"])
        return end_date > datetime.datetime.now()
    return False

# Get user subscription info
def get_subscription_info(user_id):
    if str(user_id) in user_data:
        return user_data[str(user_id)]
    return None

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message when the command /start is issued."""
    keyboard = []
    for plan in SUBSCRIPTION_PLANS:
        keyboard.append([InlineKeyboardButton(f"{plan['name']} - {plan['price']}", callback_data=f"buy_{plan['id']}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👋 Welcome to RentSub Bot! 🤖\n\n"
        "Get access to exclusive content with our subscription plans.\n\n"
        "Choose a plan below to subscribe:",
        reply_markup=reply_markup
    )

async def plans_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show all subscription plans."""
    keyboard = []
    for plan in SUBSCRIPTION_PLANS:
        keyboard.append([InlineKeyboardButton(f"{plan['name']} - {plan['price']}", callback_data=f"buy_{plan['id']}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📋 Available Subscription Plans:\n\n" + 
        "\n".join([f"• {plan['name']} - {plan['price']}" for plan in SUBSCRIPTION_PLANS]) +
        "\n\nClick on a plan to subscribe:",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help message."""
    await update.message.reply_text(
        "🔍 How to use RentSub Bot:\n\n"
        "1. Use /plans to view all subscription plans\n"
        "2. Click on a plan to subscribe\n"
        "3. Make payment to the provided UPI ID\n"
        "4. Send screenshot of payment\n"
        "5. Admin will verify and grant access\n\n"
        "To check your subscription status: /status\n\n"
        "Need more help? Contact @admin_username"  # Replace with actual admin username
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user's subscription status."""
    user_id = str(update.effective_user.id)
    
    if user_id in user_data:
        end_date = datetime.datetime.fromisoformat(user_data[user_id]["end_date"])
        is_active = end_date > datetime.datetime.now()
        
        if is_active:
            days_left = (end_date - datetime.datetime.now()).days
            await update.message.reply_text(
                f"✅ Your subscription is active!\n\n"
                f"Plan: {user_data[user_id]['plan_name']}\n"
                f"Expires on: {end_date.strftime('%d %b %Y')}\n"
                f"Days remaining: {days_left}"
            )
        else:
            await update.message.reply_text(
                "❌ Your subscription has expired.\n\n"
                "Use /plans to subscribe again."
            )
    else:
        await update.message.reply_text(
            "❌ You don't have an active subscription.\n\n"
            "Use /plans to subscribe."
        )

async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to list all active users."""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ This command is only for admins.")
        return
    
    active_users = []
    total_users = 0
    
    for uid, data in user_data.items():
        total_users += 1
        end_date = datetime.datetime.fromisoformat(data["end_date"])
        
        if end_date > datetime.datetime.now():
            username = data.get('username', 'Unknown')
            active_users.append(f"@{username} - {data['plan_name']} - Expires: {end_date.strftime('%d %b %Y')}")
    
    if active_users:
        await update.message.reply_text(
            f"📊 Active Users: {len(active_users)}/{total_users}\n\n" + 
            "\n".join(active_users)
        )
    else:
        await update.message.reply_text("No active users found.")

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to broadcast a message to all users."""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ This command is only for admins.")
        return
    
    # Check if there's a message to broadcast
    if not context.args:
        await update.message.reply_text(
            "Please provide a message to broadcast.\n\n"
            "Usage: /broadcast Your message here"
        )
        return
    
    broadcast_message = " ".join(context.args)
    sent_count = 0
    
    # Send message to all users
    for uid in user_data:
        try:
            await context.bot.send_message(
                chat_id=int(uid),
                text=f"📢 ANNOUNCEMENT 📢\n\n{broadcast_message}\n\n- Admin"
            )
            sent_count += 1
        except Exception as e:
            logger.error(f"Failed to send broadcast to {uid}: {e}")
    
    await update.message.reply_text(f"✅ Broadcast sent to {sent_count} users.")

async def access_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to give access to a user."""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ This command is only for admins.")
        return
    
    # Check for correct command format
    if len(context.args) != 2:
        await update.message.reply_text(
            "❌ Incorrect format.\n\n"
            "Usage: /access @username days"
        )
        return
    
    username = context.args[0]
    if username.startswith('@'):
        username = username[1:]  # Remove @ symbol if present
    
    try:
        days = int(context.args[1])
        if days <= 0:
            await update.message.reply_text("❌ Days must be a positive number.")
            return
    except ValueError:
        await update.message.reply_text("❌ Days must be a number.")
        return
    
    # Find user by username
    target_user_id = None
    plan_name = f"{days} Days"
    
    for uid, data in user_data.items():
        if data.get('username') == username:
            target_user_id = uid
            break
    
    if not target_user_id:
        # Check pending screenshots
        for uid, data in pending_screenshots.items():
            if data.get('username') == username:
                target_user_id = uid
                # Get plan details from pending screenshot data
                plan_id = data.get('plan_id')
                for plan in SUBSCRIPTION_PLANS:
                    if plan['id'] == plan_id:
                        plan_name = plan['name']
                        break
                break
        else:
            await update.message.reply_text(f"❌ User @{username} not found.")
            return
    
    # Calculate new subscription end date
    now = datetime.datetime.now()
    
    # If user already has a subscription, extend it
    if target_user_id in user_data:
        current_end = datetime.datetime.fromisoformat(user_data[target_user_id]["end_date"])
        if current_end > now:
            new_end = current_end + datetime.timedelta(days=days)
            user_data[target_user_id]["end_date"] = new_end.isoformat()
            user_data[target_user_id]["plan_name"] = f"{plan_name} (Extended)"
        else:
            new_end = now + datetime.timedelta(days=days)
            user_data[target_user_id]["end_date"] = new_end.isoformat()
            user_data[target_user_id]["plan_name"] = plan_name
    else:
        # Create new user entry
        new_end = now + datetime.timedelta(days=days)
        user_data[target_user_id] = {
            "username": username,
            "plan_name": plan_name,
            "start_date": now.isoformat(),
            "end_date": new_end.isoformat()
        }
    
    # Save user data
    save_user_data(user_data)
    
    # Inform admin
    await update.message.reply_text(f"✅ Access given to @{username} for {days} days.")
    
    # Inform user
    try:
        await context.bot.send_message(
            chat_id=int(target_user_id),
            text=f"✅ Your subscription has been activated!\n\n"
                f"Plan: {plan_name}\n"
                f"Duration: {days} days\n"
                f"Expires on: {new_end.strftime('%d %b %Y')}\n\n"
                f"Thank you for subscribing!"
        )
    except Exception as e:
        logger.error(f"Failed to notify user {target_user_id}: {e}")
        await update.message.reply_text(f"Note: Failed to notify the user.")
    
    # Clear from pending screenshots if exists
    if target_user_id in pending_screenshots:
        del pending_screenshots[target_user_id]

# Callback query handler for buttons
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses."""
    query = update.callback_query
    await query.answer()
    
    # Get the callback data
    data = query.data
    user = update.effective_user
    
    if data.startswith("buy_"):
        plan_id = data[4:]
        
        # Find the selected plan
        selected_plan = None
        for plan in SUBSCRIPTION_PLANS:
            if plan["id"] == plan_id:
                selected_plan = plan
                break
        
        if not selected_plan:
            await query.edit_message_text("❌ Plan not found. Please try again.")
            return
        
        # Store in pending screenshots
        pending_screenshots[str(user.id)] = {
            "username": user.username,
            "plan_id": plan_id,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        # Send payment instructions
        payment_text = (
            f"💳 Payment Details for {selected_plan['name']} ({selected_plan['price']})\n\n"
            f"UPI ID: `{UPI_ID}`\n\n"
            f"1. Pay {selected_plan['price']} to the UPI ID above\n"
            f"2. Take a screenshot of the payment\n"
            f"3. Send the screenshot here\n\n"
            f"Your access will be activated after verification."
        )
        
        await query.edit_message_text(text=payment_text, parse_mode="Markdown")

# Handle screenshots
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle received photos (payment screenshots)."""
    user = update.effective_user
    user_id = str(user.id)
    
    # Check if user is in pending screenshots
    if user_id not in pending_screenshots:
        await update.message.reply_text(
            "❓ I'm not expecting a screenshot from you. "
            "Please select a subscription plan first using /plans."
        )
        return
    
    plan_id = pending_screenshots[user_id]["plan_id"]
    
    # Find the selected plan
    selected_plan = None
    for plan in SUBSCRIPTION_PLANS:
        if plan["id"] == plan_id:
            selected_plan = plan
            break
    
    if not selected_plan:
        await update.message.reply_text("❌ There was an error with your plan. Please try again.")
        return
    
    # Check if user has a username
    if not user.username:
        await update.message.reply_text(
            "❌ You need to set a Telegram username to use this bot.\n\n"
            "Please set a username in your Telegram settings and try again."
        )
        return
    
    # Forward screenshot to admin or admin group
    if ADMIN_GROUP_ID:
        await update.message.forward(chat_id=ADMIN_GROUP_ID)
        
        # Send additional info to admin group
        await context.bot.send_message(
            chat_id=ADMIN_GROUP_ID,
            text=(
                f"📝 Payment Screenshot Info:\n\n"
                f"User: @{user.username} (ID: {user.id})\n"
                f"Plan: {selected_plan['name']} ({selected_plan['price']})\n"
                f"Duration: {selected_plan['days']} days\n\n"
                f"To approve: `/access @{user.username} {selected_plan['days']}`"
            ),
            parse_mode="Markdown"
        )
    else:
        # Forward to each admin individually
        for admin_id in ADMIN_IDS:
            await update.message.forward(chat_id=admin_id)
            
            # Send additional info to admin
            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    f"📝 Payment Screenshot Info:\n\n"
                    f"User: @{user.username} (ID: {user.id})\n"
                    f"Plan: {selected_plan['name']} ({selected_plan['price']})\n"
                    f"Duration: {selected_plan['days']} days\n\n"
                    f"To approve: `/access @{user.username} {selected_plan['days']}`"
                ),
                parse_mode="Markdown"
            )
    
    # Inform user
    await update.message.reply_text(
        "✅ Your payment screenshot has been submitted for verification.\n\n"
        "Please wait while an admin verifies your payment. "
        "You will receive a notification once your access is activated."
    )

# Handle normal text messages
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle normal text messages."""
    # Check if user has subscription
    user_id = update.effective_user.id
    
    if is_subscribed(user_id):
        # You can add content delivery logic here
        pass
    else:
        # Remind user to subscribe
        await update.message.reply_text(
            "You don't have an active subscription. Use /plans to subscribe."
        )

# Job for checking expiry and sending reminders
async def check_expiry(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check subscription expiry and send reminders."""
    now = datetime.datetime.now()
    tomorrow = now + datetime.timedelta(days=1)
    
    for user_id, data in user_data.items():
        end_date = datetime.datetime.fromisoformat(data["end_date"])
        
        # Check if subscription expires tomorrow
        if end_date.date() == tomorrow.date():
            try:
                await context.bot.send_message(
                    chat_id=int(user_id),
                    text=(
                        "⚠️ Subscription Expiry Reminder ⚠️\n\n"
                        f"Your {data['plan_name']} subscription will expire tomorrow.\n\n"
                        "To renew your subscription, use /plans."
                    )
                )
            except Exception as e:
                logger.error(f"Failed to send expiry reminder to {user_id}: {e}")
        
        # Check if subscription expires today
        elif end_date.date() == now.date():
            try:
                await context.bot.send_message(
                    chat_id=int(user_id),
                    text=(
                        "⚠️ Subscription Expired ⚠️\n\n"
                        f"Your {data['plan_name']} subscription has expired today.\n\n"
                        "To renew your subscription, use /plans."
                    )
                )
            except Exception as e:
                logger.error(f"Failed to send expiry notification to {user_id}: {e}")

def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("plans", plans_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("users", users_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("access", access_command))
    
    # Add callback query handler
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Add photo handler for screenshots
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    # Add text message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # Add job for checking expiry (runs every day at midnight)
    job_queue = application.job_queue
    job_queue.run_daily(check_expiry, time=datetime.time(0, 0))
    
    # Start the Bot
    application.run_polling()

if __name__ == "__main__":
    main()