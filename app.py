import re
from datetime import datetime, timezone
from datetime import timedelta
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect
from flask import Flask
from unicodedata import normalize

from config.settings import Config
from core.question_bank_loader import QuestionBankLoader
import os

# Load environment variables first
load_dotenv()

# Instantiate question loader
qb_loader = QuestionBankLoader()

# Create Flask app
app = Flask(__name__)
app.config.from_object(Config)
# app.secret_key = Config.SECRET_KEY
app.secret_key = os.getenv('SECRET_KEY', 'fallback-secret-key')

# Add CSRF protection
csrf = CSRFProtect(app)


# Import routes & Register Blueprint
from routes import bp as main_bp
app.register_blueprint(main_bp)

# Inject current UTC time into templates
@app.context_processor
def inject_now():
    """Inject current year into templates"""
    return {'now': datetime.now(timezone.utc)}

# Convert seconds into MM:SS format
@app.template_filter('format_duration')
def format_duration_filter(seconds):
    """Format duration in seconds to HH:MM:SS"""
    # delta = timedelta(seconds=seconds)
    # hours, remainder = divmod(delta.seconds, 3600)
    # minutes, seconds = divmod(remainder, 60)
    # return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    try:
        seconds = int(seconds)
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    except:
        return "00:00"

# Slugify strings to URL-safe text
@app.template_filter('slugify')
def slugify_filter(text):
    text = str(text)
    # Convert to ASCII
    text = normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    # Remove special characters
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    # Replace spaces with dashes
    return re.sub(r'[-\s]+', '-', text)

# Run the app
if __name__ == '__main__':
    app.run()