import logging

import telebot
from telebot.async_telebot import AsyncTeleBot
from telebot.types import (
    Message, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    CallbackQuery, 
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent
)

from ..config import settings

bot = AsyncTeleBot(settings.bot_token)
telebot.logger.setLevel(logging.INFO)

# Custom in-memory state storage
user_states = {}

# Define states
class BotStates:
    WAITING_FOR_JIO_NAME = "waiting_for_jio_name"
    WAITING_FOR_ITEM = "waiting_for_item"

# In-memory storage for Jio orders
jio_orders = {}

@bot.message_handler(commands=["start"])
async def start(message: Message) -> None:
    """Start the bot and ask for supper jio name."""
    user_id = message.from_user.id
    
    # Set state to wait for jio name
    user_states[user_id] = BotStates.WAITING_FOR_JIO_NAME
    
    await bot.reply_to(
        message, 
        "🍽️ Welcome to Supper Jio Bot!\n\n"
        "I'll help you create and manage supper orders.\n\n"
        "What would you like to name your supper jio?"
    )

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == BotStates.WAITING_FOR_JIO_NAME)
async def handle_jio_name(message: Message) -> None:
    """Handle the jio name input and create the jio."""
    user_id = message.from_user.id
    jio_name = message.text.strip()
    
    if not jio_name:
        await bot.reply_to(message, "Please provide a valid name for your supper jio.")
        return
    
    # Create the jio order
    jio_id = len(jio_orders) + 1  # Simple ID generation
    jio_orders[jio_id] = {
        "name": jio_name,
        "creator": message.from_user.first_name,
        "creator_id": user_id,
        "items": [],
        "participants": [message.from_user.first_name],
        "created_at": message.date,
        "group_messages": []
    }
    
    # Clear the state
    user_states.pop(user_id, None)
    
    # Send confirmation
    await bot.reply_to(
        message,
        f"✅ Supper jio '{jio_name}' created successfully!\n\n"
        f"Use /add_item to add food items to your jio.\n"
        f"Use /view_jio to see the current status."
    )

@bot.message_handler(commands=["add_item"])
async def add_item_command(message: Message) -> None:
    """Start the process of adding an item to a jio."""
    user_id = message.from_user.id
    
    # Check if user has any jios
    user_jios = [jio_id for jio_id, jio in jio_orders.items() if jio["creator_id"] == user_id]
    
    if not user_jios:
        await bot.reply_to(
            message,
            "❌ You don't have any supper jios yet.\n"
            "Use /start to create your first jio!"
        )
        return
    
    # If user has multiple jios, let them choose
    if len(user_jios) > 1:
        markup = InlineKeyboardMarkup()
        for jio_id in user_jios:
            jio = jio_orders[jio_id]
            markup.add(InlineKeyboardButton(
                jio["name"], 
                callback_data=f"select_jio_{jio_id}"
            ))
        
        await bot.reply_to(
            message,
            "Choose which jio to add an item to:",
            reply_markup=markup
        )
        return
    
    # If user has only one jio, proceed directly
    jio_id = user_jios[0]
    user_states[user_id] = {
        "state": BotStates.WAITING_FOR_ITEM,
        "jio_id": jio_id
    }
    
    await bot.reply_to(
        message,
        f"What food item would you like to add to '{jio_orders[jio_id]['name']}'?"
    )

@bot.message_handler(commands=["view_jio"])
async def view_jio_command(message: Message) -> None:
    """Show the current jio status."""
    user_id = message.from_user.id
    
    # Check if user has any jios
    user_jios = [jio_id for jio_id, jio in jio_orders.items() if jio["creator_id"] == user_id]
    
    if not user_jios:
        await bot.reply_to(
            message,
            "❌ You don't have any supper jios yet.\n"
            "Use /start to create your first jio!"
        )
        return
    
    # Show all user's jios
    response = "🍽️ Your Supper Jios:\n\n"
    
    for jio_id in user_jios:
        jio = jio_orders[jio_id]
        response += f"📋 **{jio['name']}**\n"
        response += f"   👥 Participants: {len(jio['participants'])}\n"
        response += f"   🍕 Items: {len(jio['items'])}\n"
        
        if jio['items']:
            response += "   📝 Current items:\n"
            for item in jio['items']:
                response += f"      • {item['user']}: {item['item']}\n"
        
        response += "\n"
    
    await bot.reply_to(message, response, parse_mode="Markdown")

