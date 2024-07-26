from flask import Flask

def create_app():
    app = Flask(__name__)

    with app.app_context():
        from . import api
        app.register_blueprint(api.bp)

    return app
