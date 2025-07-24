# 🚀 Flask CRUD API with Swagger

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Flask](https://img.shields.io/badge/flask-2.3.2-green)
![Swagger](https://img.shields.io/badge/swagger-supported-yellow)

A production-ready Flask API template featuring CRUD operations, Swagger documentation, and modular architecture.

## 📦 Features
- **Full CRUD Operations** (Create, Read, Update, Delete)
- **Interactive Swagger UI** documentation
- **In-Memory Storage** (No database required)
- **Modular Structure** (Models, Services, Resources)
- **Environment Configuration** (.env support)
- **Production-Ready** (WSGI compatible)

## 🚀 Quick Start
```bash
# Clone repository
git clone https://github.com/yourusername/flask-crud-api.git
cd flask-crud-api

# Create virtual environment
python -m venv venv

# Activate environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the API
python run.py


flask-crud-api/
├── app/
│   ├── __init__.py         # App factory
│   ├── config.py           # Configuration
│   ├── extensions.py       # Flask extensions
│   ├── models/             # Data models
│   ├── resources/          # API endpoints
│   └── services/           # Business logic
├── tests/                  # Unit tests
├── .env                    # Environment variables
├── requirements.txt        # Dependencies
└── run.py                  # Entry point

FLASK_APP=run.py
FLASK_ENV=development
APP_SECRET_KEY=your-secret-key-here

# Build image
docker build -t flask-api .

# Run container
docker run -dp 5000:5000 flask-api

# Run tests
pytest tests/

# Generate coverage report
pytest --cov=app --cov-report=html