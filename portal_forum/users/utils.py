from flask import url_for
from portal_forum import app
from flask_login import current_user
import secrets
import os

def check_image():
    if current_user.is_authenticated:
        return url_for('static', filename='profile_pics/' + current_user.image_file)
    else:
        return "none"

def save_image(image):
    rnd_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(image.filename)
    image_name = rnd_hex + f_ext
    image_path = os.path.join(app.root_path, 'static/profile_pics', image_name)
    image.save(image_path)
    return image_name