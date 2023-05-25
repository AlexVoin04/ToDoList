from datetime import datetime
from flask import render_template, url_for, redirect, g, abort, request, flash, send_file
from app import app
from app.forms import TaskForm, OneTaskForm
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
            priority_number = r.RethinkDB().table('todos').order_by(r.RethinkDB().desc('priority')).limit(1).pluck(
                'priority').run(g.rdb_conn)
            priority = (int(priority_number[0]['priority']) + 1)
        result = r.RethinkDB().table('todos').insert(
            {"name": form.label.data, "status_id": "5acb93df-e780-46fe-9973-e33acb36658f", "priority": priority}).run(
            g.rdb_conn)
        if result['inserted'] == 1:
            flash('Successfully Added!', category='success')
        else:
            flash('Failed to Add!', category='error')
        return redirect(url_for('index'))
    selection = list(r.RethinkDB().table('todos').eq_join('status_id', r.RethinkDB().table('todo_status')).without(
        {"right": "id"}).zip().run(g.rdb_conn))
    return render_template('index.html', form=form, tasks=selection)


@app.route('/delete', methods=['GET', 'POST'])
def delete():
    if request.method == 'POST':
        checked_boxes = request.form.getlist('check_box')
        if len(checked_boxes) > 0:
            count_delete = 0
            item = 0
            for get_id in checked_boxes:
                item = item + 1
                print(get_id)
                result = r.RethinkDB().table('todos').get(get_id).delete().run(g.rdb_conn)
                if result['deleted'] == 1:
                    count_delete = count_delete + 1

            if item == count_delete:
                flash('Successfully Deleted!', category='success')
            else:
                flash('Failed to delete!', category='error')
    return redirect('/')


@app.route('/json_export', methods=['POST'])
def get_data_json():
    if request.method == 'POST':
        file_name = "/home/alex/Import in json(" + str(datetime.now()) + ").json"
        data = {}
        data['Tasks'] = []
        try:
            cursor = r.RethinkDB().table('todos').run(g.rdb_conn)
            for document in cursor:
                data['Tasks'].append({'id': document['id'], 'name': document['name'], 'priority': document['priority'],
                                      'status_id': document['status_id']})
            with open(file_name, 'w', newline='', encoding='utf-8') as f:
                # f.write(str(data))
                json.dump(data, f, ensure_ascii=False)
        except:
            print('error')
        return send_file(file_name, as_attachment=True)


@app.route('/tsv_export', methods=['POST'])
def get_data_stv():
    if request.method == 'POST':
        file_name = "/home/alex/Import in tsv(" + str(datetime.now()) + ").tsv"
        with open(file_name, 'w') as f:
            cursor = r.RethinkDB().table('todos').run(g.rdb_conn)
            for row in cursor:
                line = '\t'.join(map(str, row.values())) + '\n'
                f.write(line)

        return send_file(file_name, as_attachment=True)


@app.route('/<id>')
def update_task(id):
    form = OneTaskForm()
    task = list(r.RethinkDB().table('todos').eq_join('status_id', r.RethinkDB().table('todo_status')).without(
        {"right": "id"}).zip().filter({'id': id}).run(g.rdb_conn))
    if len(task) == 0:
        abort(404)
    else:
        form.label.data = task[0]['name']
    return render_template('task.html', form=form, tasks=task[0]['name'])
