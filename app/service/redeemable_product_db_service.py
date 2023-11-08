from common.database import get_collection


class RedeemableProductDBService:

    def __init__(self):

        self.item_collection = get_collection('redeemable_product')


    def find_one(self, category_id, item_name):

        return self.item_collection.find_one(
            {
                'category_id': category_id,
                'product_name': item_name
            },
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


    def find_all_by_category_id(self, category_id):

        item_cursor = self.item_collection.find(
            {'category_id': category_id},
            {'_id': 0}
        )

        item_list = [item for item in item_cursor]

        return item_list


    def find_from_ids(self, item_ids: list):

        items = []
        item_cursor = self.item_collection.find(
            {'product_id': {'$in': item_ids}},
            {'_id': 0}
        )
        for item in item_cursor:
            items.append(item)

        return items


    def find_one_by_id(self, item_id):

        return self.item_collection.find_one(
            {'product_id': item_id},
            {'_id': 0}
        )


    def find_one_and_update(self, item_id, query):

        return self.item_collection.find_one_and_update(
            {'product_id': item_id},
            query
        )


    def insert_one(self, item: dict):

        self.item_collection.insert_one(item)


    def update_one(self, item_id: str, item: dict):

        return self.item_collection.update_one(
            {'product_id': item_id},
            {'$set': item}
        )


    def delete_one(self, item_id: str):

        item = self.item_collection.find_one(
            {'product_id': item_id},
            {'_id': 0}
        )
        if item:
            self.item_collection.delete_one(item)
            return 1


    def delete_many(self, query: dict):

        self.item_collection.delete_many(query)
