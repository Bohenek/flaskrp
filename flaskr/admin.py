import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, abort
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db
from flaskr.auth import login_required

bp = Blueprint('admin', __name__, url_prefix='/admin')

# Dekorator sprawdzający, czy użytkownik jest adminem
def admin_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None or not g.user['is_admin']:
            flash("You don't have permission to access this page.", "error")
            return redirect(url_for('blog.index')) # lub 'auth.login'
        return view(**kwargs)
    return wrapped_view

@bp.route('/')
@login_required
@admin_required
def index():
    """Strona główna panelu admina - przekierowuje do listy użytkowników"""
    return redirect(url_for('admin.list_users'))

@bp.route('/users')
@login_required
@admin_required
def list_users():
    db = get_db()
    users = db.execute(
        'SELECT id, username, is_admin FROM user ORDER BY username'
    ).fetchall()
    return render_template('admin/users.html', users=users)

@bp.route('/users/add', methods=('GET', 'POST'))
@login_required
@admin_required
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        is_admin = 'is_admin' in request.form # Sprawdza, czy checkbox jest zaznaczony
        db = get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'

        if error is None:
            try:
                db.execute(
                    "INSERT INTO user (username, password, is_admin) VALUES (?, ?, ?)",
                    (username, generate_password_hash(password), 1 if is_admin else 0),
                )
                db.commit()
            except db.IntegrityError:
                error = f"User {username} is already registered."
            else:
                flash(f"User {username} added successfully.")
                return redirect(url_for('admin.list_users'))
        flash(error)
    return render_template('admin/add_user.html')

@bp.route('/users/<int:id>/delete', methods=('POST',))
@login_required
@admin_required
def delete_user(id):
    db = get_db()
    user_to_delete = db.execute('SELECT * FROM user WHERE id = ?', (id,)).fetchone()

    if user_to_delete is None:
        flash("User not found.", "error")
        return redirect(url_for('admin.list_users'))
    
    # Sprawdzenie, czy admin nie próbuje usunąć siebie, jeśli jest jedynym adminem
    if user_to_delete['id'] == g.user['id']:
        admin_count = db.execute('SELECT COUNT(id) FROM user WHERE is_admin = 1').fetchone()[0]
        if admin_count <= 1:
            flash("You cannot delete the only administrator.", "error")
            return redirect(url_for('admin.list_users'))
    
    # Usuwamy posty tego użytkownika
    db.execute('DELETE FROM post WHERE author_id = ?', (id,))
    # Następnie usuwamy użytkownika
    db.execute('DELETE FROM user WHERE id = ?', (id,))
    db.commit()
    flash(f"User {user_to_delete['username']} and their posts have been deleted.")
    return redirect(url_for('admin.list_users'))

@bp.route('/posts/<int:id>/delete', methods=('POST',))
@login_required
@admin_required
def delete_post_admin(id):
    db = get_db()
    post = db.execute('SELECT * FROM post WHERE id = ?', (id,)).fetchone()
    if post is None:
        flash("Post not found.", "error")
    else:
        db.execute('DELETE FROM post WHERE id = ?', (id,))
        db.commit()
        flash(f"Post '{post['title']}' deleted successfully by admin.")
    # Po usunięciu posta przez admina, dobrze jest wrócić do miejsca, skąd akcja była wywołana
    # Najczęściej będzie to strona główna bloga lub strona ze szczegółami posta, jeśli taka istnieje.
    # Można też użyć request.referrer, ale trzeba uważać na bezpieczeństwo.
    return redirect(request.referrer or url_for('blog.index'))

# DODAWANIE ADMINA:
# docker compose exec server flask create-admin admin@ admin@