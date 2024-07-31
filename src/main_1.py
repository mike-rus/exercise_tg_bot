import os
import sys
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from classes.challenge import Challenge
from classes.exercise import Exercise
from classes.chat import Chat
from classes.bot_cmd import BotCommands

logger = logging.getLogger(__name__)

EXCERCISE_FOLDER = f"{os.getcwd()}/exercises/exercises"
DATA_FOLDER = f"{os.getcwd()}/data"
BOT_TOKEN_CI = os.environ.get("BOT_TOKEN_CI")
CHAT_ID = os.environ.get("CHAT_ID")
TOPIC_ID = os.environ.get("TOPIC_ID")

challenge_obj = Challenge(-1002196230372, 8, Exercise(EXCERCISE_FOLDER), DATA_FOLDER)
chat_obj = Chat()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.ERROR,
)

import datetime
async def fetch_and_process_updates(app):
    offset = None
    bot = app.bot

    while True:
        updates = await bot.get_updates(offset=offset, timeout=10, allowed_updates=[
            "message", "edited_channel_post", "callback_query", "message_reaction"
        ])  
        
        if updates:
            logger.info(f'Received {len(updates)} updates at {datetime.datetime.now()}')
        
        for update in updates:
            print(f'Processing update: {update}')
            await app.process_update(update)
            offset = update.update_id + 1

        await asyncio.sleep(1)

import asyncio
async def main():
    application = ApplicationBuilder().token(BOT_TOKEN_CI).build()
    chat_obj.add_app_instance(application)
    challenge_obj.add_app_instance(application)
    logger.error(challenge_obj.get_exercise().get_exercise())
    challenge_obj.add_chat(chat_obj)

    bot_commands = BotCommands(challenge_obj, chat_obj)

    application.add_handler(CommandHandler("init", bot_commands.init))
    application.add_handler(CommandHandler("status", bot_commands.status))
    application.add_handler(CommandHandler("change_exercises", bot_commands.change_exercises))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot_commands.handle_user_response))
    application.add_handler(CallbackQueryHandler(bot_commands.status_button, pattern='^(Cancel|Join|Ready|Stop)$'))
    application.add_handler(CallbackQueryHandler(bot_commands.change_ex_button, pattern='^(Enable|Disable)_\d+$'))
    application.add_handler(CommandHandler("start", bot_commands.start))
    application.add_handler(CommandHandler("stop", bot_commands.stop))
    application.add_handler(CommandHandler("print", bot_commands.print_exercises))
    application.add_handler(CommandHandler("start_ex", bot_commands.start_ex))
    application.add_handler(CommandHandler("stop_ex", bot_commands.stop_ex))
    application.add_handler(MessageHandler(filters.ALL, bot_commands.handle_reaction))

    await application.initialize()

    await fetch_and_process_updates(application)

if __name__ == "__main__":
    if not TOPIC_ID or not BOT_TOKEN_CI or not CHAT_ID:
        logger.error("TOPIC_ID, BOT_TOKEN_CI, and CHAT_ID should be set as environment variables")
        sys.exit(1)
    asyncio.run(main())
    sys.exit(0)
