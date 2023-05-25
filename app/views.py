from flask import render_template, url_for, redirect, g, abort
from app import app
from app.forms import TaskForm
import json

# rethink imports
import rethinkdb as r
from rethinkdb.errors import RqlRuntimeError, RqlDriverError

# rethink config
RDB_HOST = 'localhost'
RDB_PORT = 28015
TODO_DB = 'todo'


# db setup; only run once
def dbSetup():
    connection = r.RethinkDB().connect(host=RDB_HOST, port=RDB_PORT)
    try:
        r.RethinkDB().db_create(TODO_DB).run(connection)
        r.RethinkDB().db(TODO_DB).table_create('todos').run(connection)
        print('Database setup completed')
    except RqlRuntimeError:
        print('Database already exists.')
    finally:
        connection.close()


dbSetup()


# open connection before each request
@app.before_request
def before_request():
    try:
        g.rdb_conn = r.RethinkDB().connect(host=RDB_HOST, port=RDB_PORT, db=TODO_DB)
    except RqlDriverError:
        abort(503, "Database connection could be established.")


# close the connection after each request
@app.teardown_request
def teardown_request(exception):
    try:
        g.rdb_conn.close()
    except AttributeError:
        pass


@app.route('/', methods=['GET', 'POST'])
def index():
    form = TaskForm()
    if form.validate_on_submit():
        count = r.RethinkDB().table('todos').count().run(g.rdb_conn)
        if count == 0:
            priority = 1
        else:
            priority_number = r.RethinkDB().table('todos').order_by(r.RethinkDB().desc('priority')).limit(1).pluck('priority').run(g.rdb_conn)
            priority = (int(priority_number[0]['priority']) + 1)
        r.RethinkDB().table('todos').insert(
            {"name": form.label.data, "status_id": "5acb93df-e780-46fe-9973-e33acb36658f", "priority": priority}).run(g.rdb_conn)
        return redirect(url_for('index'))
    selection = list(r.RethinkDB().table('todos').eq_join('status_id', r.RethinkDB().table('todo_status')).without({"right": "id"}).zip().run(g.rdb_conn))
    return render_template('index.html', form=form, tasks=selection)

