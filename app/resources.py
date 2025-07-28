import os
from flask import request, current_app
from flask_restx import Namespace, Resource, fields ,reqparse
from .models import Item
from .extensions import db
from werkzeug.datastructures import FileStorage

ns = Namespace('items', description='CRUD operations and file upload')

item_model = ns.model('Item', {
    'id': fields.Integer(readonly=True),
    'name': fields.String(required=True),
    'file_path': fields.String(readonly=True)
})

@ns.route('/')
class ItemList(Resource):
    @ns.marshal_list_with(item_model)
    def get(self):
        return Item.query.all()

    @ns.expect(item_model, validate=True)
    @ns.marshal_with(item_model)
    def post(self):
        data = request.json
        item = Item(name=data['name'])
        db.session.add(item)
        db.session.commit()
        return item, 201

@ns.route('/<int:id>')
@ns.param('id', 'The item identifier')
class ItemResource(Resource):
    @ns.marshal_with(item_model)
    def get(self, id):
        return Item.query.get_or_404(id)

    @ns.expect(item_model)
    @ns.marshal_with(item_model)
    def put(self, id):
        item = Item.query.get_or_404(id)
        data = request.json
        item.name = data['name']
        db.session.commit()
        return item

    def delete(self, id):
        item = Item.query.get_or_404(id)
        db.session.delete(item)
        db.session.commit()
        return '', 204

upload_model = ns.parser()
upload_parser = reqparse.RequestParser()
upload_parser.add_argument('file', location='files', type=FileStorage, required=True, help='The file to upload')
upload_parser.add_argument('name', location='form', type=str, required=True, help='Name of the item')

@ns.route('/upload')
class FileUpload(Resource):
    @ns.expect(upload_parser)
    def post(self):
        args = upload_parser.parse_args()
        file = args['file']
        name = args['name']

        if not file:
            return {'message': 'No file uploaded'}, 400

        filename = file.filename
        upload_dir = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)

        item = Item(name=name, file_path=file_path)
        db.session.add(item)
        db.session.commit()

        return {'message': 'File uploaded', 'file_path': file_path, 'item_id': item.id}, 201
