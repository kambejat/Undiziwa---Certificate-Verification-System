from flask import Blueprint

api = Blueprint('api', __name__)

# Import all route modules
from .auth_routes import *
from .institution_routes import *
from .user_routes import *
from .certificate_routes import *
from .verification_routes import *
from .views import *
