import requests

from common.configs import BOT_TOKEN, IS_DEBUG
from common.logger import module_logger

logger = module_logger(__name__)


class TelegramMessageService:
    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.message = None
        self.url = None

    def send_message(self, message):
        self.message = message
        self.prepare_url()
        logger.debug(f'Sending message to {self.url}')
        response = requests.get(self.url)
        if response.status_code == 200:
            logger.debug(f'Response from telegram {response.json()}')

    def prepare_url(self):
        if self.chat_id is None:
            self.chat_id = 5842487092
        self.url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={self.chat_id}&text={self.message}'

    def telegram_bot_send_document(self, subcategory_file_location):
        if subcategory_file_location is None or IS_DEBUG:
            file_location = 'test.txt'
        else:
            file_location = subcategory_file_location
        if self.chat_id is None or IS_DEBUG:
            self.chat_id = 5842487092

        send_document = 'https://api.telegram.org/bot' + BOT_TOKEN + '/sendDocument?'
        data = {
            'chat_id': self.chat_id,
            'parse_mode': 'HTML',
            'caption': 'Please download the file'
        }
        files = {
            'document': open(file_location, 'rb')
        }
        r = requests.post(send_document, data=data, files=files, stream=True)
        print(r.url)
        return r.json()
