import os
from dotenv import load_dotenv

load_dotenv()


def uploads_folder_name():
    return os.getenv('UPLOADS_DIR', "uploads")
