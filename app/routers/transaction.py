from fastapi import APIRouter

from product_sub_api.app.service.db_service import DBService


router = APIRouter(
    prefix='/transaction',
    tags=['transaction'],
)


@router.get('/', response_model=dict)
def get_transaction(id: str = None, limit: int = 0, page: int = 0):

    db_service = DBService('transaction')

    query = {}
    if id:
        query['trackId'] = id

    page = 1 if page and page < 1 else page
    docs, doc_count = db_service.find_all(
        query,
        page,
        limit,
        order_by='createdAt',
        sort_by=-1
    )

    return {
        'limit': limit,
        'page': page,
        'result': docs,
        'total': doc_count
    }