import sys
from datetime import datetime

from flask import Blueprint, flash, redirect, abort, request
from flask import render_template, url_for
from sqlalchemy import desc

from portal_forum import db
from portal_forum.models import Thread, Album, Track
from flask_login import current_user, login_required
from portal_forum.users.utils import check_image
from portal_forum.main.forms import AlbumForm

main = Blueprint('main', __name__)

def check_image():
    if current_user.is_authenticated:
        return url_for('static', filename='profile_pics/' + current_user.image_file)
    else:
        return "none"

@main.route('/')
@main.route('/home')
def home():
    return render_template('portal-home.html')

@main.route('/forum')
def forum():
    threads = Thread.query.order_by(desc(Thread.date_last_update)).limit(5).all()
    tracks = Track.query.order_by(desc(Track.date_last_update)).limit(5).all()
    return render_template('forum-home.html', image_file=check_image(), threads=threads, tracks=tracks)

@main.route('/admin_panel', methods=['GET','POST'])
@login_required
def admin_panel():
    if not current_user.is_admin:
        abort(403)
    albums = Album.query.all()
    return render_template('admin_panel.html', image_file=check_image(), title="Panel administracyjny", albums=albums)

@main.route('/album//create', methods=['GET','POST'])
@login_required
def create_album():
    if not current_user.is_admin:
        abort(403)
    form = AlbumForm()
    if form.validate_on_submit():
        year = int(datetime.utcnow().year)
        print("_____________________________________________________-", file=sys.stderr)
        print(year, file=sys.stderr)
        print("_____________________________________________________", file=sys.stderr)
        album = Album(title=form.title.data, date_release=form.date_release.data, description=form.description.data)
        db.session.add(album)
        db.session.commit()
        flash('Album dodano pomyślnie!', 'success')
        return redirect(url_for('main.admin_panel'))
    return render_template('create_album.html', title="Dodaj album",
                           form=form, image_file=check_image())

@main.route('/album/<int:album_id>/update', methods=['GET','POST'])
@login_required
def update_album(album_id):
    if not current_user.is_admin:
        abort(403)
    album = Album.query.get_or_404(album_id)
    form = AlbumForm()
    if form.validate_on_submit():
        album.title = form.title.data
        album.date_release = form.date_release.data
        album.description = form.description.data
        db.session.commit()
        flash("Album został zaktualizowany!", 'success')
        return redirect(url_for('main.admin_panel'))
    elif request.method == "GET":
        form.title.data = album.title
        form.description.data = album.description
        form.date_release.data = album.date_release
    return render_template('create_album.html', title="Edytuj album",
                           form=form, image_file=check_image())
@main.route('/album/<int:album_id>/delete', methods=['POST','GET'])
@login_required
def delete_album(album_id):
    if not current_user.is_admin:
        abort(403)
    album = Album.query.get_or_404(album_id)
    db.session.delete(album)
    db.session.commit()
    flash("Album usunięty", 'success')
    return redirect(url_for('main.admin_panel'))