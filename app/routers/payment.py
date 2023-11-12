from fastapi import APIRouter, Request
from pymongo.collection import ReturnDocument

from schema import BaseResponse
from service.db_service import DBService
from service.telegram_service import TelegramMessageService


router = APIRouter(
    prefix='/payment',
    tags=['payment'],
)


@router.post('/', response_model=BaseResponse)
async def create_payment(request: Request):

    data = await request.json()

    status = data.get('status')
    track_id = data.get('trackId')

    db_service = DBService('transaction')

    try:
        # Update Transaction
        query = {'trackId': track_id}
        tx = db_service.find_one_and_update(
            query,
            {'$set': {'status': status}},
            return_document=ReturnDocument.BEFORE
        )

        # Update User
        if (
            status == 'Paid'
            and tx.get('status') != 'Paid'
            and tx.get('user_id')
        ):
            db_service = DBService('user')
            query = {'user_id': tx['user_id']}
            db_service.find_one_and_update(
                query,
                {'$inc': {'points': tx['points']}}
            )

            service = TelegramMessageService(tx['chat_id'])

            # Get Inventory
            db_service = DBService('inventory')
            query = {'transaction_id': tx.get('transaction_id')}
            items = db_service.find_all(query)
            files = {d['inventory_id']: d['file_path'] for d in items[0]}

            # Update Inventory
            if files:
                db_service.update_many(
                    {'inventory_id': {'$in': list(files.keys())}},
                    {'$set': {'status': 'Sold'}}
                )

            await service.send_document(files.values())

            message = ''
            if tx['points']:
                message = f" and you earned {tx['points']} points"

            message = f"Your payment to {tx['address']} is successful{message}."
            await service.send_message(message)

            # Get Promotion Transaction
            db_service = DBService('promotion_transaction')
            query.update({'status': 'New'})
            transaction = db_service.find_one_and_update(
                query,
                {'$set': {'status': 'Paid'}}
            )

            if transaction and transaction.get('amount'):
                # Update Promotion
                db_service = DBService('promotion')
                query = {'promotion_id': transaction.get('promotion_id')}
                promotion = db_service.find_one_and_update(
                    query,
                    {'$inc': {'balance': transaction['amount']}}
                )

                # Notify Promoter
                if promotion:
                    service = TelegramMessageService(promotion['user_id'])
                    message = f"You earned {transaction['amount']} USDT"
                    message += ' from your promotion.'
                    await service.send_message(message)
    except:
        pass

    return BaseResponse(
        id=track_id,
        message='Payment successfully created.',
        status=200
    )
