from flask import Flask
from .config import Config

def create_app():
    # (optional) load .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        pass

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    from .main import bp as main_bp
    app.register_blueprint(main_bp)   # <-- this must run

    return app
