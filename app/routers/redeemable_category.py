import uuid

from fastapi import APIRouter, HTTPException
from starlette import status

from schema import BaseResponse, RedeemableCategory, RedeemableCategoryResponse
from product_sub_api.app.service.db_service import DBService


router = APIRouter(
    prefix='/redeemable-category',
    tags=['redeemable-category'],
)


@router.post('/', response_model=BaseResponse)
async def create_redeemable_category(item: RedeemableCategory):

    db_service = DBService('redeemable_category')
    query = {'category_name': item.category_name}
    doc = db_service.find_one(query)
    if doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Category name already exists.'
        )

    item.category_id = str(uuid.uuid4().hex)
    db_service.insert_one(item.model_dump())

    return BaseResponse(
        id=item.category_id,
        message='Category successfully created.',
        status=200
    )


@router.get('/', response_model=RedeemableCategoryResponse)
def get_redeemable_category(id: str = None, limit: int = 0, page: int = 0):

    db_service = DBService('redeemable_category')
    query = {}
    if id:
        query['category_id'] = id

    page = 1 if page and page < 1 else page
    docs, doc_count = db_service.find_all(query, page, limit)

    paginated_response = RedeemableCategoryResponse(
        result=docs,
        page=page,
        limit=limit,
        total=doc_count
    )

    return paginated_response


@router.delete('/{id:str}', response_model=BaseResponse)
def delete_redeemable_category(id):

    db_service = DBService('redeemable_category')
    query = {'category_id': id}
    doc = db_service.find_one_and_delete(query)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Category does not exists.'
        )

    # Delete Product
    db_service = DBService('redeemable_product')
    db_service.delete_many(query)

    return BaseResponse(
        message='Category successfully deleted.',
        status=200
    )