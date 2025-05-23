from flask import Flask, render_template
from users.controllers.user_controller import user_controller
from db.db import db
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config.from_object('config.Config')
db.init_app(app)

# Registrando el blueprint del controlador de usuarios
app.register_blueprint(user_controller)

if __name__ == '__main__':
    app.run()
