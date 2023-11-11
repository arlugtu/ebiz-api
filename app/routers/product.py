import uuid

from fastapi import APIRouter, HTTPException, Request
from starlette import status

from schema import BaseResponse, Product, ProductResponse
from product_sub_api.app.service.db_service import DBService


router = APIRouter(
    prefix='/product',
    tags=['product'],
)


@router.post('/', response_model=BaseResponse)
async def create_product(item: Product):

    # Get Category
    db_service = DBService('category')
    query = {'category_id': item.category_id}
    category = db_service.find_one(query)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Category does not exists.'
        )

    # Get Subcategory
    db_service = DBService('subcategory')
    _query = {'subcategory_id': item.subcategory_id}
    subcategory = db_service.find_one(_query)
    if not subcategory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Subcategory does not exists.'
        )

    db_service = DBService('product')
    query['product_name'] = item.product_name
    query.update(_query)
    doc = db_service.find_one(query)
    if doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Product name already exists.'
        )

    item.product_id = str(uuid.uuid4().hex)
    db_service.insert_one(item.model_dump())

    return BaseResponse(
        id=item.product_id,
        message='Product successfully created.',
        status=200
    )


@router.get('/', response_model=ProductResponse)
def get_product(id: str = None, limit: int = 0, page: int = 0):

    db_service = DBService('product')

    query = {}
    if id:
        query['product_id'] = id

    page = 1 if page and page < 1 else page
    docs, doc_count = db_service.find_all(query, page, limit)

    paginated_response = ProductResponse(
        result=docs,
        page=page,
        limit=limit,
        total=doc_count
    )

    return paginated_response


@router.put('/{id:str}', response_model=BaseResponse)
async def update_product(id, request: Request):

    data = await request.json()

    keys = ('description', 'points', 'price', 'product_name')
    to_update = {k: data.get(k) for k in keys}

    db_service = DBService('product')
    query = {'product_id': id}
    db_service.find_one_and_update(query, {'$set': to_update})

    return BaseResponse(
        message='Product successfully updated.',
        status=200
    )


@router.delete('/{id:str}', response_model=BaseResponse)
def delete_product(id):

    db_service = DBService('product')
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