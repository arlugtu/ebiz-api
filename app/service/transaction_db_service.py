from common.database import get_collection


class TransactionDBService:
    def __init__(self):
        self.transaction_collection = get_collection('transactions')

    def insert(self, data):
        self.transaction_collection.insert_one(data)

