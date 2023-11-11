import time
import uvicorn

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import (CORSMiddleware)
from starlette.staticfiles import StaticFiles

from common.configs import SELF_DOMAIN
from common.logger import module_logger
from routers import (
    category,
    inventory,
    payment,
    product,
    redeemable_category,
    redeemable_inventory,
    redeemable_product,
    redeemable_transaction,
    subcategory,
    transaction
)
from service.db_service import DBService
from service.oxapay_service import get_payment_information

app = FastAPI()
app.mount('/media', StaticFiles(directory='media'), name='media')
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
    allow_origins=['*']
)
app.include_router(category.router)
app.include_router(inventory.router)
app.include_router(payment.router)
app.include_router(product.router)
app.include_router(redeemable_category.router)
app.include_router(redeemable_inventory.router)
app.include_router(redeemable_product.router)
app.include_router(redeemable_transaction.router)
app.include_router(subcategory.router)
app.include_router(transaction.router)
logger = module_logger(__name__)

scheduler = BackgroundScheduler()


@app.get('/process-transaction')
def process_transaction():

    print('prodcess_transaction')
    db_service = DBService('transaction')
    timestamp = int(time.time())
    query = {
        'expiredAt': {'$lte': timestamp},
        'status': {'$in': ['New', 'Waiting']}
    }
    docs, doc_count = db_service.find_all(query)

    if doc_count == 0:
        return

    inventory_service = DBService('inventory')
    product_service = DBService('product')
    for d in docs:
        if not d.get('trackId'):
            continue

        info = get_payment_information(d['trackId'])
        if info.get('status') == 'Expired':
            # Update Transaction
            query = {'trackId': d['trackId']}
            db_service.find_one_and_update(
                query,
                {'$set': {'status': 'Expired'}}
            )

            # Update Inventory
            query = {'status': 'Reserved', 'trackId': d['trackId']}
            inventory = inventory_service.update_many(
                query,
                {'$set': {'status': 'New'}}
            )

            # Update Product
            if inventory.modified_count > 0 and d.get('product_id'):
                query = {'product_id': d['product_id']}
                product_service.find_one_and_update(
                    query,
                    {'$inc': {'inventory': inventory.modified_count}}
                )


@app.on_event('startup')
async def startup():

    scheduler.start()

    job_id = 'process_transaction'
    scheduler.add_job(
        process_transaction,
        'cron',
        id=job_id,
        minute='*/5'
    )


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
