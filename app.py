from flask import Flask, render_template, request, redirect, session, g
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Connect to SQLite
DATABASE = os.path.join(app.root_path, 'instance', 'disaster.db')

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
#home
@app.route('/')
def welcome():
    # If user already logged in, redirect to dashboard
    if 'user_id' in session:
        return redirect('/dashboard')
    return render_template('home.html')

# login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password))
        user = cur.fetchone()

        if user:
            session['user_id'] = user['user_id']
            session['role'] = user['role']
            return redirect('/dashboard')
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# register page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        db = get_db()
        cursor = db.cursor()

        # Check if email already exists
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            return "Email already exists. Please login."

        cursor.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
            (name, email, password, role)
        )
        db.commit()
        return redirect('/login')

    return render_template('register.html')

# dashboard route
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    role = session.get('role')
    if role == 'admin':
        return redirect('/admin_home')  # Redirect admins to their separate function
    elif role == 'volunteer':
        return redirect('/volunteer_home')
    elif role == 'citizen':
        return render_template('citizen_dashboard.html')
    else:
        return "Unknown role"

#admin_home
@app.route('/admin_home')
def admin_home():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')

    return render_template('admin_dashboard.html')



#voluteer_home
@app.route('/volunteer_home')  # or your actual route name
def volunteer_home():
    if 'user_id' not in session or session.get('role') != 'volunteer':
        return redirect('/login')

    user_id = session['user_id']
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT name FROM users WHERE user_id = ?", (user_id,))
    user = cur.fetchone()

    return render_template("volunteer_dashboard.html", name=user["name"] if user else "Volunteer")

#admin_view_volunteers
@app.route('/view_volunteers')
def view_volunteers():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')

    search = request.args.get('search', '').strip()
    sort_by = request.args.get('sort_by', 'user_id')
    order = request.args.get('order', 'asc')

    # Whitelist of sortable columns
    allowed_sort_columns = ['user_id', 'name', 'email']
    if sort_by not in allowed_sort_columns:
        sort_by = 'user_id'

    if order.lower() not in ['asc', 'desc']:
        order = 'asc'

    db = get_db()
    cur = db.cursor()

    if search:
        like_term = f"%{search}%"
        query = f"""SELECT * FROM users 
                    WHERE role = 'volunteer' 
                    AND (name LIKE ? OR email LIKE ? OR CAST(user_id AS TEXT) LIKE ?)
                    ORDER BY {sort_by} {order.upper()}"""
        cur.execute(query, (like_term, like_term, like_term))
    else:
        query = f"""SELECT * FROM users 
                    WHERE role = 'volunteer' 
                    ORDER BY {sort_by} {order.upper()}"""
        cur.execute(query)

    volunteers = cur.fetchall()
    return render_template('view_volunteers.html', 
                           volunteers=volunteers, 
                           search=search, 
                           sort_by=sort_by, 
                           order=order)



#admin_deleteVoleenter
@app.route('/delete_volunteer/<int:user_id>', methods=['POST'])
def delete_volunteer(user_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')

    db = get_db()
    cursor = db.cursor()

    # Delete the user with given user_id only if their role is 'volunteer'
    cursor.execute("DELETE FROM users WHERE user_id = ? AND role = 'volunteer'", (user_id,))
    db.commit()

    return redirect('/view_volunteers')



#citizen_report_disaster
@app.route('/report_disaster', methods=['GET', 'POST'])
def report_disaster():
    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') != 'citizen':
        return "Only citizens can report disasters."

    if request.method == 'POST':
        disaster_type = request.form['type']
        location = request.form['location']
        date_time = request.form['date_time']
        description = request.form['description']
        reported_by = session['user_id']

        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO disasters (type, location, date_time, description, reported_by)
            VALUES (?, ?, ?, ?, ?)""",
            (disaster_type, location, date_time, description, reported_by)
        )
        db.commit()
        return redirect('/dashboard')

    return render_template('report_disaster.html')

#admin_view_disasters
@app.route('/view_disasters')
def view_disasters():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')

    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT d.*, u.name as reporter_name, u.email as reporter_email
        FROM disasters d
        LEFT JOIN users u ON d.reported_by = u.user_id
        ORDER BY d.date_time DESC
    """)
    disasters = cur.fetchall()
    return render_template('view_disasters.html', disasters=disasters)


#admin_to_assighn
@app.route('/disaster/<int:disaster_id>', methods=['GET', 'POST'])
def disaster_detail(disaster_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect('/login')

    db = get_db()
    cur = db.cursor()

    # Fetch disaster info
    cur.execute("SELECT * FROM disasters WHERE disaster_id = ?", (disaster_id,))
    disaster = cur.fetchone()
    if not disaster:
        return "Disaster not found", 404

    # Fetch all volunteers
    cur.execute("SELECT user_id, name, email FROM users WHERE role = 'volunteer'")
    volunteers = cur.fetchall()

    # Fetch assigned volunteers for this disaster
    cur.execute("""
        SELECT u.user_id, u.name, u.email, va.assigned_on
        FROM volunteer_assignments va
        JOIN users u ON va.volunteer_id = u.user_id
        WHERE va.disaster_id = ?
    """, (disaster_id,))
    assigned_volunteers = cur.fetchall()

    if request.method == 'POST':
        volunteer_id = request.form.get('volunteer_id')
        assigned_on = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Prevent duplicate assignments
        cur.execute("""
            SELECT * FROM volunteer_assignments
            WHERE disaster_id = ? AND volunteer_id = ?
        """, (disaster_id, volunteer_id))
        if cur.fetchone():
            return "Volunteer already assigned to this disaster."

        cur.execute("""
            INSERT INTO volunteer_assignments (disaster_id, volunteer_id, assigned_on)
            VALUES (?, ?, ?)
        """, (disaster_id, volunteer_id, assigned_on))
        db.commit()

        return redirect(f'/disaster/{disaster_id}')

    return render_template('disaster_detail.html',
                           disaster=disaster,
                           volunteers=volunteers,
                           assigned_volunteers=assigned_volunteers)

#volunteer_tasks
@app.route('/volunteer_dashboard')
def volunteer_tasks():
    if 'user_id' not in session or session.get('role') != 'volunteer':
        return redirect('/login')

    volunteer_id = session['user_id']
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT d.*
        FROM disasters d
        JOIN volunteer_assignments va ON d.disaster_id = va.disaster_id
        WHERE va.volunteer_id = ?
        ORDER BY d.date_time DESC
    """, (volunteer_id,))

    disasters = cur.fetchall()
    return render_template('volunteer_tasks.html', disasters=disasters)

# run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
