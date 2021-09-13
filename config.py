import os


class Config:
    PROJECT_ROOT_FOLDER = os.path.dirname(os.path.abspath(__file__))
    DATA_FOLDER = PROJECT_ROOT_FOLDER+"/data_files"
