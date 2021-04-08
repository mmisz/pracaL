import sys
from functools import wraps

from flask import render_template, url_for, redirect, flash, request, abort, Blueprint, g, json
from markupsafe import Markup
from sqlalchemy import desc, asc
from portal_forum.user_activity.forms import ThreadForm, PostForm, TrackForm, ScrapForm
from portal_forum import db
from portal_forum.models import Thread, User, Thread_Post, Track, Album, Discussion, Scrap
from flask_login import login_user, current_user, logout_user, login_required
from datetime import datetime
from portal_forum.users.utils import check_image
import re

user_activity = Blueprint('user_activity', __name__)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('users.login', next=request.url))
        return f(*args, **kwargs)

    return decorated_function


def check_image():
    if current_user.is_authenticated:
        return url_for('static', filename='profile_pics/' + current_user.image_file)
    else:
        return "none"


@user_activity.route('/threads', methods=['GET', 'POST'])
def threads():
    strona = request.args.get('strona', 1, type=int)
    threads = Thread.query.order_by(desc(Thread.date_last_update)).paginate(page=strona, per_page=5)
    return render_template('threads.html', title="Wątki", image_file=check_image(), threads=threads)


@user_activity.route('/thread/<int:thread_id>', methods=['GET', 'POST'])
def thread(thread_id):
    thread = Thread.query.get_or_404(thread_id)
    tags = Markup(thread.description)
    posts = Thread_Post.query. \
        filter_by(thread=thread). \
        order_by(asc(Thread_Post.date_posted))
    replies = []
    for post in posts:
        replies.append(Markup(post.reply))
    return render_template('thread.html', title=thread.topic, image_file=check_image(), thread=thread, tags=tags,
                           posts=posts, replies=replies)


@user_activity.route('/thread/new', methods=['GET', 'POST'])
@login_required
def new_thread():
    form = ThreadForm()
    if form.validate_on_submit():
        thread = Thread(topic=form.topic.data, description=form.description.data, author=current_user)
        db.session.add(thread)
        db.session.commit()
        flash("Wątek został dodany", "success")
        return redirect(url_for('main.forum'))
    return render_template('create_thread.html', title="Nowy wątek",
                           legend="Rozpocznij nowy wątek", form=form, image_file=check_image())


@user_activity.route('/thread/<int:thread_id>/update', methods=['GET', 'POST'])
@login_required
def update_thread(thread_id):
    thread = Thread.query.get_or_404(thread_id)
    if thread.author != current_user:
        abort(403)
    form = ThreadForm()
    if form.validate_on_submit():
        thread.topic = form.topic.data
        thread.description = form.description.data
        thread.date_last_update = datetime.strptime(str(datetime.utcnow()), "%Y-%m-%d %H:%M:%S.%f")
        db.session.commit()
        flash("Wątek zaktualizowany!", 'success')
        return redirect(url_for('user_activity.thread', thread_id=thread.id))
    elif request.method == "GET":
        form.topic.data = thread.topic
        form.description.data = thread.description
    return render_template('create_thread.html', title="Edytuj wątek",
                           legend="Edytuj wątek", form=form, image_file=check_image())


@user_activity.route('/thread/<int:thread_id>/delete', methods=['POST'])
@login_required
def delete_thread(thread_id):
    thread = Thread.query.get_or_404(thread_id)
    if thread.author != current_user and not current_user.is_admin:
        abort(403)
    db.session.delete(thread)
    db.session.commit()
    flash("Wątek usunięty", 'success')
    return redirect(url_for('main.forum', thread_id=thread.id))


@user_activity.route('/thread/<int:thread_id>/reply', methods=['GET', 'POST'])
@login_required
def thread_reply(thread_id):
    form = PostForm()
    if form.validate_on_submit():
        post = Thread_Post(reply=form.reply.data, author=current_user, thread_id=thread_id)
        db.session.add(post)
        db.session.commit()
        flash("Odpowiedź została dodana", "success")
        return redirect(url_for('user_activity.thread', thread_id=thread_id))
    return render_template('thread_reply.html', title="Rozwiń wątek",
                           legend="Odpowiedz", form=form, image_file=check_image(),
                           thread_id=thread_id, reply_id=None)