@bot.message_handler(commands=["share_jio"])
async def share_jio_command(message: Message) -> None:
    """Show instructions for sharing the jio via inline mode."""
    user_id = message.from_user.id
    
    # Check if user has any jios
    user_jios = [jio_id for jio_id, jio in jio_orders.items() if jio["creator_id"] == user_id]
    
    if not user_jios:
        await bot.reply_to(
            message,
            "❌ You don't have any supper jios yet.\n"
            "Use /start to create your first jio!"
        )
        return
    
    response = "📤 **How to share your supper jio:**\n\n"
    response += "1. In any group chat, type `@your_bot_username`\n"
    response += "2. Select your jio from the results\n"
    response += "3. The jio will be posted to the group\n"
    response += "4. Users can add orders via the inline button\n\n"
    
    response += "**Your available jios:**\n"
    for jio_id in user_jios:
        jio = jio_orders[jio_id]
        response += f"• {jio['name']}\n"
    
    await bot.reply_to(message, response, parse_mode="Markdown")

# Callback query handler for selecting jios
@bot.callback_query_handler(func=lambda call: call.data.startswith("select_jio_"))
async def handle_jio_selection(call):
    """Handle when user selects a jio from inline keyboard."""
    try:
        jio_id = int(call.data.split("_")[-1])
        user_id = call.from_user.id
        
        if jio_id not in jio_orders:
            await bot.answer_callback_query(call.id, "❌ Jio not found.")
            return
        
        jio = jio_orders[jio_id]
        
        # Set state to wait for item
        user_states[user_id] = {
            "state": BotStates.WAITING_FOR_ITEM,
            "jio_id": jio_id
        }
        
        await bot.answer_callback_query(call.id, f"Selected: {jio['name']}")
        await bot.send_message(
            call.from_user.id,
            f"What food item would you like to add to '{jio['name']}'?"
        )
        
    except Exception as e:
        logging.error(f"Error handling jio selection: {e}")
        await bot.answer_callback_query(call.id, "❌ An error occurred.")

# Inline query handler
@bot.inline_handler(func=lambda query: True)
async def inline_query_handler(inline_query):
    """Handle inline queries to show available jios."""
    try:
        logging.info(f"Received inline query: {inline_query.query}")
        logging.info(f"From user: {inline_query.from_user.id}")
        
        if not jio_orders:
            logging.info("No jios available for inline query")
            await bot.answer_inline_query(inline_query.id, [])
            return
        
        results = []
        
        for jio_id, jio in jio_orders.items():
            logging.info(f"Processing jio {jio_id}: {jio['name']}")
            
            # Create the jio summary
            summary = f"🍽️ **{jio['name']}**\n"
            summary += f"👤 Created by: {jio['creator']}\n"
            summary += f"👥 Participants: {len(jio['participants'])}\n"
            summary += f"🍕 Items: {len(jio['items'])}\n\n"
            
            if jio['items']:
                summary += "📝 **Current Orders:**\n"
                for item in jio['items']:
                    summary += f"• {item['user']}: {item['item']}\n"
            else:
                summary += "📝 No orders yet. Be the first to order!\n"
            
            # Create inline keyboard for adding orders
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton(
                "➕ Add Order", 
                callback_data=f"add_order_{jio_id}"
            ))
            
            # Create the inline result using proper Telegram types
            from telebot.types import InlineQueryResultArticle, InputTextMessageContent
            
            result = InlineQueryResultArticle(
                id=f"jio_{jio_id}",
                title=f"🍽️ {jio['name']}",
                description=f"Created by {jio['creator']} • {len(jio['items'])} items • {len(jio['participants'])} participants",
                input_message_content=InputTextMessageContent(
                    message_text=summary,
                    parse_mode="Markdown"
                ),
                reply_markup=markup
            )
            
            results.append(result)
            logging.info(f"Added result for jio {jio_id}")
        
        logging.info(f"Sending {len(results)} results for inline query")
        await bot.answer_inline_query(inline_query.id, results)
        logging.info("Inline query answered successfully")
        
    except Exception as e:
        logging.error(f"Error handling inline query: {e}")
        # Send empty results on error
        try:
            await bot.answer_inline_query(inline_query.id, [])
        except Exception as inner_e:
            logging.error(f"Failed to send empty results: {inner_e}")

