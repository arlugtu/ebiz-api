import uuid

from fastapi import APIRouter, HTTPException, Request
from starlette import status

from common.common import get_timestamp
from schema import BaseResponse, RedeemableProduct, RedeemableProductResponse
from service.db_service import DBService


router = APIRouter(
    prefix='/redeemable-product',
    tags=['redeemable-product'],
)


@router.post('/', response_model=BaseResponse)
async def create_redeemable_product(item: RedeemableProduct):

    # Get Category
    db_service = DBService('redeemable_category')
    query = {'category_id': item.category_id}
    category = db_service.find_one(query)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Category does not exists.'
        )

    db_service = DBService('redeemable_product')
    query['product_name'] = item.product_name
    doc = db_service.find_one(query)
    if doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Product name already exists.'
        )

    item.date_created = get_timestamp()
    item.product_id = str(uuid.uuid4().hex)
    db_service.insert_one(item.model_dump())

    return BaseResponse(
        id=item.product_id,
        message='Product successfully created.',
        status=200
    )


@router.get('/', response_model=RedeemableProductResponse)
def get_redeemable_product(id: str = None, limit: int = 0, page: int = 0):

    db_service = DBService('redeemable_product')

    query = {}
    if id:
        query['product_id'] = id

    page = 1 if page and page < 1 else page
    docs, doc_count = db_service.find_all(
        query,
        page,
        limit,
        order_by='product_name'
    )

    paginated_response = RedeemableProductResponse(
        result=docs,
        page=page,
        limit=limit,
        total=doc_count
    )

    return paginated_response


@router.put('/{id:str}', response_model=BaseResponse)
async def update_redeemable_product(id, request: Request):

    data = await request.json()

    keys = ('description', 'points', 'product_name')
    to_update = {k: data.get(k) for k in keys}

    db_service = DBService('redeemable_product')
    query = {'product_id': id}
    db_service.find_one_and_update(query, {'$set': to_update})

    return BaseResponse(
        message='Product successfully updated.',
        status=200
    )


@router.delete('/{id:str}', response_model=BaseResponse)
def delete_redeemable_product(id):

    db_service = DBService('redeemable_product')
    query = {'product_id': id}
    doc = db_service.find_one_and_delete(query)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Product does not exists.'
        )

    return BaseResponse(
        message='Product successfully deleted.',
        status=200
    )
