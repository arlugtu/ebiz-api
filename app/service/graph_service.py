from common.configs import DNS_URL
from service.product_db_service import ProductDBService
from service.relationship_db_service import RelationshipDBService


class GraphService:

    def create_graph(self):

        graph = []

        '''
        item_service = ProductDBService()
        all_products = item_service.find_item_by_category('product')
        for product in all_products:
            if product:
                if product and product['has_children']:
                    product['children'] = self.get_children(product['item_id'])
                else:
                    product['children'] = []

                if 'media' in product and product['media']:
                    product['media'] = f"{DNS_URL}/{product['media']}"

                graph.append(product)
        '''

        return graph

    def get_children(self, parent_id):

        child_list = []

        '''
        relationship_service = RelationshipDBService()
        item_service = ProductDBService()
        children = relationship_service.get_children(parent_id=parent_id)
        for child in children:
            child_item = item_service.find_one_by_id(child)
            if child_item:
                if child_item['has_children']:
                    child_item['children'] = self.get_children(child)
                else:
                    child_item['children'] = []

                if 'media' in child_item and child_item['media']:
                    child_item['media'] = f"{DNS_URL}/{child_item['media']}"

                child_list.append(child_item)
        '''

        return child_list