# Callback query handler for adding orders from inline messages
@bot.callback_query_handler(func=lambda call: call.data.startswith("add_order_"))
async def handle_add_order_callback(call):
    """Handle when someone clicks 'Add Order' from an inline message."""
    try:
        jio_id = int(call.data.split("_")[-1])
        
        if jio_id not in jio_orders:
            await bot.answer_callback_query(call.id, "❌ Jio not found.")
            return
        
        jio = jio_orders[jio_id]
        
        # Check if this is an inline message
        if hasattr(call, 'inline_message_id') and call.inline_message_id:
            # Record this inline message for updates
            inline_entry = {"inline_message_id": call.inline_message_id}
            if inline_entry not in jio.setdefault("group_messages", []):
                jio["group_messages"].append(inline_entry)
                logging.info(f"✅ Recorded inline message for jio {jio_id}: {call.inline_message_id}")
        
        # Send instructions to the user
        await bot.answer_callback_query(
            call.id, 
            f"To add an order to '{jio['name']}', start a chat with me and use /add_item"
        )
        
        # Try to send a direct message to the user
        try:
            await bot.send_message(
                call.from_user.id,
                f"🍽️ **Add Order to '{jio['name']}'**\n\n"
                f"Please send me the food item you'd like to order.\n"
                f"Example: 'Chicken Rice' or 'Beef Noodles'",
                parse_mode="Markdown"
            )
            
            # Set state for this user
            user_states[call.from_user.id] = {
                "state": BotStates.WAITING_FOR_ITEM,
                "jio_id": jio_id
            }
            
        except Exception as e:
            logging.warning(f"Could not send DM to user {call.from_user.id}: {e}")
            await bot.answer_callback_query(
                call.id, 
                "Please start a chat with me first to add your order."
            )
        
    except Exception as e:
        logging.error(f"Error handling add order callback: {e}")
        await bot.answer_callback_query(call.id, "❌ An error occurred.")

# Function to update all group messages when jio changes
async def update_all_jio_messages(jio_id):
    """Update all group messages for a specific jio."""
    if jio_id not in jio_orders:
        return
    
    jio = jio_orders[jio_id]
    
    # Create updated summary
    summary = f"🍽️ **{jio['name']}**\n"
    summary += f"👤 Created by: {jio['creator']}\n"
    summary += f"👥 Participants: {len(jio['participants'])}\n"
    summary += f"🍕 Items: {len(jio['items'])}\n\n"
    
    if jio['items']:
        summary += "📝 **Current Orders:**\n"
        for item in jio['items']:
            summary += f"• {item['user']}: {item['item']}\n"
    else:
        summary += "📝 No orders yet. Be the first to order!\n"
    
    # Create updated markup
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(
        "➕ Add Order", 
        callback_data=f"add_order_{jio_id}"
    ))
    
    # Update all group messages
    for group_msg in jio.get("group_messages", []):
        try:
            if "inline_message_id" in group_msg:
                # Update inline message
                await bot.edit_message_text(
                    summary,
                    inline_message_id=group_msg["inline_message_id"],
                    reply_markup=markup,
                    parse_mode="Markdown"
                )
                logging.info(f"✅ Updated inline message: {group_msg['inline_message_id']}")
            elif "chat_id" in group_msg and "message_id" in group_msg:
                # Update regular group message
                await bot.edit_message_text(
                    summary,
                    chat_id=group_msg["chat_id"],
                    message_id=group_msg["message_id"],
                    reply_markup=markup,
                    parse_mode="Markdown"
                )
                logging.info(f"✅ Updated group message: {group_msg['chat_id']}:{group_msg['message_id']}")
        except Exception as e:
            logging.error(f"Failed to update group message {group_msg}: {e}")

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get("state") == BotStates.WAITING_FOR_ITEM)
async def handle_item_input(message: Message) -> None:
    """Handle when user inputs a food item."""
    user_id = message.from_user.id
    user_state = user_states.pop(user_id, None)
    
    if not user_state:
        await bot.reply_to(message, "❌ No active jio session. Use /add_item to start.")
        return
    
    jio_id = user_state["jio_id"]
    item_name = message.text.strip()
    
    if not item_name:
        await bot.reply_to(message, "Please provide a valid food item name.")
        return
    
    # Add the item to the jio
    jio = jio_orders[jio_id]
    jio["items"].append({
        "user": message.from_user.first_name,
        "item": item_name,
        "added_at": message.date
    })
    
    # Add user to participants if not already there
    if message.from_user.first_name not in jio["participants"]:
        jio["participants"].append(message.from_user.first_name)
    
    # Update all group messages
    await update_all_jio_messages(jio_id)
    
    await bot.reply_to(
        message,
        f"✅ Added '{item_name}' to '{jio['name']}'!\n\n"
        f"Current items: {len(jio['items'])}\n"
        f"Participants: {len(jio['participants'])}\n\n"
        f"📤 All group messages have been updated!"
    )

