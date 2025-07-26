# Environment Setup Script

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create data directories
New-Item -ItemType Directory -Path data/question_banks -Force
New-Item -ItemType Directory -Path logs -Force

# Initialize database
# python -m flask db init
# python -m flask db migrate
# python -m flask db upgrade

# Run vendor script setup
.\setup_vendor.ps1

# Create sample topics manifest
Set-Content data/topics_manifest.json @'
[
  {
    "topic_id": "java",
    "filename": "java.json",
    "title": "Java",
    "description": "Core Java concepts, OOP, collections, and more.",
    "icon": "fa-mug-hot"
  },
  {
    "topic_id": "aws",
    "filename": "AWS-AI-Practitioner.json",
    "title": "AWS AI Practitioner",
    "description": "Foundational concepts of AI/ML services on AWS.",
    "icon": "fa-brain"
  }
]
'@

# Create sample question bank
Set-Content data/question_banks/java.json @'
{
  "exam_sets": [
    {
      "name": "Java Core Fundamentals",
      "questions": [
        {
          "id": "java_q001",
          "domain": "JVM Architecture",
          "difficulty": "Easy",
          "question_text": "Which JVM memory area stores method and class-level data?",
          "options": [
            "Heap Area",
            "Stack Area",
            "Method Area",
            "PC Register"
          ],
          "correct_answer_index": 2,
          "explanation": "The Method Area stores per-class structures like runtime constant pool and method data."
        }
      ]
    }
  ]
}
'@

# Create .env file if not exists
if (-not (Test-Path .env)) {
    Set-Content .env @"
# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your_very_secure_secret_key

# Question Bank Paths
QB_MANIFEST_PATH=data/topics_manifest.json
QB_DATA_DIR=data/question_banks/

# Logging Configuration
LOG_LEVEL=DEBUG
LOG_FILE=logs/app.log
ERROR_LOG_FILE=logs/errors.log
"@
}

Write-Host "Setup completed successfully!"
Write-Host "To start the application, run: .\venv\Scripts\activate and then flask run"