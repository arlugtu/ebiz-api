import os
import uuid

from datetime import datetime
from typing import List

import uvicorn
from fastapi import FastAPI, Form, HTTPException, UploadFile
from fastapi.middleware.cors import (CORSMiddleware)
from pymongo import UpdateMany
from starlette import status
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles

from bot_engine import BotEngineUpdate
from common.configs import SELF_DOMAIN
from common.logger import module_logger
from payment_handler import PaymentHandler
from schema import (
    BaseResponse,
    Category,
    CategoryResponse,
    Inventory,
    Product,
    ProductResponse,
    Subcategory,
    ItemIn,
    PaginatedItemListResponse,
    Relationship,
    ResModel
)
from service.category_db_service import CategoryDBService
from service.inventory_db_service import InventoryDBService
from service.product_db_service import ProductDBService
from service.subcategory_db_service import SubcategoryDBService

from service.file_writer_service import FileWriter
from service.graph_service import GraphService
from service.item_file_path_db_service import ItemFileDBService
from service.relationship_db_service import RelationshipDBService

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
    try:
        bot_engine = BotEngineUpdate()
        bot_engine.restart_bot_engine()
    except Exception as e:
        logger.error(f'{e}')

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

    try:
        bot_engine = BotEngineUpdate()
        bot_engine.restart_bot_engine()
    except Exception as e:
        logger.error(f'{e}')

    return id


@app.post('/inventory', response_model=Inventory)
async def create_inventory(item: Inventory):

    db_service = InventoryDBService()

    item.inventory_id = str(uuid.uuid4().hex)
    item_dict = item.model_dump()
    db_service.insert_one(item_dict)
    try:
        bot_engine = BotEngineUpdate()
        bot_engine.restart_bot_engine()
    except Exception as e:
        logger.error(f'{e}')

    return item


@app.get('/inventory/{id:str}')
def get_inventory_by_product_id(id):

    db_service = InventoryDBService()
    docs, doc_count = db_service.find_all(id)

    return docs


@app.delete('/inventory/{id:str}')
def delete_inventory(id):

    db_service = InventoryDBService()
    doc = db_service.find_one_by_id(id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Inventory does not exists.'
        )

    if db_service.delete_one(id):
        # Update Product
        db_service = ProductDBService()
        product = db_service.find_one_by_id(doc['product_id'])
        if product:
            _product = {
                'inventory': product['inventory'] - 1
            }
            db_service.update_one(doc['product_id'], _product)

        # Delete File
        delete_file(doc['file_path'])

    try:
        bot_engine = BotEngineUpdate()
        bot_engine.restart_bot_engine()
    except Exception as e:
        logger.error(f'{e}')

    return id


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


@app.post('/inventory-upload/{product_id:str}', response_model=BaseResponse)
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
    product = db_service.find_one_by_id(product_id)
    if product:
        _product = {
            'inventory': product['inventory'] + len(files)
        }
        db_service.update_one(product_id, _product)

    try:
        bot_engine = BotEngineUpdate()
        bot_engine.restart_bot_engine()
    except Exception as e:
        logger.error(f'{e}')

    return BaseResponse(
        message='Files successfully uploaded.',
        status=200
    )


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
    try:
        bot_engine = BotEngineUpdate()
        bot_engine.restart_bot_engine()
    except Exception as e:
        logger.error(f'{e}')

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
    try:
        bot_engine = BotEngineUpdate()
        bot_engine.restart_bot_engine()
    except Exception as e:
        logger.error(f'{e}')

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
    try:
        bot_engine = BotEngineUpdate()
        bot_engine.restart_bot_engine()
    except Exception as e:
        logger.error(f'{e}')

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

    try:
        bot_engine = BotEngineUpdate()
        bot_engine.restart_bot_engine()
    except Exception as e:
        logger.error(f'{e}')

    return id


def delete_file(file_path):

    try:
        os.remove(file_path)
    except:
        pass


'''
@app.post("/bulk-upload")
async def bulk_image_upload(
        files: List[UploadFile],
        item_ids: List[str] = Form(...)
):

    if len(item_ids) != len(files):
        raise HTTPException(status_code=400, detail="Number of sub-category IDs and files must match.")

    uploaded_files_list = []
    file_writer = FileWriter()
    file_paths = await file_writer.save(files)
    logger.debug(f'File Paths {file_paths}')

    update_operations = []
    for item_id, file_path in zip(item_ids, file_paths):
        uploaded_files_list.append({"item_id": item_id, "location": f'{SELF_DOMAIN}{file_path}'})
        filter_query = {"item_id": item_id}
        update_operation = {
            "$set": {"location": file_path}
        }
        update_operations.append(UpdateMany(filter_query, update_operation))

    item_file_db_service = ItemFileDBService()
    item_file_db_service.update_many_files(update_operations)

    return {"message": "Bulk image upload successful", "uploaded_files": uploaded_files_list}


@app.get('/products')
def get_all_products(page: int | None = None, limit: int | None = None):

    logger.info('Get all product process started')
    item_db_service = ItemDBService()
    products, doc_count = item_db_service.find_all_products(page, limit)
    if page is None and limit is None:
        page = 1
        limit = doc_count

    paginated_response = PaginatedItemListResponse(result=products, page=page, limit=limit, total=doc_count)
    logger.info('Get all product process completed')

    return paginated_response


@app.get('/subcategories/{parent_id}')
def get_all_subcategories(parent_id, page: int | None = None, limit: int | None = None):

    relationship_db_service = RelationshipDBService()
    children_list = relationship_db_service.get_children(parent_id)
    item_db_service = ItemDBService()

    return item_db_service.find_from_ids(children_list)


@app.post('/relationship')
def add_one_relationship(relationship: Relationship):

    item_db_service = ItemDBService()
    item_db_service.update_has_children(relationship.parent_id, True)
    relationship_db_service = RelationshipDBService()

    return relationship_db_service.add_relationship(relationship)


@app.post('/{item_id}', response_model=ResModel)
async def add_file_inventory_for_item(
        item_id: str,
        file: UploadFile,
):

    file_writer = FileWriter()
    path = await file_writer.save_single(file)
    data = {
        'item_id': item_id,
        'purchased': False,
        'location': path
    }
    logger.debug(f'Sub Data {data}')
    item_file_db_service = ItemFileDBService()
    item_file_db_service.insert_file_data(data)
    data['location'] = f"{SELF_DOMAIN}{data['location']}"
    item_db_service = ItemDBService()
    item_db_service.update_inventory(item_id, 1)
    try:
        bot_engine = BotEngineUpdate()
        bot_engine.restart_bot_engine()
    except Exception as ex:
        logger.error(f'{ex}')

    return data


@app.post("/payment/handler")
async def receive_webhook_data(data: dict):

    logger.debug(f'Payment Data: {data}')
    payment_handler = PaymentHandler()
    payment_handler.handle_payment(data)

    return data


@app.post("/item/media")
async def add_media_file_to_item(
        item_id: str,
        file: UploadFile,
):

    print(item_id)
    file_writer = FileWriter()
    file_path, file_type = await file_writer.save_media_get_details(file)
    item_db_service = ItemDBService()

    return item_db_service.update_media_details(item_id, file_path, file_type)


@app.get("/graph")
async def get_graph():

    graph_service = GraphService()
    graph = graph_service.create_graph()

    return graph
'''


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
