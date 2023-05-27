from datetime import datetime
from flask import render_template, url_for, redirect, g, abort, request, flash, send_file, jsonify
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
    filter_type = request.args.get('filter-type')
    if form.validate_on_submit():
        count = r.RethinkDB().table('todos').count().run(g.rdb_conn)
        if count == 0:
            priority = 1
        else:
            priority_number = r.RethinkDB().table('todos').order_by(r.RethinkDB().desc('priority')).limit(1).pluck(
                'priority').run(g.rdb_conn)
            priority = (int(priority_number[0]['priority']) + 1)
        result = r.RethinkDB().table('todos').insert(
            {"name": form.label.data, "status_id": "9f49d122-54b9-4cf4-9ea3-ce5e8c43a656", "priority": priority}).run(
            g.rdb_conn)
        if result['inserted'] == 1:
            flash('Successfully Added!', category='success')
        else:
            flash('Failed to Add!', category='error')
        return redirect(url_for('index'))

    if filter_type == 'status-done':
        selection = list(r.RethinkDB().table('todos').eq_join('status_id', r.RethinkDB().table('todo_status')).without(
            {"right": "id"}).zip().filter(lambda row: row['text_status'].match('done')).run(g.rdb_conn))
    elif filter_type == 'status-active':
        selection = list(r.RethinkDB().table('todos').eq_join('status_id', r.RethinkDB().table('todo_status')).without(
            {"right": "id"}).zip().filter(lambda row: row['text_status'].match('active')).run(g.rdb_conn))
    else:
        selection = list(r.RethinkDB().table('todos').eq_join('status_id', r.RethinkDB().table('todo_status')).without(
            {"right": "id"}).zip().run(g.rdb_conn))
    return render_template('index.html', form=form, tasks=selection, filter=filter_type)


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


@app.route('/json_import', methods=['POST'])
def import_data_json():
    data = request.get_json()
    result = r.RethinkDB().table('todos').insert(
        {data}).run(g.rdb_conn)
    return jsonify({'success': True})


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


@app.route('/<id>', methods=['GET', 'POST'])
def update_task(id):
    form = OneTaskForm()
    if request.method == 'POST':
        text = form.label.data
        print(text)
        result = r.RethinkDB().table('todos').get(id).update({"name": text}).run(g.rdb_conn)
        if result['replaced'] == 1:
            flash('Task Changed Successfully!', category='success')
        else:
            flash('Failed to Change Task !', category='error')
        return redirect(url_for('update_task', id=id))

    else:
        task = list(r.RethinkDB().table('todos').eq_join('status_id', r.RethinkDB().table('todo_status')).without(
            {"right": "id"}).zip().filter({'id': id}).run(g.rdb_conn))
        if len(task) == 0:
            abort(404)
        else:
            form.label.data = task[0]['name']
        return render_template('task.html', form=form, task=task, status=task[0]['text_status'], id_task=task[0]['id'])


@app.route('/<id>/update_status_task', methods=['GET', 'POST'])
def update_status_task(id):
    if request.method == 'POST':
        value = request.form['status']
        result = r.RethinkDB().table('todos').get(id).update({"status_id": value}).run(g.rdb_conn)
        if result['replaced'] == 1:
            flash('Task Status Changed Successfully!', category='success')
        else:
            flash('Failed to Change Status!', category='error')
    return redirect('/{}'.format(id))


@app.route('/move_positions_tasks', methods=['GET', 'POST'])
def move_positions_tasks():
    if request.method == 'POST':
        checked_boxes = request.form.getlist('check_box')
        print(checked_boxes)
        if len(checked_boxes) > 0:
            if len(checked_boxes) == 2:
                cursor1 = r.RethinkDB().table('todos').get(checked_boxes[0]).pluck('priority').run(g.rdb_conn)[
                    'priority']
                cursor2 = r.RethinkDB().table('todos').get(checked_boxes[1]).pluck('priority').run(g.rdb_conn)[
                    'priority']
                print(cursor1)
                print(cursor2)
                result1 = r.RethinkDB().table('todos').get(checked_boxes[0]).update({'priority': cursor2}).run(
                    g.rdb_conn)
                result2 = r.RethinkDB().table('todos').get(checked_boxes[1]).update({'priority': cursor1}).run(
                    g.rdb_conn)
                if result1['replaced'] + result2['replaced'] == 2:
                    flash('Task Priority Changed Successfully!', category='success')
                else:
                    flash('Failed to Change priority!', category='error')
            else:
                flash('Chose two tasks!', category='error')
        return redirect('/move_positions_tasks')
    selection = list(r.RethinkDB().table('todos').eq_join('status_id', r.RethinkDB().table('todo_status')).without(
        {"right": "id"}).zip().run(g.rdb_conn))
    return render_template('move_positions_tasks.html', tasks=selection)
