from flask import Flask
from app.config import Config
from app.routes.auth_routes import auth_bp
from app.routes.chat_routes import chat_bp
from app.routes.admin_routes import admin_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(admin_bp)

    return app