@user_activity.route('/thread/<int:thread_id>/reply_to/<int:post_id>', methods=['GET', 'POST'])
@login_required
def quote_thread_post(thread_id, post_id):
    post = Thread_Post.query.get_or_404(post_id)
    form = PostForm()
    date_posted = str(datetime.strptime(str(post.date_posted), "%Y-%m-%d %H:%M:%S.%f"))
    date_posted = date_posted.split(".")[0]
    quote = "<div>" \
            "<div style='background:#eeeeee;border:1px solid #cccccc;padding:5px 10px;'>" \
            "<b>" + post.author.username + "</b> powiedział " + date_posted + \
            "</div>" \
            "<blockquote class='cke_contents_ltr blockquote'>" + post.reply + "</blockquote>" \
                                                                              "<p></p></div>"
    if form.validate_on_submit():
        post = Thread_Post(reply=form.reply.data, author=current_user, thread_id=thread_id)
        db.session.add(post)
        db.session.commit()
        flash("Odpowiedź została dodana", "success")
        return redirect(url_for('user_activity.thread', thread_id=thread_id))
    elif request.method == "GET":
        form.reply.data = Markup(quote)
    return render_template('thread_reply.html', title="Rozwiń wątek",
                           legend="Odpowiedz użytkownikowi " + post.author.username, form=form,
                           image_file=check_image(),
                           thread_id=thread_id, reply_id=None)


@user_activity.route('/thread/<int:thread_id>/reply/<int:post_id>/update', methods=['GET', 'POST'])
@login_required
def update_thread_post(post_id, thread_id):
    thread = Thread.query.get_or_404(thread_id)
    post = Thread_Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.reply = form.reply.data
        post.date_last_update = datetime.strptime(str(datetime.utcnow()), "%Y-%m-%d %H:%M:%S.%f")
        db.session.commit()
        flash("Odpowiedź została zaktualizowana!", 'success')
        return redirect(url_for('user_activity.thread', thread_id=thread.id))
    elif request.method == "GET":
        form.reply.data = post.reply
    return render_template('thread_reply.html', title="Edytuj odpowiedź",
                           legend="Edytuj odpowiedź", form=form, image_file=check_image())


