import os


class Config:
    PROJECT_ROOT_FOLDER = os.path.dirname(os.path.abspath(__file__))
    DATA_FOLDER = PROJECT_ROOT_FOLDER+"/data"
    ASSETS_FOLDER = PROJECT_ROOT_FOLDER+"/assets"
    OUTPUT_FOLDER = PROJECT_ROOT_FOLDER+"/data/output"
    UPLOAD_FOLDER = PROJECT_ROOT_FOLDER+"/data/uploads"
    LOG_FOLDER = PROJECT_ROOT_FOLDER+"/data/logs"
    MODELS_FOLDER = PROJECT_ROOT_FOLDER+"/models"
