from classes.exercise import Exercise
from classes.player import Player, PlayerMode
from classes.chat import Chat
from enum import Enum
import re
import os
import random

from telegram.ext._utils.types import BT
from telegram.ext._jobqueue import JobQueue, Job
from telegram.ext import ApplicationBuilder, CallbackContext

import pytz
from datetime import datetime, time, timedelta

from telegram.ext import (
    ContextTypes,
)

class ChallengeStatus(Enum):
    IDLE = 'IDLE'
    INITED = 'INITED'
    STARTED = 'STARTED'
    PAUSED = 'PAUSED'
    STOPED = 'STOPED'

class Challenge():
    def __init__(self, chat_id, thread_id, exercise : Exercise, data_folder : str):
        self.chat_id = chat_id
        self.thread_id = thread_id
        self.status : ChallengeStatus = ChallengeStatus.IDLE
        self.players = []
        self.exercise : Exercise = exercise
        self.chat : Chat = Chat()
        self.data_folder = data_folder
        self.days = 7
        self.num_ex = 2
        self.num_aux = 1
        self.sent_messages = {}
    
    def get_chatid(self):
        return self.chat_id
    
    def get_status(self) -> ChallengeStatus:
        return self.status
    
    def set_status(self, status : ChallengeStatus):
        self.status = status
    
    def prepare_to_start(self):
        for player in self.players:
            if player.get_status() == PlayerMode.INIT:
                player.set_status(PlayerMode.STOP)
           
    async def add_player(self, telegram_id, name = None) -> Player:
        player = self.get_player(telegram_id)
        if player is None:
            player = Player(telegram_id, name, self.data_folder)
            self.players.append(player)
            await self.chat.send_message(telegram_id, f"You have joined the Challenge #{self.chat_id}", 3)
        else:
            await self.chat.send_message(telegram_id, "Already joined", 3)
        return player
    
    def get_player(self, telegram_id) -> Player:
        for player in self.players:
            if player.telegram_id == telegram_id:
                return player
        return None
    
    def get_players(self):
        return self.players

    async def check_players(self) -> bool:
        status = True
        for player in self.players:
            if player.get_status() == PlayerMode.INIT:
                await self.chat.send_message(self.chat_id, f"@{player.get_name()} is not ready", 10)
                status = False
        return status
                
    
    def get_exercise(self):
        return self.exercise
        
    def add_chat(self, chat : Chat):
        self.chat = chat
        
    def add_exercise(self, context: ContextTypes.DEFAULT_TYPE):
        command_text = ' '.join(context.args)
        match = re.match(r'^([^;]+);(\d+)', command_text)
        
        if match:
            self.exercise.add_exercise(match.group(1), int(match.group(2)), self.status != ChallengeStatus.STARTED)
        
        if (self.status == ChallengeStatus.STARTED):
            pass
            #провести выборы, подходит ли новое упраженение

    async def restore_players(self):
        for filename in os.listdir(self.data_folder):
            if filename.startswith("player_") and filename.endswith(".json"):
                telegram_id = int(filename.split('_')[1].split('.')[0])
                player = await self.add_player(telegram_id)
                await self.chat.send_message(self.chat_id, f"New player restored @{player.get_name()}", 10)

    
    async def start_challenge_routine(self):
        timezone = pytz.timezone('Europe/Moscow')
        now = datetime.now(timezone)

        ex_task_time = time(hour=21, minute=25, second=0)
        rem_task_time = time(hour=22, minute=0, second=0)
        res_task_time = time(hour=21, minute=30, second=0)

        ex_task_datetime = timezone.localize(datetime.combine(now.date(), ex_task_time))
        rem_task_datetime = timezone.localize(datetime.combine(now.date(), rem_task_time))
        res_task_datetime = timezone.localize(datetime.combine(now.date(), res_task_time))

        if ex_task_datetime < now:
            ex_task_datetime += timedelta(days=1)
        if rem_task_datetime < now:
            rem_task_datetime += timedelta(days=1)
        if res_task_datetime < now:
            res_task_datetime += timedelta(days=1)

        ex_task_time_utc = ex_task_datetime.astimezone(pytz.utc).time()
        rem_task_time_utc = rem_task_datetime.astimezone(pytz.utc).time()
        res_task_time_utc = res_task_datetime.astimezone(pytz.utc).time()

        self.job_queue.run_daily(self.send_daily_exercises, ex_task_time_utc)
        self.job_queue.run_daily(self.send_daily_reminder, rem_task_time_utc)
        self.job_queue.run_daily(self.send_daily_result, res_task_time_utc)

    async def send_daily_exercises(self, context: ContextTypes.DEFAULT_TYPE):
        for player in self.players:
            if player.get_status() == PlayerMode.READY:
                available_exercises = [
                    ex for ex in self.exercise.get_exercise() 
                    if player.get_ex_status(ex['sha'])
                ]
                player_exercises = random.sample(
                    available_exercises, 
                    min(len(available_exercises), self.num_ex)
                )

                self.sent_messages[player.telegram_id] = []

                for i, ex in enumerate(player_exercises):
                    exercise_text = f"{i+1}) {ex['name']} {ex['reps']}"
                    sent_message = await self.chat.send_message(player.telegram_id, exercise_text)
                    if sent_message:
                        self.sent_messages[player.telegram_id].append(sent_message.message_id)
                    else:
                        print(f"Failed to send message to {player.telegram_id}")

                print(f"Sent messages to {player.telegram_id}: {self.sent_messages[player.telegram_id]}")

    async def send_daily_reminder(self, context: ContextTypes.DEFAULT_TYPE):
        for player in self.players:
            if player.get_status() == PlayerMode.READY:
                message = f"The Daily Challenge \n@{player.get_name()}\nDid you complete the exercises?"
                await context.bot.send_message(chat_id=player.telegram_id, message_thread_id=self.thread_id, text=message)

    async def send_daily_result(self, context: ContextTypes.DEFAULT_TYPE):
        for player in self.players:
            if player.get_status() == PlayerMode.READY:
                completed_exercises = []
                for message_id in self.sent_messages.get(player.telegram_id, []):
                    message = await context.bot.get_message(chat_id=player.telegram_id, message_id=message_id)
                    if message.reactions and any(reaction.emoji == "👍" for reaction in message.reactions):
                        completed_exercises.append(message.text)

                message = "Your daily results:\n" + "\n".join(completed_exercises)
                await context.bot.send_message(chat_id=player.telegram_id, text=message)

    async def pin_message(self, message_id, bot):
        await bot.pin_chat_message(chat_id=self.chat_id, message_id=message_id)



    def add_app_instance(self, app: ApplicationBuilder):
        """
        Adds an application instance (bot, job_queue) to the chat registry.

        Args:
            app (ApplicationBuilder): The ApplicationBuilder instance containing the bot and job queue.
        """
        self.bot: BT = app.bot
        self.job_queue: JobQueue = app.job_queue