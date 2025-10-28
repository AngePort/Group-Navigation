from flask import Flask
from db import db_init, close_db
from routes import profiles_bp


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    # default database path (file under instance/). Tests should override DATABASE when needed.
    app.config.setdefault("DATABASE", "instance/app.db")

    if test_config:
        app.config.update(test_config)

    db_init(app)
    app.register_blueprint(profiles_bp, url_prefix="/profiles")
    app.teardown_appcontext(close_db)

    @app.route("/")
    def index():
        return {"app": "Driving Navigation (prototype)", "status": "ok"}

    return app
