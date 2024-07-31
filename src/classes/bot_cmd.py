import os
import json
import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from classes.challenge import Challenge, ChallengeStatus
from classes.exercise import Exercise
from classes.chat import Chat
from classes.player import PlayerMode
from telegram import Update, MessageReactionUpdated
from telegram.ext import CallbackContext

logger = logging.getLogger(__name__)

USER_EXERCISE_REQUESTS = {}

class BotCommands:
    def __init__(self, challenge_obj: Challenge, chat_obj: Chat):
        self.challenge_obj = challenge_obj
        self.chat_obj = chat_obj

    async def init(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_type = update.message.chat.type
        if chat_type == 'private':        
            user_id = update.message.from_user.id
            username = update.message.from_user.username
            await self.challenge_obj.add_player(user_id, username)
        elif chat_type in ['group', 'supergroup']:
            await self.challenge_obj.restore_players()
            self.challenge_obj.set_status(ChallengeStatus.INITED)
            

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_type = update.message.chat.type
        if chat_type == 'private':
            user_id = update.message.from_user.id
            player = self.challenge_obj.get_player(user_id)
            if player:
                keyboard = [
                    [InlineKeyboardButton("Cancel", callback_data='Cancel')],
                    [InlineKeyboardButton("Join", callback_data='Join')],
                    [InlineKeyboardButton("Ready", callback_data='Ready')],
                    [InlineKeyboardButton("Stop", callback_data='Stop')],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await self.chat_obj.send_message(user_id, f"Ваш статус {player.get_status()}", reply_markup=reply_markup)
        elif chat_type in ['group', 'supergroup']:
            for player in self.challenge_obj.get_players():
                await self.chat_obj.send_message(self.challenge_obj.get_chatid(), f"Участник @{player.get_name()} {player.get_status()}")
            await update.message.reply_text('Это сообщение из группового чата.')

    async def change_exercises(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_type = update.message.chat.type
        if chat_type == 'private':
            user_id = update.message.from_user.id
            if not context.args or not context.args[0].isdigit():
                USER_EXERCISE_REQUESTS[user_id] = True
                await self.chat_obj.send_message(user_id, "Пожалуйста, введите номер упражнения, которое хотите изменить:")
                return
            exercise_num = int(context.args[0])
            await self.process_exercise_change(user_id, exercise_num)

    async def process_exercise_change(self, user_id, exercise_num):
        player = self.challenge_obj.get_player(user_id)
        if player:
            keyboard = [
                [InlineKeyboardButton("Enable", callback_data=f'Enable_{exercise_num}')],
                [InlineKeyboardButton("Disable", callback_data=f'Disable_{exercise_num}')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            exercise = self.challenge_obj.get_exercise().get_exercise(exercise_num)
            await self.chat_obj.send_message(
                user_id,
                f"{exercise['name']} {exercise['reps']} {player.get_ex_status(exercise['sha'])}",
                reply_markup=reply_markup
            )

    async def handle_user_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.message.from_user.id
        if user_id in USER_EXERCISE_REQUESTS:
            try:
                exercise_num = int(update.message.text)
                await self.process_exercise_change(user_id, exercise_num)
            except ValueError:
                await self.chat_obj.send_message(user_id, "Пожалуйста, введите действительный номер упражнения.")
            finally:
                USER_EXERCISE_REQUESTS.pop(user_id, None)
                await update.message.delete()

    async def print_exercises(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_type = update.message.chat.type
        if chat_type == 'private':
            user_id = update.message.from_user.id
            player = self.challenge_obj.get_player(user_id)
            response = "\n".join([
                f"{i+1}) {'✅' if player.get_ex_status(ex['sha']) else '❌'} {ex['name']} {ex['reps']}"
                for i, ex in enumerate(self.challenge_obj.get_exercise().get_exercise())
            ])
            await self.chat_obj.send_message(user_id, response)

    async def status_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        user_id = query.from_user.id
        player = self.challenge_obj.get_player(user_id)
        await query.answer()
        action = query.data
        if action == 'Cancel':
            await query.edit_message_text("Cancel")
        elif action == 'Join':
            await query.edit_message_text(text="Вы выбрали Join")
            player.set_status(PlayerMode.INIT)
        elif action == 'Stop':
            await query.edit_message_text(text="Вы выбрали Stop")
            player.set_status(PlayerMode.STOP)
        elif action == 'Ready':
            await query.edit_message_text(text="Вы выбрали Ready")
            player.set_status(PlayerMode.READY)

    async def change_ex_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        user_id = query.from_user.id
        player = self.challenge_obj.get_player(user_id)
        await query.answer()
        callback_data = query.data.split('_')
        action = callback_data[0]
        exercise_num = int(callback_data[1])
        if action == 'Enable':
            await query.edit_message_text(text=f"Вы выбрали Enable для упражнения {exercise_num}")
            player.set_ex_status(self.challenge_obj.get_exercise().get_exercise(exercise_num)['sha'], True)
        elif action == 'Disable':
            player.set_ex_status(self.challenge_obj.get_exercise().get_exercise(exercise_num)['sha'], False)
            await query.edit_message_text(text=f"Вы выбрали Disable для упражнения {exercise_num}")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_type = update.message.chat.type
        if chat_type == 'private':
            user_id = update.message.from_user.id
            player = self.challenge_obj.get_player(user_id)
            if player:
                await update.message.reply_text(f"Вы @{player.get_name()}, изменили статус {player.set_status(PlayerMode.READY)}")
        elif chat_type in ['group', 'supergroup']:
            force_start = 'force' in context.args
            status = await self.challenge_obj.check_players()
            if status or force_start:
                self.challenge_obj.prepare_to_start()
                self.challenge_obj.set_status(ChallengeStatus.STARTED)
                await update.message.reply_text("Challenge started!")
            else:
                await update.message.reply_text("Not all players are ready.")

    async def stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_type = update.message.chat.type
        if chat_type == 'private':
            user_id = update.message.from_user.id
            player = self.challenge_obj.get_player(user_id)
            if player:
                await update.message.reply_text(f"Вы {user_id}, ваш статус {player.get_status()}")
        elif chat_type in ['group', 'supergroup']:
            await update.message.reply_text('Это сообщение из группового чата.')


    async def start_ex(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self.challenge_obj.send_daily_exercises(None)

    async def stop_ex(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self.challenge_obj.send_daily_result(context)


    async def handle_reaction(self, update: Update, context: CallbackContext):
        print("==========1")
        if isinstance(update, MessageReactionUpdated):
            reaction = update.message_reaction
            user_id = reaction.user.id
            message_id = reaction.message_id
            new_reactions = reaction.new_reaction

            print("==========2")
            if any(emoji.emoji == "👍" for emoji in new_reactions):  # Замените на соответствующий эмодзи
                player = next(player for player in self.players if player.telegram_id == user_id)
                if player and message_id in self.sent_messages.get(user_id, []):
                    # Отметьте упражнение как выполненное
                    exercise_index = self.sent_messages[user_id].index(message_id)
                    player.mark_exercise_completed(exercise_index)

                    print(f"Player {player.get_name()} completed exercise {exercise_index + 1}")

                    # Optionally, acknowledge the reaction
                    await context.bot.send_message(chat_id=user_id, text=f"Упражнение {exercise_index + 1} отмечено как выполненное!")
