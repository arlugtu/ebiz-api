import os
import uuid

from typing import List

import uvicorn
from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.middleware.cors import (CORSMiddleware)
from starlette import status
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles

from common.configs import SELF_DOMAIN
from common.logger import module_logger
from schema import (
    BaseResponse,
    Category,
    CategoryResponse,
    Inventory,
    Product,
    ProductResponse,
    RedeemableCategory,
    RedeemableCategoryResponse,
    RedeemableInventory,
    RedeemableProduct,
    RedeemableProductResponse,
    Subcategory
)
from service.category_db_service import CategoryDBService
from service.file_writer_service import FileWriter
from service.inventory_db_service import InventoryDBService
from service.product_db_service import ProductDBService
from service.redeemable_category_db_service import RedeemableCategoryDBService
from service.redeemable_inventory_db_service import RedeemableInventoryDBService
from service.redeemable_product_db_service import RedeemableProductDBService
from service.subcategory_db_service import SubcategoryDBService
from service.telegram_service import TelegramMessageService
from service.transaction_db_service import TransactionDBService
from service.user_db_service import UserDBService

app = FastAPI()
app.mount("/media", StaticFiles(directory="media"), name="media")
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origins=["*"]
)
logger = module_logger(__name__)


@app.post('/category', response_model=Category)
async def create_category(item: Category):

    db_service = CategoryDBService()
    doc = db_service.find_one(item.category_name)
    if doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Category Name {item.category_name} already exists.'
        )

    item.category_id = str(uuid.uuid4().hex)
    item_dict = item.model_dump()
    db_service.insert_one(item_dict)

    return item


@app.get('/category')
def get_category(page: int | None = None, limit: int | None = None):

    page = 1 if page and page < 1 else page

    db_service = CategoryDBService()
    docs, doc_count = db_service.find_all(page, limit)
    if page and limit:
        limit = doc_count

    # Get Subcategory
    if docs:
        db_service = SubcategoryDBService()
        for doc in docs:
            subcategory = db_service.find_all(doc['category_id'])
            doc['subcategory'] = subcategory[0]

    paginated_response = CategoryResponse(
        result=docs,
        page=page,
        limit=limit,
        total=doc_count
    )

    return paginated_response


@app.delete('/category/{id:str}')
def delete_category(id):

    db_service = CategoryDBService()
    doc = db_service.find_one_by_id(id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Category does not exists.'
        )

    if db_service.delete_one(id):
        # Delete Subcategory
        db_service = SubcategoryDBService()
        db_service.delete_many({'category_id': id})

        # Delete Product
        db_service = ProductDBService()
        db_service.delete_many({'category_id': id})

    return id


@app.post('/inventory', response_model=Inventory)
async def create_inventory(item: Inventory):

    db_service = InventoryDBService()

    item.inventory_id = str(uuid.uuid4().hex)
    item_dict = item.model_dump()
    db_service.insert_one(item_dict)

    return item


@app.get('/inventory/{id:str}')
def get_inventory_by_product_id(id):

    db_service = InventoryDBService()
    docs, doc_count = db_service.find_all(id)

    return docs


@app.delete('/inventory/{id:str}')
def delete_inventory(id):

    _return = {'status': 200}

    db_service = InventoryDBService()
    doc = db_service.find_one_by_id(id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Inventory does not exists.'
        )

    if db_service.delete_one(id):
        # Delete File
        delete_file(doc['file_path'])

        if doc['status'] == 'New':
            # Update Product
            db_service = ProductDBService()
            product = db_service.find_one_and_update(
                doc['product_id'],
                {'$inc': {'inventory': -1}}
            )
            _return['inventory'] = product['inventory']

    _return['message'] = 'Inventory successfully deleted.'

    return _return


@app.get('/inventory-download/{id:str}')
def  download_inventory(id):

    db_service = InventoryDBService()
    doc = db_service.find_one_by_id(id)
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


@app.post('/inventory-upload/{product_id:str}')
async def upload_inventory(
    product_id: str,
    files: List[UploadFile]
):

    # Save Files
    file_writer = FileWriter()
    file_paths = await file_writer.save(files)

    db_service = InventoryDBService()

    # Insert Inventory
    to_insert = []
    for i, file in enumerate(files):
        item = Inventory(
            file_name=file.filename,
            file_path=file_paths[i],
            inventory_id=str(uuid.uuid4().hex),
            product_id=product_id,
            status='New'
        )
        item_dict = item.model_dump()
        to_insert.append(item_dict)

    if to_insert:
        db_service.insert_many(to_insert)

    # Update Product
    db_service = ProductDBService()
    product = db_service.find_one_and_update(
        product_id,
        {'$inc': {'inventory': len(files)}}
    )

    return {
        'inventory': product['inventory'],
        'message': 'Files successfully uploaded.',
        'status': 200
    }


