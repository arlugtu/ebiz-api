from common.database import get_collection


class ItemFileDBService:
    def __init__(self):
        self.item_file_collection = get_collection('item_files')

    def update_many_files(self, query):
        self.item_file_collection.bulk_write(query)

    def insert_file_data(self, data):
        self.item_file_collection.insert_one(data)
