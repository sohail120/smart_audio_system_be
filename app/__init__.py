# import os
# from flask import Flask
# from .config import Config
# from .extensions import db, api, cors
# from .resources import ns

# def create_app(config_class=Config):
#     app = Flask(__name__)
#     app.config.from_object(config_class)

#     db.init_app(app)
#     cors.init_app(app)
#     api.init_app(app)

#     with app.app_context():
#         db.create_all()

#     api.add_namespace(ns)

#     return app


from flask import Flask
from .config import Config
from .extensions import db, cors, api, migrate
from .resources import ns

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    cors.init_app(app)
    api.init_app(app)
    migrate.init_app(app, db)

    api.add_namespace(ns)

    return app
