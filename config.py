import os


class Config:
    PROJECT_ROOT_FOLDER = os.path.dirname(os.path.abspath(__file__))
    DATA_FOLDER = PROJECT_ROOT_FOLDER+"/data"

    # data/ is tiered by what actually depends on it:
    LIVE_DATA_FOLDER = DATA_FOLDER+"/live"            # read by reader/ at request time
    CEFR_MODEL_DATA_FOLDER = DATA_FOLDER+"/cefr_model"  # inputs to cefr_model/{train,test}.py
    USER_LEVEL_DATA_FOLDER = DATA_FOLDER+"/user_level"  # input to user_level_model/train.py
    BUILD_DATA_FOLDER = DATA_FOLDER+"/build"          # intermediate artifacts that produced LIVE_DATA_FOLDER

    ASSETS_FOLDER = PROJECT_ROOT_FOLDER+"/assets"
    OUTPUT_FOLDER = DATA_FOLDER+"/output"
    UPLOAD_FOLDER = DATA_FOLDER+"/uploads"
    LOG_FOLDER = DATA_FOLDER+"/logs"
    MODELS_FOLDER = PROJECT_ROOT_FOLDER+"/models"
