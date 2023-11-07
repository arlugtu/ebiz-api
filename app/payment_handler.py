from common.logger import module_logger
from service.subcategory_db_service import SubcategoryDBService
from service.telegram_service import TelegramMessageService
from service.transaction_db_service import TransactionDBService
from service.user_db_service import UserDBService

logger = module_logger(__name__)


class PaymentHandler:
    @staticmethod
    def get_meta_data(metadata):
        name, chat_id, item_id, user_id, user_name, redeem_points = None, None, None, None, None, None
        if 'name' in metadata:
            name = metadata['name']
        if 'chat_id' in metadata:
            chat_id = metadata['chat_id']
        if 'item_id' in metadata:
            item_id = metadata['item_id']
        if 'user_id' in metadata:
            user_id = metadata['user_id']
        if 'user_name' in metadata:
            user_name = metadata['user_name']
        if 'redeem_points' in metadata:
            redeem_points = metadata['redeem_points']
        return name, chat_id, item_id, user_id, user_name, redeem_points

    @staticmethod
    def reduce_quantity(subcategory_id):
        logger.info(f'Reducing Quantity for Subcategory {subcategory_id}')
        pass

    @staticmethod
    def get_payment_details(payment_list):
        payment_data = payment_list[0]
        network = payment_data.get('network')
        payment_id = payment_data.get('transaction_id')
        status = payment_data.get('status')
        detected_at = payment_data.get('detected_at')
        value = payment_data.get('value')
        amount = None
        if 'local' in value and 'amount' in value['local']:
            amount = value['local']['amount']
        return network, payment_id, status, detected_at, amount

    def prepare_payment_data(self, payment_data, coinbase_id, coinbase_code, user_id):
        network, payment_id, status, detected_at, amount = self.get_payment_details(payment_data)
        data = {
            'user_id': user_id,
            'coinbase_id': coinbase_id,
            'coinbase_code': coinbase_code,
            'network': network,
            'payment_id': payment_id,
            'status': status,
            'detected_at': detected_at,
            'amount': amount,
        }
        logger.debug(f'Payment Success Details {data}')
        return data

    def handle_payment(self, data):
        if 'id' in data and data['id'] != '00000000-0000-0000-0000-000000000000':
            if 'event' in data and 'type' in data['event']:
                payment_type = data['event']['type']
        if 'event' in data and 'type' in data['event']:
            payment_type = data['event']['type']
            logger.debug(f'{payment_type}')
            coinbase_code, coinbase_id = self.get_coinbase_data(data)
            name, chat_id, subcategory_id, user_id, user_name, redeem_points = self.get_meta_data(
                data['event']['data']['metadata']
            )
            telegram_message_service = TelegramMessageService(chat_id)
            if payment_type == 'charge:confirmed':
                payment_data = self.prepare_payment_data(data['event']['data']['payments'],
                                                         coinbase_id, coinbase_code, user_id)
                transaction_service = TransactionDBService()
                transaction_service.insert(payment_data)
                user_data = {
                    'user_id': user_id,
                    'user_name': user_name,
                    'name': name,
                    'redeem_points': redeem_points
                }
                logger.debug(f'User Details {user_data}')
                user_service = UserDBService()
                user_service.insert_or_update(user_data)
                # TODO points history implementation
                self.reduce_quantity(subcategory_id)
                telegram_message_service.send_message('Payment is Successful, Thank you for the payment')
                subcategory_db_service = SubcategoryDBService()
                subcategory_file_location = subcategory_db_service.find_one_get_field(subcategory_id, 'file')
                telegram_message_service.telegram_bot_send_document(subcategory_file_location)
                logger.debug('Success Payment')
            elif payment_type == 'charge:failed':
                logger.debug('Payment Failed')
                telegram_message_service.send_message('Payment Failed')
        else:
            logger.error(f'Error Data: {data}')

    @staticmethod
    def get_coinbase_data(data):
        coinbase_id = data['event']['data']['id']
        coinbase_code = data['event']['data']['code']
        return coinbase_code, coinbase_id