@app.post('/payment')
async def create_payment(request: Request):

    data = await request.json()

    status = data.get('status')
    track_id = data.get('trackId')

    db_service = TransactionDBService()

    try:
        # Update Transaction
        tx = db_service.find_one_and_update(
            track_id,
            {'$set': {'status': status}}
        )

        # Update User
        if (
            status == 'Paid'
            and tx.get('status') != 'Paid'
            and tx.get('user_id')
        ):
            db_service = UserDBService()
            db_service.find_one_and_update(
                tx['user_id'],
                {'$inc': {'points': tx['points']}}
            )

            service = TelegramMessageService(tx['chat_id'])

            # Get Inventory
            db_service = InventoryDBService()
            items, doc_count = db_service.find_all(track_id, key='trackId')
            files = {d['inventory_id']: d['file_path'] for d in items}

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
    except:
        pass


@app.post('/product', response_model=Product)
async def create_product(item: Product):

    # Get Category
    db_service = CategoryDBService()
    category = db_service.find_one(item.category_name)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Category Name {item.category_name} does not exists.'
        )

    # Get Subcategory
    db_service = SubcategoryDBService()
    subcategory = db_service.find_one(
        category['category_id'],
        item.subcategory_name
    )
    if not subcategory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Subcategory Name {item.subcategory_name} does not exists.'
        )

    db_service = ProductDBService()
    doc = db_service.find_one(
        category['category_id'],
        subcategory['subcategory_id'],
        item.product_name
    )
    if doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Product Name {item.product_name} already exists.'
        )

    item.category_id = category['category_id']
    item.product_id = str(uuid.uuid4().hex)
    item.subcategory_id = subcategory['subcategory_id']
    item_dict = item.model_dump()
    db_service.insert_one(item_dict)

    return item


@app.get('/product')
def get_product(page: int | None = None, limit: int | None = None):

    page = 1 if page and page < 1 else page

    db_service = ProductDBService()
    docs, doc_count = db_service.find_all(page, limit)
    if page and limit:
        limit = doc_count

    paginated_response = ProductResponse(
        result=docs,
        page=page,
        limit=limit,
        total=doc_count
    )

    return paginated_response


@app.get('/product/{id:str}')
def get_product_by_id(id):

    db_service = ProductDBService()
    doc = db_service.find_one_by_id(id)

    return doc


@app.put('/product/{id:str}')
async def update_product(id, request: Request):

    data = await request.json()

    keys = ('description', 'points', 'price', 'product_name')
    to_update = {k: data.get(k) for k in keys}

    db_service = ProductDBService()
    db_service.find_one_and_update(id, {'$set': to_update})


@app.delete('/product/{id:str}')
def delete_product(id):

    db_service = ProductDBService()
    doc = db_service.find_one_by_id(id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Product does not exists.'
        )

    db_service.delete_one(id)

    return id


@app.post('/redeemable-category', response_model=RedeemableCategory)
async def create_redeemable_category(item: RedeemableCategory):

    db_service = RedeemableCategoryDBService()
    doc = db_service.find_one(item.category_name)
    if doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Category Name {item.category_name} already exists.'
        )

    item.category_id = str(uuid.uuid4().hex)
    item_dict = item.model_dump()
    db_service.insert_one(item_dict)

    return item


@app.get('/redeemable-category')
def get_redeemable_category(page: int | None = None, limit: int | None = None):

    page = 1 if page and page < 1 else page

    db_service = RedeemableCategoryDBService()
    docs, doc_count = db_service.find_all(page, limit)
    if page and limit:
        limit = doc_count

    paginated_response = RedeemableCategoryResponse(
        result=docs,
        page=page,
        limit=limit,
        total=doc_count
    )

    return paginated_response


@app.delete('/redeemable-category/{id:str}')
def delete_redeemable_category(id):

    db_service = RedeemableCategoryDBService()
    doc = db_service.find_one_by_id(id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Category does not exists.'
        )

    if db_service.delete_one(id):
        # Delete Product
        db_service = RedeemableProductDBService()
        db_service.delete_many({'category_id': id})

    return id


@app.post('/redeemable-inventory', response_model=RedeemableInventory)
async def create_redeemable_inventory(item: RedeemableInventory):

    db_service = RedeemableInventoryDBService()

    item.inventory_id = str(uuid.uuid4().hex)
    item_dict = item.model_dump()
    db_service.insert_one(item_dict)

    return item


