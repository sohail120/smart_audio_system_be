from flask_restx import Api

api = Api(
    version='1.0',
    title='Smart Audio System API',
    description='API for Smart Audio System',
    doc='/swagger/'
)