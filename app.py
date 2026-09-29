import os
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'super_secret_key_change_in_production'

# Database Setup
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'trucks.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'admin', 'driver', 'customer'

class Truck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    national_id = db.Column(db.String(50), nullable=False) # رقم التعريف الوطني
    phone_number = db.Column(db.String(20), nullable=False) # رقم الهاتف
    cargo_description = db.Column(db.String(200), nullable=False) # وصف نوع الحمولة
    driver_name = db.Column(db.String(100), nullable=False)
    capacity = db.Column(db.Float, nullable=False)

with app.app_context():
    db.drop_all() # Re-create table structure to apply new columns without SQL errors
    db.create_all()
    # Check if main admin exists, else create
    admin = User.query.filter_by(username='لعور حوسين').first()
    if not admin:
        hashed_pw = generate_password_hash('123456', method='pbkdf2:sha256')
        admin = User(username='لعور حوسين', password_hash=hashed_pw, role='admin')
        db.session.add(admin)
        db.session.commit()

# HTML Templates
HTML_LOGIN = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تطبيق شاحنات النقل</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f6f9; text-align: center; padding: 20px; direction: rtl; }
        .card { background: white; padding: 30px; border-radius: 10px; max-width: 400px; margin: auto; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        h2 { color: #2c3e50; }
        input, select, button { width: 100%; padding: 12px; margin: 10px 0; border-radius: 5px; border: 1px solid #ccc; box-sizing: border-box; }
        button { background-color: #27ae60; color: white; font-weight: bold; cursor: pointer; border: none; }
        button:hover { background-color: #219150; }
        .link { margin-top: 15px; display: block; color: #2980b9; text-decoration: none; }
    </style>
</head>
<body>
    <div class="card">
        <h2>تسجيل الدخول - تطبيق الشاحنات</h2>
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            {% for message in messages %}
              <p style="color: red;">{{ message }}</p>
            {% endfor %}
          {% endif %}
        {% endwith %}
        <form action="/login" method="POST">
            <input type="text" name="username" placeholder="اسم المستخدم" required>
            <input type="password" name="password" placeholder="كلمة المرور" required>
            <button type="submit">دخول</button>
        </form>
        <a class="link" href="/register">إنشاء حساب جديد</a>
    </div>
</body>
</html>
'''

HTML_REGISTER = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>إنشاء حساب</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f6f9; text-align: center; padding: 20px; direction: rtl; }
        .card { background: white; padding: 30px; border-radius: 10px; max-width: 400px; margin: auto; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        input, select, button { width: 100%; padding: 12px; margin: 10px 0; border-radius: 5px; border: 1px solid #ccc; box-sizing: border-box; }
        button { background-color: #2980b9; color: white; font-weight: bold; cursor: pointer; border: none; }
    </style>
</head>
<body>
    <div class="card">
        <h2>حساب جديد</h2>
        <form action="/register" method="POST">
            <input type="text" name="username" placeholder="اسم المستخدم" required>
            <input type="password" name="password" placeholder="كلمة المرور" required>
            <select name="role">
                <option value="customer">زبون (طلب شاحنة)</option>
                <option value="driver">سائق شاحنة</option>
            </select>
            <button type="submit">تسجيل الحساب</button>
        </form>
        <a href="/">العودة لتسجيل الدخول</a>
    </div>
</body>
</html>
'''

HTML_ADMIN = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>لوحة التحكم - لعور حوسين</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; background-color: #eef2f5; direction: rtl; }
        .header { background-color: #2c3e50; color: white; padding: 15px; border-radius: 8px; }
        .container { background: white; padding: 20px; margin-top: 20px; border-radius: 8px; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { border: 1px solid #ddd; padding: 10px; text-align: center; }
        th { background-color: #34495e; color: white; }
        .btn-delete { background-color: #e74c3c; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; text-decoration: none; font-size: 14px; }
        .btn-delete:hover { background-color: #c0392b; }
    </style>
</head>
<body>
    <div class="header">
        <h1>مرحباً بك: المدير لعور حوسين</h1>
        <a href="/logout" style="color: #e74c3c; font-weight: bold;">تسجيل الخروج</a>
    </div>
    <div class="container">
        <h3>قائمة خدمات السائقين المتاحة في النظام</h3>
        <table>
            <tr>
                <th>اسم السائق</th>
                <th>رقم التعريف الوطني</th>
                <th>رقم الهاتف</th>
                <th>وصف نوع الحمولة</th>
                <th>الحمولة (طناً)</th>
                <th>الإجراء</th>
            </tr>
            {% for truck in trucks %}
            <tr>
                <td>{{ truck.driver_name }}</td>
                <td>{{ truck.national_id }}</td>
                <td>{{ truck.phone_number }}</td>
                <td>{{ truck.cargo_description }}</td>
                <td>{{ truck.capacity }}</td>
                <td>
                    <a href="/delete_truck/{{ truck.id }}" class="btn-delete" onclick="return confirm('هل أنت تأكد من حذف هذا السجل؟');">حذف</a>
                </td>
            </tr>
            {% else %}
            <tr><td colspan="6">لا توجد سجلات مسجلة حالياً</td></tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
'''

HTML_DRIVER = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>واجهة السائق</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; background-color: #eef2f5; direction: rtl; }
        .card { background: white; padding: 20px; border-radius: 8px; max-width: 500px; margin: auto; }
        input, textarea, button { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; }
        button { background-color: #e67e22; color: white; border: none; font-weight: bold; cursor: pointer; }
    </style>
</head>
<body>
    <div class="card">
        <h2>لوحة السائق: {{ session['username'] }}</h2>
        <h3>تسجيل بيانات الخدمة والحمولة</h3>
        <form action="/add_truck" method="POST">
            <input type="text" name="national_id" placeholder="رقم التعريف الوطني" required>
            <input type="tel" name="phone_number" placeholder="رقم الهاتف" required>
            <textarea name="cargo_description" placeholder="وصف نوع الحمولة (مثال: مواد بناء، مواد غذائية...)" rows="3" required></textarea>
            <input type="number" step="0.1" name="capacity" placeholder="الحمولة الكلية (بالطن)" required>
            <button type="submit">إضافة للخدمة</button>
        </form>
        <a href="/logout">تسجيل الخروج</a>
    </div>
</body>
</html>
'''

HTML_CUSTOMER = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>واجهة الزبائن</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; background-color: #eef2f5; direction: rtl; }
        .card { background: white; padding: 20px; border-radius: 8px; max-width: 600px; margin: auto; text-align: center; }
    </style>
</head>
<body>
    <div class="card">
        <h2>أهلاً بك يا {{ session['username'] }} في منصة خدمات النقل</h2>
        <p>يمكنك تقديم طلبات نقل البضائع واختيار الشاحنة المناسبة لنقل حمولتك بسهولة.</p>
        <a href="/logout" style="color: red;">تسجيل الخروج</a>
    </div>
</body>
</html>
'''

# Routes
@app.route('/')
def home():
    if 'username' in session:
        role = session.get('role')
        username = session.get('username')
        if username == 'لعور حوسين' or role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif role == 'driver':
            return redirect(url_for('driver_dashboard'))
        else:
            return redirect(url_for('customer_dashboard'))
    return render_template_string(HTML_LOGIN)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role

            if user.username == 'لعور حوسين' or user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'driver':
                return redirect(url_for('driver_dashboard'))
            else:
                return redirect(url_for('customer_dashboard'))

        flash('اسم المستخدم أو كلمة المرور غير صحيحة')
        return redirect(url_for('home'))
    return render_template_string(HTML_LOGIN)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form.get('role', 'customer')

        if User.query.filter_by(username=username).first():
            flash('اسم المستخدم مستعمل بالفعل!')
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password_hash=hashed_pw, role=role)
        db.session.add(new_user)
        db.session.commit()
        flash('تم إنشاء الحساب بنجاح، يمكنك التسجيل الآن')
        return redirect(url_for('home'))
    return render_template_string(HTML_REGISTER)

@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'admin' and session.get('username') != 'لعور حوسين':
        return redirect(url_for('home'))
    trucks = Truck.query.all()
    return render_template_string(HTML_ADMIN, trucks=trucks)

@app.route('/driver')
def driver_dashboard():
    if session.get('role') != 'driver':
        return redirect(url_for('home'))
    return render_template_string(HTML_DRIVER)

@app.route('/customer')
def customer_dashboard():
    if session.get('role') != 'customer':
        return redirect(url_for('home'))
    return render_template_string(HTML_CUSTOMER)

@app.route('/add_truck', methods=['POST'])
def add_truck():
    if session.get('role') == 'driver':
        national_id = request.form['national_id']
        phone_number = request.form['phone_number']
        cargo_description = request.form['cargo_description']
        capacity = request.form['capacity']

        new_truck = Truck(
            national_id=national_id,
            phone_number=phone_number,
            cargo_description=cargo_description,
            driver_name=session['username'],
            capacity=float(capacity)
        )
        db.session.add(new_truck)
        db.session.commit()
    return redirect(url_for('driver_dashboard'))

@app.route('/delete_truck/<int:truck_id>')
def delete_truck(truck_id):
    if session.get('role') == 'admin' or session.get('username') == 'لعور حوسين':
        truck = Truck.query.get(truck_id)
        if truck:
            db.session.delete(truck)
            db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
