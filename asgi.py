from asgiref.wsgi import WsgiToAsgi
from app import app as flask_app, init_db

init_db()

app = WsgiToAsgi(flask_app)
