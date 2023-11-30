import mysql.connector
import click
from flask import current_app, g


def get_db():
    if "db" not in g:
        g.db = mysql.connector.connect(**current_app.config["DATABASE"])
        g.db.autocommit = True
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    with current_app.open_resource("schema.sql") as f:
        sql_script = f.read().decode("utf8")
        sql_commands = sql_script.split(";")
        for command in sql_commands:
            if command.strip():
                db.cursor().execute(command)
    db.commit()


@click.command("init-db")
def init_db_command():
    init_db()
    click.echo("Initialized the database.")


def init_app(app):
    app.teadown_appcontext(close_db)
    app.cli.add_command(init_db_command)