@bot.message_handler(commands=["help"])
async def help_command(message: Message) -> None:
    """Show help information."""
    help_text = """🍽️ **Supper Jio Bot - Help**

**Commands:**
• `/start` - Create a new supper jio
• `/add_item` - Add food items to your jio
• `/view_jio` - View your current jio status
• `/share_jio` - Learn how to share your jio
• `/list_jios` - List all available jios
• `/close_jio` - Close your jio
• `/debug` - Show debug information
• `/test_inline` - Test inline query functionality
• `/bot_info` - Show bot configuration and status
• `/help` - Show this help message

**How to use:**
1. Start with `/start` to create your jio
2. Add items with `/add_item`
3. Share to groups using inline mode: `@your_bot_username`
4. Users can add orders via the inline button

**Features:**
✅ Create and manage supper orders
✅ Share to multiple groups
✅ Real-time updates across all groups
✅ Track participants and items
✅ Inline mode for easy sharing"""
    
    await bot.reply_to(message, help_text, parse_mode="Markdown")

@bot.message_handler(commands=["list_jios"])
async def list_jios_command(message: Message) -> None:
    """List all available jios."""
    if not jio_orders:
        await bot.reply_to(message, "❌ No supper jios available yet.")
        return
    
    response = "🍽️ **Available Supper Jios:**\n\n"
    
    for jio_id, jio in jio_orders.items():
        response += f"📋 **{jio['name']}**\n"
        response += f"   👤 Creator: {jio['creator']}\n"
        response += f"   👥 Participants: {len(jio['participants'])}\n"
        response += f"   🍕 Items: {len(jio['items'])}\n"
        response += f"   📍 Shared in {len(jio.get('group_messages', []))} groups\n\n"
    
    await bot.reply_to(message, response, parse_mode="Markdown")

@bot.message_handler(commands=["close_jio"])
async def close_jio_command(message: Message) -> None:
    """Close a jio (only creator can close)."""
    user_id = message.from_user.id
    
    # Check if user has any jios
    user_jios = [jio_id for jio_id, jio in jio_orders.items() if jio["creator_id"] == user_id]
    
    if not user_jios:
        await bot.reply_to(
            message,
            "❌ You don't have any supper jios to close.\n"
            "Use /start to create your first jio!"
        )
        return
    
    # If user has multiple jios, let them choose
    if len(user_jios) > 1:
        markup = InlineKeyboardMarkup()
        for jio_id in user_jios:
            jio = jio_orders[jio_id]
            markup.add(InlineKeyboardButton(
                f"Close: {jio['name']}", 
                callback_data=f"close_jio_{jio_id}"
            ))
        
        await bot.reply_to(
            message,
            "Choose which jio to close:",
            reply_markup=markup
        )
        return
    
    # If user has only one jio, close it directly
    jio_id = user_jios[0]
    jio_name = jio_orders[jio_id]["name"]
    
    # Remove the jio
    del jio_orders[jio_id]
    
    await bot.reply_to(
        message,
        f"✅ Closed supper jio '{jio_name}' successfully!\n\n"
        f"All group messages will no longer be updated."
    )

