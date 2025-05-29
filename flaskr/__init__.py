import os
import click
from flask import Flask
from werkzeug.security import generate_password_hash


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev', # Zmień na coś bezpiecznego w produkcji!
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        app.logger.error(f"Could not create instance folder {app.instance_path}: {e}")
        pass

    # a simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import blog
    app.register_blueprint(blog.bp)
    app.add_url_rule('/', endpoint='index') # Ustawia blog.index jako stronę główną

    from . import admin # Importujemy nowy blueprint
    app.register_blueprint(admin.bp) # Rejestrujemy go

    # Dodajemy komendę CLI do tworzenia admina
    @app.cli.command('create-admin')
    @click.argument('username')
    @click.argument('password')
    def create_admin_command(username, password):
        """Creates a new admin user."""
        # Musimy uzyskać kontekst aplikacji, aby móc korzystać z get_db
        with app.app_context():
            db_conn = db.get_db()
            error = None
            try:
                db_conn.execute(
                    "INSERT INTO user (username, password, is_admin) VALUES (?, ?, 1)",
                    (username, generate_password_hash(password)),
                )
                db_conn.commit()
            except db_conn.IntegrityError:
                error = f"User {username} is already registered."
            
            if error is None:
                click.echo(f"Admin user {username} created successfully.")
            else:
                click.echo(error, err=True)

    return app