from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ab62f053dc6f3bd97654d729bb670fad'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "Zaloguj się aby uzyskać dostęp do strony"
login_manager.login_message_category = 'info'

from portal_forum.users.routes import users
from portal_forum.user_activity.routes import user_activity
from portal_forum.main.routes import main

app.register_blueprint(users)
app.register_blueprint(user_activity)
app.register_blueprint(main)






