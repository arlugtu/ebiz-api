from common.database import get_collection


class CategoryDBService:

    def __init__(self):

        self.item_collection = get_collection('category')


    def find_one(self, item_name):

        return self.item_collection.find_one(
            {'category_name': item_name},
            {'_id': 0}
        )


    def find_all(self, page: int | None, limit: int | None):

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
            {'category_id': {'$in': item_ids}},
            {'_id': 0}
        )
        for item in item_cursor:
            items.append(item)

        return items


    def find_one_by_id(self, item_id):

        return self.item_collection.find_one(
            {'category_id': item_id},
            {'_id': 0}
        )


    def delete_one(self, item_id: str):

        item = self.item_collection.find_one(
            {'category_id': item_id},
            {'_id': 0}
        )
        if item:
            self.item_collection.delete_one(item)
            return 1


    def insert_one(self, item: dict):

        self.item_collection.insert_one(item)
