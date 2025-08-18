python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

flask run

API endpoints: http://localhost:5000/items/

Swagger UI: http://localhost:5000/swagger/
pip freeze > requirements.txt

flask db migrate -m "your message here"
flask db upgrade



docker build -t smart_audio_system_be .
docker build -t my-python-app .
docker run -d -p 5000:5000 my-python-app


 
docker ps -a

