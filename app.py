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
    national_id = db.Column(db.String(50), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    cargo_description = db.Column(db.String(200), nullable=False)
    driver_name = db.Column(db.String(100), nullable=False)
    capacity = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False, default=0.0) # السعر بالدينار
    is_approved = db.Column(db.Boolean, default=False) # حالة موافقة المسؤول

with app.app_context():
    db.create_all()
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
    <title>تسجيل الدخول</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f6f9; text-align: center; padding: 20px; direction: rtl; }
        .card { background: white; padding: 30px; border-radius: 12px; max-width: 400px; margin: auto; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        h2 { color: #2c3e50; margin-bottom: 20px; }
        .form-group { text-align: right; margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; color: #333; }
        input, select, button { width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #ccc; box-sizing: border-box; font-size: 15px; }
        button { background-color: #27ae60; color: white; font-weight: bold; cursor: pointer; border: none; margin-top: 10px; }
        .link { margin-top: 15px; display: block; color: #2980b9; text-decoration: none; }
        .alert { color: green; font-weight: bold; margin-bottom: 15px; }
        .error { color: red; font-weight: bold; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>تسجيل الدخول - تطبيق الشاحنات</h2>
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, message in messages %}
              <p class="{{ category }}">{{ message }}</p>
            {% endfor %}
          {% endif %}
        {% endwith %}
        <form action="/login" method="POST">
            <div class="form-group">
                <label>اسم المستخدم:</label>
                <input type="text" name="username" placeholder="أدخل اسم المستخدم" required>
            </div>
            <div class="form-group">
                <label>كلمة المرور:</label>
                <input type="password" name="password" placeholder="أدخل كلمة المرور" required>
            </div>
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
        .card { background: white; padding: 30px; border-radius: 12px; max-width: 400px; margin: auto; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        h2 { color: #2c3e50; margin-bottom: 20px; }
        .form-group { text-align: right; margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; color: #333; }
        input, select, button { width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #ccc; box-sizing: border-box; font-size: 15px; }
        button { background-color: #2980b9; color: white; font-weight: bold; cursor: pointer; border: none; margin-top: 10px; }
        .error { color: red; font-weight: bold; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>حساب جديد</h2>
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, message in messages %}
              <p class="{{ category }}">{{ message }}</p>
            {% endfor %}
          {% endif %}
        {% endwith %}
        <form action="/register" method="POST">
            <div class="form-group">
                <label>اسم المستخدم:</label>
                <input type="text" name="username" placeholder="اختر اسم المستخدم" required>
            </div>
            <div class="form-group">
                <label>كلمة المرور:</label>
                <input type="password" name="password" placeholder="اختر كلمة المرور" required>
            </div>
            <div class="form-group">
                <label>نوع الحساب:</label>
                <select name="role">
                    <option value="customer">زبون (طلب شاحنة)</option>
                    <option value="driver">سائق شاحنة</option>
                </select>
            </div>
            <button type="submit">تسجيل الحساب والدخول مباشرة</button>
        </form>
        <a href="/" style="display: block; margin-top: 15px; color: #777;">العودة لتسجيل الدخول</a>
    </div>
</body>
</html>
'''

HTML_ADMIN = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة التحكم - لعور حوسين</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; background-color: #eef2f5; direction: rtl; }
        .header { background-color: #2c3e50; color: white; padding: 15px; border-radius: 8px; text-align: center; }
        .container { background: white; padding: 20px; margin-top: 20px; border-radius: 8px; overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { border: 1px solid #ddd; padding: 10px; text-align: center; }
        th { background-color: #34495e; color: white; }
        .btn-approve { background-color: #27ae60; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; text-decoration: none; font-size: 14px; margin-left: 5px; }
        .btn-delete { background-color: #e74c3c; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; text-decoration: none; font-size: 14px; }
        .badge-pending { background-color: #f39c12; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; }
        .badge-approved { background-color: #27ae60; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>مرحباً بك: المدير لعور حوسين</h1>
        <a href="/logout" style="color: #e74c3c; font-weight: bold; text-decoration: none;">تسجيل الخروج</a>
    </div>
    <div class="container">
        <h3>إدارة طلبات الشاحنات والسائقين</h3>
        <table>
            <tr>
                <th>اسم السائق</th>
                <th>رقم الهوية / الهاتف</th>
                <th>وصف نوع الحمولة</th>
                <th>الحمولة (طناً)</th>
                <th>السعر المحدّد</th>
                <th>الحالة</th>
                <th>الإجراء</th>
            </tr>
            {% for truck in trucks %}
            <tr>
                <td>{{ truck.driver_name }}</td>
                <td>{{ truck.national_id }} <br> <small>{{ truck.phone_number }}</small></td>
                <td>{{ truck.cargo_description }}</td>
                <td>{{ truck.capacity }} طن</td>
                <td><strong>{{ truck.price }} دج</strong></td>
                <td>
                    {% if truck.is_approved %}
                        <span class="badge-approved">مقبول ومفعل</span>
                    {% else %}
                        <span class="badge-pending">بانتظار الموافقة</span>
                    {% endif %}
                </td>
                <td>
                    {% if not truck.is_approved %}
                        <a href="/approve_truck/{{ truck.id }}" class="btn-approve">موافقة</a>
                    {% endif %}
                    <a href="/delete_truck/{{ truck.id }}" class="btn-delete" onclick="return confirm('هل أنت تأكد من الحذف؟');">حذف</a>
                </td>
            </tr>
            {% else %}
            <tr><td colspan="7">لا توجد طلبات مسجلة حالياً</td></tr>
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
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>واجهة السائق</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; background-color: #eef2f5; direction: rtl; }
        .card { background: white; padding: 25px; border-radius: 12px; max-width: 500px; margin: auto; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        h2 { color: #d35400; text-align: center; margin-bottom: 5px; }
        h3 { text-align: center; color: #555; margin-bottom: 20px; font-size: 16px; }
        .form-group { text-align: right; margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; color: #333; }
        input, textarea, button { width: 100%; padding: 12px; border: 1px solid #ccc; border-radius: 8px; box-sizing: border-box; font-size: 14px; }
        button { background-color: #e67e22; color: white; border: none; font-weight: bold; cursor: pointer; margin-top: 10px; font-size: 16px; }
        button:hover { background-color: #d35400; }
        .alert-success { background-color: #d4edda; color: #155724; padding: 12px; border-radius: 8px; border: 1px solid #c3e6cb; margin-bottom: 15px; text-align: center; font-weight: bold; }
        .logout-link { display: block; text-align: center; margin-top: 20px; color: #c0392b; text-decoration: none; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <h2>لوحة السائق: {{ session['username'] }}</h2>
        <h3>تسجيل بيانات الخدمة والتسعيرة</h3>

        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, message in messages %}
              <div class="alert-success">{{ message }}</div>
            {% endfor %}
          {% endif %}
        {% endwith %}

        <form action="/add_truck" method="POST">
            <div class="form-group">
                <label>رقم التعريف الوطني:</label>
                <input type="text" name="national_id" placeholder="أدخل رقم التعريف الوطني" required>
            </div>
            
            <div class="form-group">
                <label>رقم الهاتف:</label>
                <input type="tel" name="phone_number" placeholder="أدخل رقم الهاتف للتواصل" required>
            </div>

            <div class="form-group">
                <label>نوع الشاحنة / الحمولة:</label>
                <textarea name="cargo_description" placeholder="مثال: شاحنة مغلقة، نقل أثاث، مواد بناء..." rows="2" required></textarea>
            </div>

            <div class="form-group">
                <label>أقصى حمولة (بالطن):</label>
                <input type="number" step="0.1" name="capacity" placeholder="مثال: 10" required>
            </div>

            <div class="form-group">
                <label>السعر المطلوب (بالدينار الجزائري دج):</label>
                <input type="number" name="price" placeholder="مثال: 15000" required>
            </div>

            <button type="submit">إرسال الطلب للمسؤول</button>
        </form>
        <a class="logout-link" href="/logout">تسجيل الخروج</a>
    </div>
</body>
</html>
'''

HTML_CUSTOMER = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>خيارات الشاحنات المتاحة</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 15px; background-color: #f4f6f9; direction: rtl; margin: 0; }
        .header { background-color: #2c3e50; color: white; padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 20px; }
        .container { max-width: 500px; margin: auto; }
        
        /* تصميم قائمة خيارات الشاحنات المماثل للتطبيقات الحديثة */
        .option-card {
            background: white;
            border: 2px solid #6c5ce7;
            border-radius: 16px;
            padding: 15px 20px;
            margin-bottom: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 12px rgba(108, 92, 231, 0.08);
        }
        .option-info { text-align: right; }
        .option-title { font-size: 18px; font-weight: bold; color: #2d3436; margin-bottom: 4px; }
        .option-sub { font-size: 13px; color: #636e72; margin-bottom: 6px; }
        .option-price { font-size: 20px; font-weight: bold; color: #2d3436; }
        .price-currency { font-size: 14px; font-weight: normal; color: #636e72; }
        
        .btn-order {
            background-color: #6c5ce7;
            color: white;
            padding: 12px 20px;
            border-radius: 10px;
            text-decoration: none;
            font-weight: bold;
            font-size: 15px;
            display: inline-block;
            border: none;
            cursor: pointer;
        }
        .btn-order:hover { background-color: #5b4bc4; }
        .empty-msg { text-align: center; color: #7f8c8d; background: white; padding: 20px; border-radius: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h3 style="margin: 0;">أهلاً بك {{ session['username'] }}</h3>
            <p style="margin: 5px 0 0 0; font-size: 13px; opacity: 0.8;">اختر الشاحنة المناسبة لنقل حمولتك</p>
            <a href="/logout" style="color: #ff7675; font-size: 12px; text-decoration: none; display: inline-block; margin-top: 8px;">تسجيل الخروج</a>
        </div>

        <p style="text-align: center; color: #636e72; font-size: 14px; font-weight: bold;">جميع خيارات الشاحنات المتاحة والمعتمدة:</p>

        {% for truck in trucks %}
        <div class="option-card">
            <div class="option-info">
                <div class="option-title">{{ truck.cargo_description }}</div>
                <div class="option-sub">السائق: {{ truck.driver_name }} • الحمولة: {{ truck.capacity }} طن</div>
                <div class="option-price">{{ truck.price }} <span class="price-currency">دج</span></div>
            </div>
            <div>
                <a href="tel:{{ truck.phone_number }}" class="btn-order">طلب وحجز</a>
            </div>
        </div>
        {% else %}
        <div class="empty-msg">
            لا توجد شاحنات معتمدة حالياً، يرجى المحاولة لاحقاً.
        </div>
        {% endfor %}
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

        flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
        return redirect(url_for('home'))
    return render_template_string(HTML_LOGIN)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form.get('role', 'customer')

        if User.query.filter_by(username=username).first():
            flash('اسم المستخدم مستعمل بالفعل!', 'error')
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password_hash=hashed_pw, role=role)
        db.session.add(new_user)
        db.session.commit()

        session['user_id'] = new_user.id
        session['username'] = new_user.username
        session['role'] = new_user.role

        if new_user.role == 'driver':
            return redirect(url_for('driver_dashboard'))
        else:
            return redirect(url_for('customer_dashboard'))

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
    # عرض الشاحنات المقبولة فقط للزبائن
    trucks = Truck.query.filter_by(is_approved=True).all()
    return render_template_string(HTML_CUSTOMER, trucks=trucks)

@app.route('/add_truck', methods=['POST'])
def add_truck():
    if session.get('role') == 'driver':
        national_id = request.form['national_id']
        phone_number = request.form['phone_number']
        cargo_description = request.form['cargo_description']
        capacity = request.form['capacity']
        price = request.form['price']

        new_truck = Truck(
            national_id=national_id,
            phone_number=phone_number,
            cargo_description=cargo_description,
            driver_name=session['username'],
            capacity=float(capacity),
            price=float(price),
            is_approved=False # يتطلب موافقة المدير أولاً
        )
        db.session.add(new_truck)
        db.session.commit()

        flash('تم إرسال الطلب بنجاح وبانتظار موافقة المسؤول.', 'success')

    return redirect(url_for('driver_dashboard'))

@app.route('/approve_truck/<int:truck_id>')
def approve_truck(truck_id):
    if session.get('role') == 'admin' or session.get('username') == 'لعور حوسين':
        truck = Truck.query.get(truck_id)
        if truck:
            truck.is_approved = True
            db.session.commit()
    return redirect(url_for('admin_dashboard'))

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
