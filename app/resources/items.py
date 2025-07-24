from flask_restx import Resource, fields, Namespace
from app.services.item_service import (
    get_all_items,
    get_item_by_id,
    create_item,
    update_item,
    delete_item
)

# Create the namespace
items_ns = Namespace('items', description='Item operations')

item_model = items_ns.model('Item', {
    'id': fields.Integer(readonly=True, description='The item identifier'),
    'name': fields.String(required=True, description='The item name'),
    'description': fields.String(description='The item description')
})

@items_ns.route('/')
class ItemList(Resource):
    @items_ns.doc('list_items')
    @items_ns.marshal_list_with(item_model)
    def get(self):
        """List all items"""
        return get_all_items()

    @items_ns.doc('create_item')
    @items_ns.expect(item_model)
    @items_ns.marshal_with(item_model, code=201)
    def post(self):
        """Create a new item"""
        return create_item(items_ns.payload), 201

@items_ns.route('/<int:id>')
@items_ns.response(404, 'Item not found')
@items_ns.param('id', 'The item identifier')
class ItemResource(Resource):
    @items_ns.doc('get_item')
    @items_ns.marshal_with(item_model)
    def get(self, id):
        """Fetch an item given its identifier"""
        item = get_item_by_id(id)
        if not item:
            items_ns.abort(404, "Item not found")
        return item

    @items_ns.doc('update_item')
    @items_ns.expect(item_model)
    @items_ns.marshal_with(item_model)
    def put(self, id):
        """Update an item given its identifier"""
        item = update_item(id, items_ns.payload)
        if not item:
            items_ns.abort(404, "Item not found")
        return item

    @items_ns.doc('delete_item')
    @items_ns.response(204, 'Item deleted')
    def delete(self, id):
        """Delete an item given its identifier"""
        if not delete_item(id):
            items_ns.abort(404, "Item not found")
        return '', 204