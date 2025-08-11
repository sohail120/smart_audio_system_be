from flask_restx import fields

def register_models(api):
    file_model = api.model('File', {
        'id': fields.String(readonly=True, description='The file identifier'),
        'status': fields.Integer(description='File processing status'),
    })
    return file_model
