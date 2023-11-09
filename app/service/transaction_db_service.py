from common.database import get_collection


class TransactionDBService:

    def __init__(self):

        self.item_collection = get_collection('transaction')


    def find_one(self, tx_id):

        return self.item_collection.find_one({'tx_id': tx_id}, {'_id': 0})


    def find_all(self, page: int | None = None, limit: int | None = None):

        item_cursor = self.item_collection.find({}, {'_id': 0})
        if limit and page:
            skip = (page - 1) * limit
            item_cursor = item_cursor.skip(skip).limit(limit)

        doc_count = self.item_collection.count_documents({})
        item_list = [item for item in item_cursor]

        return item_list, doc_count


    def find_from_ids(self, item_ids: list):

        items = []
        item_cursor = self.item_collection.find(
            {'trackId': {'$in': item_ids}},
            {'_id': 0}
        )
        for item in item_cursor:
            items.append(item)

        return items


    def find_one_by_id(self, item_id):

        return self.item_collection.find_one(
            {'trackId': item_id},
            {'_id': 0}
        )


    def find_one_and_update(self, item_id, query):

        return self.item_collection.find_one_and_update(
            {'trackId': item_id},
            query
        )


    def insert_one(self, item: dict):

        self.item_collection.insert_one(item)


    def delete_one(self, item_id: str):

        item = self.item_collection.find_one(
            {'subcategory_id': item_id},
            {'_id': 0}
        )
        if item:
            self.item_collection.delete_one(item)
            return 1


    def delete_many(self, query: dict):

        self.item_collection.delete_many(query)
