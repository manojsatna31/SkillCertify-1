import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path('.') / '.env'

load_dotenv(dotenv_path=env_path)


class Config:
    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')

    # Question Bank
    QB_MANIFEST_PATH = os.getenv('QB_MANIFEST_PATH', 'data/topics_manifest.json')
    QB_DATA_DIR = os.getenv('QB_DATA_DIR', 'data/question_banks/')

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
    ERROR_LOG_FILE = os.getenv('ERROR_LOG_FILE', 'logs/errors.log')

    # Session
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes


    # Exam Settings
    EXAM_TIME_LIMITS = {
        'easy': 45,  # minutes
        'medium': 60,
        'hard': 90
    }
config = Config()