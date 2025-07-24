from flask_restx import Resource, fields, Namespace
from app.services.item_service import (
    # get_all_upload_file,
    get_item_by_id,
    create_item,
    update_item,
    delete_item
)

# Create the namespace
upload_file_ns = Namespace('upload_file', description='Item operations')

item_model = upload_file_ns.model('Item', {
    'id': fields.Integer(readonly=True, description='The item identifier'),
    'name': fields.String(required=True, description='The item name'),
    'description': fields.String(description='The item description')
})

@upload_file_ns.route('/')
class ItemList(Resource):
    @upload_file_ns.doc('list_upload_file')
    @upload_file_ns.marshal_list_with(item_model)
    def get(self):
        """List all upload_file"""
        return get_all_upload_file()

    @upload_file_ns.doc('create_item')
    @upload_file_ns.expect(item_model)
    @upload_file_ns.marshal_with(item_model, code=201)
    def post(self):
        """Create a new item"""
        return create_item(upload_file_ns.payload), 201

@upload_file_ns.route('/<int:id>')
@upload_file_ns.response(404, 'Item not found')
@upload_file_ns.param('id', 'The item identifier')
class ItemResource(Resource):
    @upload_file_ns.doc('get_item')
    @upload_file_ns.marshal_with(item_model)
    def get(self, id):
        """Fetch an item given its identifier"""
        item = get_item_by_id(id)
        if not item:
            upload_file_ns.abort(404, "Item not found")
        return item

    @upload_file_ns.doc('update_item')
    @upload_file_ns.expect(item_model)
    @upload_file_ns.marshal_with(item_model)
    def put(self, id):
        """Update an item given its identifier"""
        item = update_item(id, upload_file_ns.payload)
        if not item:
            upload_file_ns.abort(404, "Item not found")
        return item

    @upload_file_ns.doc('delete_item')
    @upload_file_ns.response(204, 'Item deleted')
    def delete(self, id):
        """Delete an item given its identifier"""
        if not delete_item(id):
            upload_file_ns.abort(404, "Item not found")
        return '', 204