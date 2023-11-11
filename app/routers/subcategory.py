import uuid

from fastapi import APIRouter, HTTPException
from starlette import status

from schema import BaseResponse, Subcategory, SubcategoryResponse
from product_sub_api.app.service.db_service import DBService


router = APIRouter(
    prefix='/subcategory',
    tags=['subcategory'],
)


@router.post('/', response_model=BaseResponse)
def create_subcategory(item: Subcategory):

    db_service = DBService('subcategory')
    query = {
        'category_id': item.category_id,
        'subcategory_id': item.subcategory_id,
    }
    doc = db_service.find_one(query)
    if doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Subcategory name already exists.'
        )

    item.subcategory_id = str(uuid.uuid4().hex)
    db_service.insert_one(item.model_dump())

    return BaseResponse(
        id=item.subcategory_id,
        message='Subcategory successfully created.',
        status=200
    )


@router.get('/', response_model=SubcategoryResponse)
def get_subcategory(
    id: str = None,
    category_id: str = None,
    limit: int = 0,
    page: int = 0,
):

    db_service = DBService('subcategory')

    query = {}
    if id:
        query['subcategory_id'] = id

    if category_id:
        query['category_id'] = category_id

    page = 1 if page and page < 1 else page
    docs, doc_count = db_service.find_all(query, page, limit)

    paginated_response = SubcategoryResponse(
        result=docs,
        page=page,
        limit=limit,
        total=doc_count
    )

    return paginated_response


@router.delete('/{id:str}', response_model=BaseResponse)
def delete_subcategory(id):

    db_service = DBService('subcategory')
    query = {'subcategory_id': id}
    doc = db_service.find_one_and_delete(query)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Subcategory does not exists.'
        )

    # Delete Product
    db_service = DBService('product')
    db_service.delete_many(query)

    return BaseResponse(
        message='Subcategory successfully deleted.',
        status=200
    )