@user_activity.route('/thread/<int:thread_id>/reply/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_thread_post(thread_id, post_id):
    thread = Thread.query.get_or_404(thread_id)
    post = Thread_Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash("Odpowiedź została usunięta", 'success')
    return redirect(url_for('user_activity.thread', thread_id=thread.id))


@login_required
@user_activity.route('/track/<int:track_id>', methods=['GET', 'POST'])
def track(track_id):
    track = Track.query.get_or_404(track_id)
    tags = Markup(track.lyrics)
    tags_description = Markup(track.description)
    return render_template('track.html', title=track.title, image_file=check_image(), track=track, tags=tags,
                           tags_description=tags_description)


@user_activity.route('/tracks', methods=['GET', 'POST'])
@login_required
def tracks():
    strona = request.args.get('strona', 1, type=int)
    tracks = Track.query.order_by(desc(Track.date_last_update)).paginate(page=strona, per_page=5)
    return render_template('tracks.html', title="Utwory", image_file=check_image(), tracks=tracks)


@user_activity.route('/tracks/new', methods=['GET', 'POST'])
@login_required
def new_track():
    form = TrackForm()
    albums = Album.query.all()

    if form.validate_on_submit():
        albums_list = request.form.getlist("albums")
        tags = form.lyrics.data
        tags = tags.replace("<p>", '')
        tags = tags.replace("</p>", "<br/>")
        track = Track(title=form.title.data, lyrics=tags, lyrics_with_scraps=tags, author=current_user,
                      date_release=form.date_release.data, lyrics_by=form.lyrics_by.data,
                      description=form.description.data)

        for cd in albums_list:
            album = Album.query.filter_by(id=int(cd)).first_or_404()

            track.albums.append(album)
        db.session.add(track)
        db.session.commit()

        new_track = Track.query.order_by(Track.id.desc()).first()
        discussion = Discussion(track_id=new_track.id)
        db.session.add(discussion)
        db.session.commit()
        flash("Utwór został dodany", "success")
        return redirect(url_for('user_activity.tracks'))

    return render_template('create_track.html', title="Nowy Utwór", albums=albums,
                           legend="Dodaj nowy utwór", form=form, image_file=check_image())


@user_activity.route('/track/<int:track_id>/update', methods=['GET', 'POST'])
@login_required
def update_track(track_id):
    track = Track.query.get_or_404(track_id)
    if track.author != current_user:
        abort(403)
    form = TrackForm()
    if form.validate_on_submit():
        tags = form.lyrics.data
        tags = tags.replace("<p>", '')
        tags = tags.replace("</p>", "<br/>")

        track.title = form.title.data
        track.lyrics = tags
        track.lyrics_with_scraps = tags
        track.description = form.description.data
        track.date_release = form.date_release.data
        track.lyrics_by = form.lyrics_by.data
        track.date_last_update = datetime.strptime(str(datetime.utcnow()), "%Y-%m-%d %H:%M:%S.%f")
        for scrap in track.scraps:
            db.session.delete(scrap)
        db.session.commit()
        flash("Wątek zaktualizowany!", 'success')
        return redirect(url_for('user_activity.track', track_id=track.id))
    elif request.method == "GET":
        form.title.data = track.title
        form.lyrics.data = track.lyrics
        form.description.data = track.description
        form.date_release.data = track.date_release
        form.lyrics_by.data = track.lyrics_by
    return render_template('create_track.html', title="Edytuj utwór",
                           legend="Edytuj utwór", form=form, image_file=check_image())


@user_activity.route('/track/<int:track_id>/delete', methods=['POST'])
@login_required
def delete_track(track_id):
    track = Track.query.get_or_404(track_id)
    if track.author != current_user and not current_user.is_admin:
        abort(403)
    discussion = Discussion.query.filter_by(track_id=track_id).first()
    db.session.delete(discussion)
    db.session.delete(track)
    db.session.commit()
    flash("Utwór usunięty", 'success')
    return redirect(url_for('main.forum'))


@login_required
@user_activity.route('/track/<int:track_id>/scraps', methods=['GET', 'POST'])
def scraps(track_id):
    track = Track.query.get_or_404(track_id)
    tags = track.lyrics_with_scraps
    scrap_descriptions = []
    for scrap in track.scraps:
        scrap_descriptions.append(scrap.description)
    scrap_descriptions = json.dumps(scrap_descriptions)

    tags = Markup(tags)
    form = ScrapForm()
    if form.validate_on_submit():
        track.lyrics_with_scraps = form.lyrics_with_scraps.data
        new_scrap = Scrap(description=form.description.data, track_id=track_id,
                          author=current_user)
        db.session.add(new_scrap)
        db.session.commit()
        flash("Fragment został oznaczony", "success")
        return redirect(url_for('user_activity.scraps', track_id=track_id))

    return render_template('scraps.html', title=track.title, image_file=check_image(), track=track, tags=tags,
                           form=form, scrap_descriptions=scrap_descriptions)


@login_required
@user_activity.route("/user/activity/<string:username>")
def user_actions(username):
    strona = request.args.get('strona', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    threads = Thread.query. \
        filter_by(author=user). \
        order_by(desc(Thread.date_posted)). \
        paginate(page=strona, per_page=5)
    return render_template('user_activity.html', title="Aktywność użytkownika", image_file=check_image(),
                           threads=threads, user=user)


'''
document.getElementsByClassName('postcell')[0].addEventListener('mouseup',function(e)
{
        var txt = document.getElementsByClassName('postcell')[0].innerText;
        var selection = window.getSelection();
        var start = selection.anchorOffset;
        var end = selection.focusOffset;
        if (start >= 0 && end >= start){
    	    console.log("start: " + start);
    	    console.log("end: " + end);
            console.log(txt.substring(start,end));
        }
});
'''
