import os


class Config:
    PROJECT_ROOT_FOLDER = os.path.dirname(os.path.abspath(__file__))
    DATA_FOLDER = PROJECT_ROOT_FOLDER+"/data"

    # data/ is split by whether prod code reads it directly:
    RAW_DATA_FOLDER = DATA_FOLDER+"/raw"              # only touched by src/intelli_e_reader/data_pipeline/ scripts
    PROCESSED_DATA_FOLDER = DATA_FOLDER+"/processed"  # read directly by reader/ or cefr_model/

    ASSETS_FOLDER = PROJECT_ROOT_FOLDER+"/assets"
    OUTPUT_FOLDER = DATA_FOLDER+"/output"
    UPLOAD_FOLDER = DATA_FOLDER+"/uploads"
    LOG_FOLDER = DATA_FOLDER+"/logs"
    MODELS_FOLDER = PROJECT_ROOT_FOLDER+"/models"
