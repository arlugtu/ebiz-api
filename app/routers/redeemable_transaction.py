from fastapi import APIRouter

from schema import BaseResponse
from product_sub_api.app.service.db_service import DBService
from service.telegram_service import TelegramMessageService


router = APIRouter(
    prefix='/redeemable-transaction',
    tags=['redeemable-transaction'],
)


@router.post('/{id:str}', response_model=BaseResponse)
async def create_redeemable_transaction(id):

    db_service = DBService('redeemable_transaction')
    query = {'transaction_id': id}
    doc = db_service.find_one(query)
    if not doc:
        return

    db_service = DBService('redeemable_inventory')

    service = TelegramMessageService(doc['chat_id'])

    # Get Redeemable Inventory
    items = db_service.find_all(query)
    files = {d['inventory_id']: d['file_path'] for d in items[0]}

    await service.send_document(files.values())

    return BaseResponse(
        id=id,
        message='Transaction successfully created.',
        status=200
    )