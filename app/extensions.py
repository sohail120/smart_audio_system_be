from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_restx import Api
from flask_migrate import Migrate

db = SQLAlchemy()
cors = CORS()
api = Api(title="CRUD + File Upload API", version="1.0")
migrate = Migrate()