# Callback handler for closing jios
@bot.callback_query_handler(func=lambda call: call.data.startswith("close_jio_"))
async def handle_close_jio_callback(call):
    """Handle when user selects a jio to close."""
    try:
        jio_id = int(call.data.split("_")[-1])
        user_id = call.from_user.id
        
        if jio_id not in jio_orders:
            await bot.answer_callback_query(call.id, "❌ Jio not found.")
            return
        
        jio = jio_orders[jio_id]
        
        # Check if user is the creator
        if jio["creator_id"] != user_id:
            await bot.answer_callback_query(call.id, "❌ Only the creator can close this jio.")
            return
        
        jio_name = jio["name"]
        
        # Remove the jio
        del jio_orders[jio_id]
        
        await bot.answer_callback_query(call.id, f"✅ Closed: {jio_name}")
        await bot.edit_message_text(
            f"✅ **Closed Supper Jio**\n\n"
            f"'{jio_name}' has been closed successfully.\n"
            f"All group messages will no longer be updated.",
            inline_message_id=call.inline_message_id,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logging.error(f"Error handling close jio callback: {e}")
        await bot.answer_callback_query(call.id, "❌ An error occurred.")

@bot.message_handler(commands=["debug"])
async def debug_command(message: Message) -> None:
    """Show debug information for troubleshooting."""
    if not jio_orders:
        await bot.reply_to(message, "❌ No supper jios available.")
        return
    
    debug_text = "🔍 **Debug Information:**\n\n"
    
    for jio_id, jio in jio_orders.items():
        debug_text += f"📋 **Jio ID: {jio_id}**\n"
        debug_text += f"   Name: {jio['name']}\n"
        debug_text += f"   Creator: {jio['creator']} (ID: {jio['creator_id']})\n"
        debug_text += f"   Items: {len(jio['items'])}\n"
        debug_text += f"   Participants: {jio['participants']}\n"
        
        group_messages = jio.get("group_messages", [])
        debug_text += f"   Group Messages: {len(group_messages)}\n"
        
        if group_messages:
            for i, gm in enumerate(group_messages):
                debug_text += f"     {i+1}. {gm}\n"
        else:
            debug_text += "     None\n"
        
        debug_text += "\n"
    
    await bot.reply_to(message, debug_text, parse_mode="Markdown")

@bot.message_handler(commands=["test_inline"])
async def test_inline_command(message: Message) -> None:
    """Test inline query functionality."""
    if not jio_orders:
        await bot.reply_to(message, "❌ No jios available to test inline mode.")
        return
    
    response = "🧪 **Inline Query Test**\n\n"
    response += f"📊 Total jios: {len(jio_orders)}\n\n"
    
    for jio_id, jio in jio_orders.items():
        response += f"📋 **{jio['name']}** (ID: {jio_id})\n"
        response += f"   👤 Creator: {jio['creator']}\n"
        response += f"   🍕 Items: {len(jio['items'])}\n"
        response += f"   👥 Participants: {len(jio['participants'])}\n"
        response += f"   📍 Group messages: {len(jio.get('group_messages', []))}\n\n"
    
    response += "**To test inline mode:**\n"
    response += "1. Go to any group chat\n"
    response += "2. Type `@your_bot_username`\n"
    response += "3. You should see the jios listed above\n"
    response += "4. Select one to post it to the group\n\n"
    
    response += "**Debug info:**\n"
    response += f"• Bot username: @{(await bot.get_me()).username}\n"
    response += f"• Inline handler: ✅ Active\n"
    response += f"• Callback handlers: ✅ Active\n"
    
    await bot.reply_to(message, response, parse_mode="Markdown")

@bot.message_handler(commands=["bot_info"])
async def bot_info_command(message: Message) -> None:
    """Show detailed bot information and configuration."""
    try:
        # Get bot information
        bot_info = await bot.get_me()
        
        response = "🤖 **Bot Information**\n\n"
        response += f"**Basic Info:**\n"
        response += f"• Name: {bot_info.first_name}\n"
        response += f"• Username: @{bot_info.username}\n"
        response += f"• ID: {bot_info.id}\n"
        response += f"• Can join groups: {'✅' if bot_info.can_join_groups else '❌'}\n"
        response += f"• Can read all group messages: {'✅' if bot_info.can_read_all_group_messages else '❌'}\n"
        response += f"• Supports inline queries: {'✅' if bot_info.supports_inline_queries else '❌'}\n\n"
        
        response += f"**Current Status:**\n"
        response += f"• Active jios: {len(jio_orders)}\n"
        response += f"• Total users with states: {len(user_states)}\n\n"
        
        response += f"**Inline Mode Test:**\n"
        response += f"1. Go to any group chat\n"
        response += f"2. Type `@{bot_info.username}`\n"
        response += f"3. You should see available jios\n\n"
        
        if not bot_info.supports_inline_queries:
            response += "⚠️ **WARNING:** Inline mode is not enabled!\n"
            response += "To enable it, message @BotFather and use /setinline\n\n"
        
        await bot.reply_to(message, response, parse_mode="Markdown")
        
    except Exception as e:
        logging.error(f"Error getting bot info: {e}")
        await bot.reply_to(message, f"❌ Error getting bot information: {e}")
