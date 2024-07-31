

from telegram.ext import ApplicationBuilder, CallbackContext

from telegram.ext._utils.types import BT
from telegram.ext._jobqueue import JobQueue, Job
from telegram._message import Message

import asyncio
        
class Chat():
    def add_app_instance(self, app: ApplicationBuilder) -> None:
            self.bot: BT = app.bot
            self.job_queue: JobQueue = app.job_queue

    # TODO It seems to me that working with messages can be abstracted into a separate entity.
    async def delete_message_delayed(
        self, chat_id: int, message_id: int, delay: int
    ) -> None:
        """
        Deletes a message after a specified delay.

        Args:
            chat_id (int): The ID of the chat where the message is located.
            message_id (int): The ID of the message to be deleted.
            delay (int): The delay in seconds before deleting the message.
        """
        await asyncio.sleep(delay)
        await self.bot.delete_message(chat_id=chat_id, message_id=message_id)

    async def send_message(
        self,
        chat_id: int,
        text: str,
        self_destruct: int = 0,
        message_thread_id: int = None,
        reply_markup = None
    ) -> Message:
        """
        Sends a message to a specified chat and schedules its deletion after a delay.

        Args:
            chat_id (int): The ID of the chat where the message will be sent.
            text (str): The text of the message.
            self_destruct (int, optional): Delay in seconds before the message is deleted. Defaults to 0.
        """

        message: Message = await self.bot.send_message(
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            reply_markup = reply_markup,
            text=f"{text} {'⏰' if self_destruct != 0 else ''}", 
        )
        if self_destruct != 0:
            asyncio.create_task(
                self.delete_message_delayed(
                    chat_id=chat_id, message_id=message.message_id, delay=self_destruct
                )
            )
        return message