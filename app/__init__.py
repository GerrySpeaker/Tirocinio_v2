# app/__init__.py
from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config['DEBUG'] = True

    # Registra le rotte (il Blueprint)
    from app.routes import main
    app.register_blueprint(main)

    return app