@app.get('/redeemable-inventory/{id:str}')
def get_redeemable_inventory_by_product_id(id):

    db_service = RedeemableInventoryDBService()
    docs, doc_count = db_service.find_all(id)

    return docs


@app.delete('/redeemable-inventory/{id:str}')
def delete_redeemable_inventory(id):

    _return = {'status': 200}

    db_service = RedeemableInventoryDBService()
    doc = db_service.find_one_by_id(id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Inventory does not exists.'
        )

    if db_service.delete_one(id):
        # Delete File
        delete_file(doc['file_path'])

        if doc['status'] == 'New':
            # Update Redeemable Product
            db_service = RedeemableProductDBService()
            product = db_service.find_one_and_update(
                doc['product_id'],
                {'$inc': {'inventory': -1}}
            )
            if product:
                _return['inventory'] = product['inventory']

    _return['message'] = 'Inventory successfully deleted.'

    return _return


@app.get('/redeemable-inventory-download/{id:str}')
def  download_redeemable_inventory(id):

    db_service = RedeemableInventoryDBService()
    doc = db_service.find_one_by_id(id)
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


@app.post('/redeemable-inventory-upload/{product_id:str}')
async def upload_redeemable_inventory(
    product_id: str,
    files: List[UploadFile]
):

    # Save Files
    file_writer = FileWriter()
    file_paths = await file_writer.save(files)

    db_service = RedeemableInventoryDBService()

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
        item_dict = item.model_dump()
        to_insert.append(item_dict)

    if to_insert:
        db_service.insert_many(to_insert)

    # Update Redeemable Product
    db_service = RedeemableProductDBService()
    product = db_service.find_one_and_update(
        product_id,
        {'$inc': {'inventory': len(files)}}
    )

    return {
        'inventory': product['inventory'],
        'message': 'Files successfully uploaded.',
        'status': 200
    }


@app.post('/redeemable-product', response_model=RedeemableProduct)
async def create_redeemable_product(item: RedeemableProduct):

    # Get Category
    db_service = RedeemableCategoryDBService()
    category = db_service.find_one(item.category_name)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Category Name {item.category_name} does not exists.'
        )

    db_service = RedeemableProductDBService()
    doc = db_service.find_one(
        category['category_id'],
        item.product_name
    )
    if doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Product Name {item.product_name} already exists.'
        )

    item.category_id = category['category_id']
    item.product_id = str(uuid.uuid4().hex)
    item_dict = item.model_dump()
    db_service.insert_one(item_dict)

    return item


@app.get('/redeemable-product')
def get_redeemable_product(page: int | None = None, limit: int | None = None):

    page = 1 if page and page < 1 else page

    db_service = RedeemableProductDBService()
    docs, doc_count = db_service.find_all(page, limit)
    if page and limit:
        limit = doc_count

    paginated_response = RedeemableProductResponse(
        result=docs,
        page=page,
        limit=limit,
        total=doc_count
    )

    return paginated_response


@app.get('/redeemable-product/{id:str}')
def get_redeemable_product_by_id(id):

    db_service = RedeemableProductDBService()
    doc = db_service.find_one_by_id(id)

    return doc


@app.put('/redeemable-product/{id:str}')
async def update_redeemable_product(id, request: Request):

    data = await request.json()

    keys = ('description', 'points', 'product_name')
    to_update = {k: data.get(k) for k in keys}

    db_service = RedeemableProductDBService()
    db_service.find_one_and_update(id, {'$set': to_update})


@app.delete('/redeemable-product/{id:str}')
def delete_redeemable_product(id):

    db_service = RedeemableProductDBService()
    doc = db_service.find_one_by_id(id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Product does not exists.'
        )

    db_service.delete_one(id)

    return id


@app.post('/subcategory')
def create_subcategory(item: Subcategory):

    db_service = SubcategoryDBService()
    doc = db_service.find_one(item.category_id, item.subcategory_name)
    if doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Subcategory Name {item.subcategory_name} already exists.'
        )

    item.subcategory_id = str(uuid.uuid4().hex)
    item_dict = item.model_dump()
    db_service.insert_one(item_dict)

    return item


@app.get('/subcategory/{id:str}')
def get_subcategory_by_category_id(id):

    db_service = SubcategoryDBService()
    docs, doc_count = db_service.find_all(id)

    return docs


@app.delete('/subcategory/{id:str}')
def delete_subcategory(id):

    db_service = SubcategoryDBService()
    doc = db_service.find_one_by_id(id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Subcategory does not exists.'
        )

    if db_service.delete_one(id):
        # Delete Product
        db_service = ProductDBService()
        db_service.delete_many({'subcategory_id': id})

    return id


def delete_file(file_path):

    try:
        os.remove(file_path)
    except:
        pass


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
