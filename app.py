import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_restx import Api, Resource, fields

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('APP_SECRET_KEY')

# Initialize Swagger
api = Api(
    app, 
    version='1.0', 
    title='Simple CRUD API',
    description='A simple CRUD API with in-memory storage',
    doc='/swagger/'  # Swagger UI will be available at /swagger/
)

# Namespace for our operations
ns = api.namespace('items', description='Item operations')

# In-memory "database"
items_db = {}
current_id = 1

# Model for Swagger documentation
item_model = api.model('Item', {
    'id': fields.Integer(readonly=True, description='The item unique identifier'),
    'name': fields.String(required=True, description='The item name'),
    'description': fields.String(description='The item description')
})

@ns.route('/')
class ItemList(Resource):
    """Shows a list of all items, and lets you POST to add new items"""
    
    @ns.doc('list_items')
    @ns.marshal_list_with(item_model)
    def get(self):
        """List all items"""
        return list(items_db.values())
    
    @ns.doc('create_item')
    @ns.expect(item_model)
    @ns.marshal_with(item_model, code=201)
    def post(self):
        """Create a new item"""
        global current_id
        data = api.payload
        item_id = current_id
        current_id += 1
        item = {
            'id': item_id,
            'name': data['name'],
            'description': data.get('description', '')
        }
        items_db[item_id] = item
        return item, 201

@ns.route('/<int:id>')
@ns.response(404, 'Item not found')
@ns.param('id', 'The item identifier')
class Item(Resource):
    """Show a single item and lets you delete or update it"""
    
    @ns.doc('get_item')
    @ns.marshal_with(item_model)
    def get(self, id):
        """Fetch an item given its identifier"""
        if id not in items_db:
            api.abort(404, "Item not found")
        return items_db[id]
    
    @ns.doc('delete_item')
    @ns.response(204, 'Item deleted')
    def delete(self, id):
        """Delete an item given its identifier"""
        if id not in items_db:
            api.abort(404, "Item not found")
        del items_db[id]
        return '', 204
    
    @ns.doc('update_item')
    @ns.expect(item_model)
    @ns.marshal_with(item_model)
    def put(self, id):
        """Update an item given its identifier"""
        if id not in items_db:
            api.abort(404, "Item not found")
        data = api.payload
        item = items_db[id]
        item.update({
            'name': data['name'],
            'description': data.get('description', item['description'])
        })
        return item

if __name__ == '__main__':
    app.run(debug=True)