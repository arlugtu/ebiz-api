from common.database import get_collection
from pymongo.collection import ReturnDocument


class DBService:

    def __init__(self, name):

        self.collection = get_collection(name)


    def find_all(
        self,
        query: dict,
        page: int | None = None,
        limit: int | None = None,
        order_by: str | None = None,
        sort_by: int | None = 1
    ):

        items = self.collection.find(query, {'_id': 0})
        if order_by and sort_by:
            items = items.sort(order_by, sort_by)

        if limit and page:
            skip = (page - 1) * limit
            items = items.skip(skip).limit(limit)

        total_items = self.collection.count_documents(query)
        items = [item for item in items]

        return items, total_items


    def find_one(self, query: dict):

        return self.collection.find_one(query, {'_id': 0})


    def find_one_and_delete(self, query: dict):

        return self.collection.find_one_and_delete(query)


    def find_one_and_update(
        self,
        query: dict,
        data: dict,
        return_document=ReturnDocument.AFTER
    ):

        return self.collection.find_one_and_update(
            query,
            data,
            return_document=return_document
        )


    def delete_many(self, query: dict):

        return self.collection.delete_many(query)


    def insert_one(self, item: dict):

        return self.collection.insert_one(item)


    def insert_many(self, items: list):

        return self.collection.insert_many(items)


    def update_many(self, query: dict, data: dict):

        return self.collection.update_many(query, data)
