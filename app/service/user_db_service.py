from common.database import get_collection


class UserDBService:
    def __init__(self):
        self.user_collection = get_collection('users')

    def insert_or_update(self, user_data):
        user = self.user_collection.find_one({'user_id': user_data.get('user_id')})
        if user:
            existing_redeem_points = user.get('redeem_points')
            new_redeem_points = existing_redeem_points + user.get('redeem_points')
            self.user_collection.update_one(
                {'user_id': user_data.get('user_id')},
                {'$set': {'redeem_points': new_redeem_points}}
            )
        else:
            self.user_collection.insert_one(user_data)
