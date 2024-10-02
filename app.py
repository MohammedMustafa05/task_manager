import pyrebase
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'lol'

# Firebase configuration for Realtime Database
firebase_config = {
    "apiKey": "AIzaSyC6Qm0MnvdIsyXK5_baVKYOhWKWKztvUF0",
    "authDomain": "task-manager-d44ef.firebaseapp.com",
    "databaseURL": "https://task-manager-d44ef-default-rtdb.firebaseio.com",  # Ensure this URL is correct
    "storageBucket": "task-manager-d44ef.appspot.com"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
db = firebase.database()

@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('index'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            session['user'] = user['localId']
            return redirect(url_for('index'))
        except:
            return 'Login failed'
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            user = auth.create_user_with_email_and_password(email, password)
            session['user'] = user['localId']
            return redirect(url_for('index'))
        except:
            return 'Registration failed'
    return render_template('register.html')

@app.route('/index', methods=['GET', 'POST'])
def index():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        task = request.form['task']
        deadline = request.form['deadline']
        priority = request.form['priority']
        db.child("tasks").push({
            'task': task,
            'deadline': deadline,
            'priority': priority,
            'userId': session['user'],
            'completed': False
        })

    # Get the sort and filter options from the query parameters
    sort_by = request.args.get('sort_by', 'deadline')  # Default sort by deadline
    filter_by = request.args.get('filter_by', 'all')   # Default filter is 'all'

    tasks = db.child("tasks").order_by_child("userId").equal_to(session['user']).get()

    task_list = []
    if tasks.each():
        for task in tasks.each():
            task_dict = {"id": task.key(), **task.val()}

            # Apply filter based on completion status
            if filter_by == 'completed' and not task_dict['completed']:
                continue
            if filter_by == 'not_completed' and task_dict['completed']:
                continue
            if filter_by in ['high', 'medium', 'low'] and task_dict['priority'] != filter_by:
                continue

            task_list.append(task_dict)

    # Sort tasks based on the selected sort option
    if sort_by == 'deadline':
        task_list.sort(key=lambda x: x['deadline'])
    elif sort_by == 'priority':
        priority_order = {'high': 1, 'medium': 2, 'low': 3}
        task_list.sort(key=lambda x: priority_order.get(x['priority'], 4))
    
    return render_template('index.html', tasks=task_list, sort_by=sort_by, filter_by=filter_by)



@app.route('/complete/<task_id>')
def complete_task(task_id):
    db.child("tasks").child(task_id).update({'completed': True})
    return redirect(url_for('index'))

@app.route('/delete/<task_id>')
def delete_task(task_id):
    db.child("tasks").child(task_id).remove()
    return redirect(url_for('index'))

# Start the app
if __name__ == "__main__":
    app.run(debug=True)
