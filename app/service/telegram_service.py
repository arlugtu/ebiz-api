import requests

from common.configs import BOT_TOKEN
from common.logger import module_logger
from telegram import Bot, InputMediaDocument

logger = module_logger(__name__)


class TelegramMessageService:

    def __init__(self, chat_id):

        self.bot = Bot(BOT_TOKEN)
        self.chat_id = chat_id


    async def send_message(self, message):

        await self.bot.send_message(self.chat_id, message)


    async def send_document(self, files):

        media_group = list()
        for f in files:
            if not f:
                continue

            with open(f, 'rb') as _f:
                _f.seek(0)
                media_group.append(InputMediaDocument(_f, caption=''))

        await self.bot.send_media_group(self.chat_id, media=media_group)
