import random
import string
import uuid

from fastapi import APIRouter, HTTPException, Request
from starlette import status

from common.common import get_timestamp
from schema import (
    BaseResponse,
    Promotion,
    PromotionResponse
)
from service.db_service import DBService
from service.telegram_service import TelegramMessageService


router = APIRouter(
    prefix='/promotion',
    tags=['promotion'],
)


@router.post('/', response_model=BaseResponse)
def create_promotion(item: Promotion):

    db_service = DBService('promotion')
    query = {
        'user_id': item.user_id
    }
    doc = db_service.find_one(query)
    if doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Promotion for user already exists.'
        )

    item.code = generate_promo_code(db_service)
    item.date_created = get_timestamp()
    item.promotion_id = str(uuid.uuid4().hex)
    db_service.insert_one(item.model_dump())

    return BaseResponse(
        id=item.promotion_id,
        message='Promotion successfully created.',
        status=200
    )


@router.get('/', response_model=PromotionResponse)
def get_promotion(
    id: str = None,
    limit: int = 0,
    page: int = 0,
):

    db_service = DBService('promotion')

    query = {}
    if id:
        query['promotion_id'] = id

    page = 1 if page and page < 1 else page
    docs, doc_count = db_service.find_all(
        query,
        page,
        limit,
        order_by='date_created',
        sort_by=-1
    )

    if docs:
        _docs = {d['user_id']: d for d in docs}

        # Get Promotion Payout requests
        db_service = DBService('promotion_payout')
        query = {
            'status': 'Pending',
            'user_id': {'$in': list(_docs.keys())}
        }
        payout = db_service.find_all(query)
        for d in payout[0]:
            _docs[d['user_id']]['payout_amount'] = d['amount']
            _docs[d['user_id']]['payout_id'] = d['payout_id']

        docs = list(_docs.values())

    paginated_response = PromotionResponse(
        result=docs,
        page=page,
        limit=limit,
        total=doc_count
    )

    return paginated_response


@router.get('/settings', response_model=dict)
def get_promotion_settings(key: str = None):

    db_service = DBService('promotion_settings')

    query = {}
    if key:
        query['key'] = key

    docs = db_service.find_all(query)

    _return = {
        'result': {
            d['key']: d['value']
            for d in docs[0]
            if d.get('key')
        }
    }

    return _return


@router.post('/settings', response_model=BaseResponse)
async def update_promotion_settings(request: Request):

    db_service = DBService('promotion_settings')

    data = await request.json() or {}

    to_update = [
        {
            'key': k,
            'value': v
        }
        for k, v in data.items()
    ]
    for d in to_update:
        query = {'key': d['key']}
        db_service.update_one(query, {'$set': d}, True)

    return BaseResponse(
        message='Settings successfully updated.',
        status=200
    )


@router.put('/payout/{id:str}', response_model=BaseResponse)
async def update_promotion_payout(id, request: Request):

    data = await request.json()

    to_update = {'status': data.get('status')}

    db_service = DBService('promotion_payout')
    query = {'payout_id': id}
    payout = db_service.find_one_and_update(query, {'$set': to_update})

    # Update Promotion
    amount = payout.get('amount') or 0
    message = ''
    if to_update['status'] == 'Approved':
        message = 'approved'
        db_service = DBService('promotion')
        query = {'user_id': payout['user_id']}
        db_service.find_one_and_update(
            query,
            {
                '$inc': {
                    'balance': -amount,
                    'total_payout': amount
                }
            }
        )
    elif to_update['status'] == 'Disapproved':
        message = 'disapproved'

    # Notify User
    if amount and message and payout.get('user_id'):
        try:
            service = TelegramMessageService(payout['user_id'])
            message = f"Your withdrawal of {amount} USDT has been {message}."
            await service.send_message(message)
        except:
            pass

    return BaseResponse(
        message='Product successfully updated.',
        status=200
    )


def generate_promo_code(db_service=None):

    db_service = db_service or DBService('promotion')

    chars = string.ascii_uppercase + string.digits
    code = ''.join([random.choice(chars) for i in range(6)])

    retry = 0
    while retry < 10:
        # Validate code
        query = {'code': code}
        promotion = db_service.find_one(query)
        if not promotion:
            return code

        retry += 1
