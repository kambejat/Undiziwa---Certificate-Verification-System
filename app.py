from flask import Flask
from flask_migrate import Migrate     # ← Add this
from models import db
from api.views import api
from schema.schemas import ma
from config import Config
import os 

migrate = Migrate()  # ← Create migrate instance

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Create upload folder here
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    db.init_app(app)
    ma.init_app(app)
    migrate.init_app(app, db)
    app.register_blueprint(api)

    return app

