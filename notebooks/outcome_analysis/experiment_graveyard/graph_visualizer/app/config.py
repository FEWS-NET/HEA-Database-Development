import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")

    # Project root = parent of "app" folder
    _APP_DIR = os.path.dirname(os.path.abspath(__file__))
    _ROOT = os.path.dirname(_APP_DIR)

    # Default workbook path (override with env var DEFAULT_WORKBOOK_PATH)
    DEFAULT_WORKBOOK_PATH = os.environ.get(
        "DEFAULT_WORKBOOK_PATH",
        os.path.join(_ROOT, "LIAS_Senegal.xlsx")  # change if you like
    )

    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join(_ROOT, "instance", "uploads"))
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB