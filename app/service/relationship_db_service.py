from common.database import get_collection
from common.logger import module_logger
from schema import Relationship

logger = module_logger(__name__)


class RelationshipDBService:
    def __init__(self):
        self.relationship_collection = get_collection('relationships')

    def add_relationship(self, relationship: Relationship):
        logger.info('Adding relationship process started')
        relationship_id_db = self.relationship_collection.find_one({'parent_id': relationship.parent_id})
        if relationship_id_db:
            logger.debug(f'Adding an existing relationship,'
                         f' Parent: {relationship.parent_id}, Child: {relationship.child_id}')
            inserted = self.relationship_collection.update_one(
                {'parent_id': relationship.parent_id},
                {'$push': {'children': relationship.child_id}}
            )
        else:
            logger.debug(f'Adding a new relationship, Parent: {relationship.parent_id}, Child: {relationship.child_id}')
            inserted = self.relationship_collection.insert_one(
                {'parent_id': relationship.parent_id, 'children': [relationship.child_id]})
        logger.info('Adding relationship process completed')
        return {'message': 'Relationship added successfully'}

    def get_children(self, parent_id):
        relationship_id_db = self.relationship_collection.find_one({'parent_id': parent_id}, {'_id': 0})
        if relationship_id_db is not None and 'children' in relationship_id_db:
            return relationship_id_db.get('children')
        return []
