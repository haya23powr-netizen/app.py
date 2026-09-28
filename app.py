import os
import sqlite3
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'super_secret_key_change_in_production'

# مسار قاعدة البيانات الآمن
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'trucks_advanced.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trucks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_number TEXT UNIQUE NOT NULL,
            driver_name TEXT NOT NULL,
            status TEXT DEFAULT 'متاحة',
            capacity INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تطبيق إدارة الشاحنات</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <nav class="navbar navbar-dark bg-dark mb-4">
        <div class="container">
            <a class="navbar-brand fw-bold" href="#">🚚 نظام الشاحنات</a>
            {% if session.user_id %}
                <span class="navbar-text text-white ms-auto me-3">مرحباً، {{ session.username }}</span>
                <a href="/logout" class="btn btn-outline-danger btn-sm">تسجيل الخروج</a>
            {% endif %}
        </div>
    </nav>

    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, message in messages %}
              <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
                {{ message }}
              </div>
            {% endfor %}
          {% endif %}
        {% endwith %}

        {% if page == 'login' %}
        <div class="row justify-content-center">
            <div class="col-md-5">
                <div class="card shadow-sm">
                    <div class="card-header bg-primary text-white text-center"><h4>تسجيل الدخول</h4></div>
                    <div class="card-body">
                        <form method="POST" action="/login">
                            <div class="mb-3">
                                <label class="form-label">اسم المستخدم</label>
                                <input type="text" name="username" class="form-control" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">كلمة المرور</label>
                                <input type="password" name="password" class="form-control" required>
                            </div>
                            <button type="submit" class="btn btn-primary w-100">دخول</button>
                        </form>
                        <p class="mt-3 text-center">ليس لديك حساب؟ <a href="/register">سجل الآن</a></p>
                    </div>
                </div>
            </div>
        </div>

        {% elif page == 'register' %}
        <div class="row justify-content-center">
            <div class="col-md-5">
                <div class="card shadow-sm">
                    <div class="card-header bg-success text-white text-center"><h4>إنشاء حساب جديد</h4></div>
                    <div class="card-body">
                        <form method="POST" action="/register">
                            <div class="mb-3">
                                <label class="form-label">اسم المستخدم</label>
                                <input type="text" name="username" class="form-control" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">كلمة المرور</label>
                                <input type="password" name="password" class="form-control" required>
                            </div>
                            <button type="submit" class="btn btn-success w-100">تسجيل</button>
                        </form>
                        <p class="mt-3 text-center">لديك حساب بالفعل؟ <a href="/">تسجيل الدخول</a></p>
                    </div>
                </div>
            </div>
        </div>

        {% elif page == 'dashboard' %}
        <div class="row mb-4">
            <div class="col-md-4 mb-3">
                <div class="card shadow-sm">
                    <div class="card-header bg-dark text-white"><h5>إضافة شاحنة جديدة</h5></div>
                    <div class="card-body">
                        <form method="POST" action="/add_truck">
                            <div class="mb-2">
                                <label>رقم لوحة الشاحنة</label>
                                <input type="text" name="plate_number" class="form-control" required>
                            </div>
                            <div class="mb-2">
                                <label>اسم السائق</label>
                                <input type="text" name="driver_name" class="form-control" required>
                            </div>
                            <div class="mb-3">
                                <label>الحمولة (طن)</label>
                                <input type="number" name="capacity" class="form-control" required>
                            </div>
                            <button type="submit" class="btn btn-primary w-100">إضافة الشاحنة</button>
                        </form>
                    </div>
                </div>
            </div>

            <div class="col-md-8">
                <div class="card shadow-sm">
                    <div class="card-header bg-dark text-white"><h5>قائمة الشاحنات المسجلة</h5></div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-hover align-middle">
                                <thead>
                                    <tr>
                                        <th>اللوحة</th>
                                        <th>السائق</th>
                                        <th>الحمولة</th>
                                        <th>الحالة</th>
                                        <th>إجراءات</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for truck in trucks %}
                                    <tr>
                                        <td><strong>{{ truck['plate_number'] }}</strong></td>
                                        <td>{{ truck['driver_name'] }}</td>
                                        <td>{{ truck['capacity'] }} طن</td>
                                        <td>
                                            <span class="badge {% if truck['status'] == 'متاحة' %}bg-success{% elif truck['status'] == 'في الطريق' %}bg-warning text-dark{% else %}bg-danger{% endif %}">
                                                {{ truck['status'] }}
                                            </span>
                                        </td>
                                        <td>
                                            <form method="POST" action="/update_status/{{ truck['id'] }}" class="d-inline">
                                                <select name="status" onchange="this.form.submit()" class="form-select form-select-sm d-inline-block w-auto">
                                                    <option value="متاحة" {% if truck['status'] == 'متاحة' %}selected{% endif %}>متاحة</option>
                                                    <option value="في الطريق" {% if truck['status'] == 'في الطريق' %}selected{% endif %}>في الطريق</option>
                                                    <option value="صيانة" {% if truck['status'] == 'صيانة' %}selected{% endif %}>صيانة</option>
                                                </select>
                                            </form>
                                            <a href="/delete_truck/{{ truck['id'] }}" class="btn btn-sm btn-outline-danger me-1">حذف</a>
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        {% endif %}
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template_string(HTML_TEMPLATE, page='login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            flash('تم إنشاء الحساب بنجاح! يمكنك تسجيل الدخول الآن.', 'success')
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            flash('اسم المستخدم موجود بالفعل، اختر اسماً آخر.', 'danger')
        finally:
            conn.close()
    return render_template_string(HTML_TEMPLATE, page='register')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user and check_password_hash(user['password'], password):
        session['user_id'] = user['id']
        session['username'] = user['username']
        return redirect(url_for('dashboard'))
    else:
        flash('بيانات الدخول غير صحيحة!', 'danger')
        return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM trucks')
    trucks = cursor.fetchall()
    conn.close()
    return render_template_string(HTML_TEMPLATE, page='dashboard', trucks=trucks)

@app.route('/add_truck', methods=['POST'])
def add_truck():
    if 'user_id' in session:
        plate = request.form['plate_number']
        driver = request.form['driver_name']
        capacity = request.form['capacity']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO trucks (plate_number, driver_name, capacity) VALUES (?, ?, ?)', (plate, driver, capacity))
            conn.commit()
            flash('تمت إضافة الشاحنة بنجاح', 'success')
        except sqlite3.IntegrityError:
            flash('رقم اللوحة مسجل مسبقاً!', 'warning')
        finally:
            conn.close()
    return redirect(url_for('dashboard'))

@app.route('/update_status/<int:truck_id>', methods=['POST'])
def update_status(truck_id):
    if 'user_id' in session:
        new_status = request.form['status']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE trucks SET status = ? WHERE id = ?', (new_status, truck_id))
        conn.commit()
        conn.close()
    return redirect(url_for('dashboard'))

@app.route('/delete_truck/<int:truck_id>')
def delete_truck(truck_id):
    if 'user_id' in session:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM trucks WHERE id = ?', (truck_id,))
        conn.commit()
        conn.close()
        flash('تم حذف الشاحنة', 'info')
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

