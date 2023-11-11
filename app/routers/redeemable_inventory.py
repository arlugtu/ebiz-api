import uuid

from fastapi import APIRouter, HTTPException, UploadFile
from starlette import status
from starlette.responses import FileResponse
from typing import List

from common.common import delete_file
from schema import (
    BaseResponse,
    RedeemableInventory,
    RedeemableInventoryResponse
)
from product_sub_api.app.service.db_service import DBService
from service.file_writer_service import FileWriter


router = APIRouter(
    prefix='/redeemable-inventory',
    tags=['redeemable-inventory'],
)


@router.post('/', response_model=BaseResponse)
async def create_redeemable_inventory(item: RedeemableInventory):

    db_service = DBService('redeemable_inventory')

    item.inventory_id = str(uuid.uuid4().hex)
    db_service.insert_one(item.model_dump())

    return BaseResponse(
        id=item.inventory_id,
        message='Inventory successfully created.',
        status=200
    )


@router.get('/', response_model=RedeemableInventoryResponse)
def get_redeemable_inventory(
    id: str = None,
    product_id: str = None,
    limit: int = 0,
    page: int = 0,
):

    db_service = DBService('redeemable_inventory')

    query = {}
    if id:
        query['inventory_id'] = id

    if product_id:
        query['product_id'] = product_id

    page = 1 if page and page < 1 else page
    docs, doc_count = db_service.find_all(query, page, limit)

    paginated_response = RedeemableInventoryResponse(
        result=docs,
        page=page,
        limit=limit,
        total=doc_count
    )

    return paginated_response


@router.delete('/{id:str}', response_model=dict)
def delete_redeemable_inventory(id):

    _return = {'status': 200}

    db_service = DBService('redeemable_inventory')
    query = {'inventory_id': id}
    doc = db_service.find_one_and_delete(query)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Inventory does not exists.'
        )

    # Delete File
    delete_file(doc['file_path'])

    if doc['status'] == 'New':
        # Update Redeemable Product
        db_service = DBService('redeemable_product')
        query = {'product_id': doc['product_id']}
        product = db_service.find_one_and_update(
            query,
            {'$inc': {'inventory': -1}}
        )
        if product:
            _return['inventory'] = product['inventory']

    _return['message'] = 'Inventory successfully deleted.'

    return _return


@router.get('/download/{id:str}')
def download_redeemable_inventory(id):

    db_service = DBService('redeemable_inventory')
    query = {'inventory_id': id}
    doc = db_service.find_one(query)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'File does not exists.'
        )

    return FileResponse(
        doc['file_path'],
        media_type='text/plain',
        filename=doc['file_name']
    )


@router.post('/upload/{product_id:str}', response_model=dict)
async def upload_redeemable_inventory(
    product_id: str,
    files: List[UploadFile]
):

    # Save Files
    file_writer = FileWriter()
    file_paths = await file_writer.save(files)

    db_service = DBService('redeemable_inventory')

    # Insert Inventory
    to_insert = []
    for i, file in enumerate(files):
        item = RedeemableInventory(
            file_name=file.filename,
            file_path=file_paths[i],
            inventory_id=str(uuid.uuid4().hex),
            product_id=product_id,
            status='New'
        )
        to_insert.append(item.model_dump())

    if to_insert:
        db_service.insert_many(to_insert)

    # Update Redeemable Product
    db_service = DBService('redeemable_product')
    query = {'product_id': product_id}
    product = db_service.find_one_and_update(
        query,
        {'$inc': {'inventory': len(files)}}
    )

    return {
        'inventory': product['inventory'],
        'message': 'Files successfully uploaded.',
        'status': 200
    }