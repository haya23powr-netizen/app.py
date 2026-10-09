import os
import uuid
from flask import Flask, render_template_string, request, redirect, url_for, session, flash, send_from_directory, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'super_secret_key_change_in_production')

# Database & Upload Setup
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'trucks.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
    id_card_image = db.Column(db.String(200), nullable=True)
    phone_number = db.Column(db.String(20), nullable=False)
    whatsapp_number = db.Column(db.String(20), nullable=True)
    from_wilaya = db.Column(db.String(50), nullable=False, default="غير محدد")
    to_wilaya = db.Column(db.String(50), nullable=False, default="غير محدد")
    cargo_description = db.Column(db.String(200), nullable=False)
    driver_name = db.Column(db.String(100), nullable=False)
    capacity = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False, default=0.0)
    rating = db.Column(db.Float, default=5.0)
    is_approved = db.Column(db.Boolean, default=False)

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
        th, td { border: 1px solid #ddd; padding: 10px; text-align: center; vertical-align: middle; }
        th { background-color: #34495e; color: white; }
        .btn-approve { background-color: #27ae60; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; text-decoration: none; font-size: 14px; margin-left: 5px; }
        .btn-delete { background-color: #e74c3c; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; text-decoration: none; font-size: 14px; }
        .badge-pending { background-color: #f39c12; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; }
        .badge-approved { background-color: #27ae60; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; }
        .id-img { max-width: 80px; max-height: 50px; border-radius: 4px; border: 1px solid #ccc; }
        .id-link { display: inline-block; text-decoration: none; font-size: 12px; color: #2980b9; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h1>مرحباً بك: المدير لعور حوسين</h1>
        <a href="/logout" style="color: #e74c3c; font-weight: bold; text-decoration: none;">تسجيل الخروج</a>
    </div>
    <div class="container">
        <h3>إدارة ومراجعة طلبات الشاحنات</h3>
        <table>
            <tr>
                <th>اسم السائق</th>
                <th>المسار (من - إلى)</th>
                <th>الهاتف / الواتساب</th>
                <th>بطاقة التعريف</th>
                <th>نوع الحمولة</th>
                <th>الحمولة</th>
                <th>السعر</th>
                <th>الحالة</th>
                <th>الإجراء</th>
            </tr>
            {% for truck in trucks %}
            <tr>
                <td>{{ truck.driver_name }} ⭐{{ truck.rating }}</td>
                <td>{{ truck.from_wilaya }} ➔ {{ truck.to_wilaya }}</td>
                <td>{{ truck.phone_number }}<br><small>واتس: {{ truck.whatsapp_number or 'غير متوفر' }}</small></td>
                <td>
                    {% if truck.id_card_image %}
                        <a href="/uploads/{{ truck.id_card_image }}" target="_blank" class="id-link">
                            <img src="/uploads/{{ truck.id_card_image }}" class="id-img" alt="البطاقة"><br>
                            معاينة البطاقة
                        </a>
                    {% else %}
                        <span style="color: #999;">لا توجد صورة</span>
                    {% endif %}
                </td>
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
            <tr><td colspan="9">لا توجد طلبات مسجلة حالياً</td></tr>
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
        input, textarea, select, button { width: 100%; padding: 12px; border: 1px solid #ccc; border-radius: 8px; box-sizing: border-box; font-size: 14px; }
        button { background-color: #e67e22; color: white; border: none; font-weight: bold; cursor: pointer; margin-top: 10px; font-size: 16px; }
        button:hover { background-color: #d35400; }
        .alert-success { background-color: #d4edda; color: #155724; padding: 12px; border-radius: 8px; border: 1px solid #c3e6cb; margin-bottom: 15px; text-align: center; font-weight: bold; }
        .logout-link { display: block; text-align: center; margin-top: 20px; color: #c0392b; text-decoration: none; font-weight: bold; }
        .status-box { background: #fff3cd; color: #856404; padding: 10px; border-radius: 8px; margin-bottom: 15px; font-size: 14px; text-align: center; }
    </style>
</head>
<body>
    <div class="card">
        <h2>لوحة السائق: {{ session['username'] }}</h2>
        <h3>تسجيل بيانات الرحلة وبطاقة التعريف</h3>

        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, message in messages %}
              <div class="alert-success">{{ message }}</div>
            {% endfor %}
          {% endif %}
        {% endwith %}

        {% if my_truck %}
            <div class="status-box">
                حالة طلبك الحالي: <strong>{% if my_truck.is_approved %}مقبول ومفعل ✅{% else %}بانتظار موافقة المدير ⏳{% endif %}</strong>
            </div>
        {% endif %}

        <form action="/add_truck" method="POST" enctype="multipart/form-data">
            <div class="form-group">
                <label>رقم التعريف الوطني:</label>
                <input type="text" name="national_id" placeholder="أدخل رقم التعريف الوطني" required>
            </div>

            <div class="form-group">
                <label>صورة بطاقة التعريف الوطنية:</label>
                <input type="file" name="id_card_image" accept="image/*,.pdf" required>
            </div>
            
            <div class="form-group">
                <label>رقم الهاتف للاتصال:</label>
                <input type="tel" name="phone_number" placeholder="مثال: 0661234567" required>
            </div>

            <div class="form-group">
                <label>رقم الواتساب (اختياري - الصيغة الدولية):</label>
                <input type="tel" name="whatsapp_number" placeholder="مثال: 213661234567">
            </div>

            <div class="form-group">
                <label>الإنطلاق من ولاية:</label>
                <input type="text" name="from_wilaya" placeholder="مثال: سكيكدة، الجزائر، تمنراست..." required>
            </div>

            <div class="form-group">
                <label>الوصول إلى ولاية:</label>
                <input type="text" name="to_wilaya" placeholder="مثال: ورقلة، وهران، جميع الولايات..." required>
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
        .container { max-width: 550px; margin: auto; }
        .search-box { background: white; padding: 15px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
        .search-box input { width: 48%; padding: 10px; border-radius: 6px; border: 1px solid #ccc; box-sizing: border-box; }
        .search-box button { width: 100%; padding: 10px; background: #2980b9; color: white; border: none; border-radius: 6px; font-weight: bold; margin-top: 10px; cursor: pointer; }
        
        .option-card {
            background: white;
            border: 2px solid #6c5ce7;
            border-radius: 16px;
            padding: 15px 20px;
            margin-bottom: 15px;
            box-shadow: 0 4px 12px rgba(108, 92, 231, 0.08);
        }
        .option-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .option-title { font-size: 18px; font-weight: bold; color: #2d3436; }
        .option-route { font-size: 13px; color: #0984e3; font-weight: bold; background: #e3f2fd; padding: 4px 8px; border-radius: 6px; }
        .option-sub { font-size: 13px; color: #636e72; margin-bottom: 10px; }
        .option-price { font-size: 20px; font-weight: bold; color: #2d3436; margin-bottom: 10px; }
        .price-currency { font-size: 14px; font-weight: normal; color: #636e72; }
        
        .actions-btn { display: flex; gap: 8px; margin-top: 10px; }
        .btn-call {
            flex: 1;
            background-color: #2980b9;
            color: white;
            padding: 10px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
            font-size: 14px;
            text-align: center;
        }
        .btn-whatsapp {
            flex: 1;
            background-color: #25D366;
            color: white;
            padding: 10px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
            font-size: 14px;
            text-align: center;
        }
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

        <!-- فلتر البحث حسب الولايات -->
        <form class="search-box" method="GET" action="/customer">
            <div style="display: flex; justify-content: space-between;">
                <input type="text" name="from_search" placeholder="من ولاية..." value="{{ request.args.get('from_search', '') }}">
                <input type="text" name="to_search" placeholder="إلى ولاية..." value="{{ request.args.get('to_search', '') }}">
            </div>
            <button type="submit">بحث عن شاحنة</button>
        </form>

        {% for truck in trucks %}
        <div class="option-card">
            <div class="option-header">
                <div class="option-title">{{ truck.cargo_description }}</div>
                <div class="option-route">{{ truck.from_wilaya }} ➔ {{ truck.to_wilaya }}</div>
            </div>
            <div class="option-sub">
                السائق: <strong>{{ truck.driver_name }}</strong> (⭐ {{ truck.rating }}) • الحمولة: {{ truck.capacity }} طن
            </div>
            <div class="option-price">{{ truck.price }} <span class="price-currency">دج</span></div>

            <!-- خيارات الاتصال أو واتساب -->
            <div class="actions-btn">
                <a href="tel:{{ truck.phone_number }}" class="btn-call">📞 اتصال هاتف</a>
                {% if truck.whatsapp_number %}
                    <a href="https://wa.me/{{ truck.whatsapp_number }}?text=مرحباً،%20أنا%20مهتم%20بحجز%20الشاحنة" target="_blank" class="btn-whatsapp">💬 مراسلة واتساب</a>
                {% endif %}
            </div>
        </div>
        {% else %}
        <div class="empty-msg">
            لا توجد شاحنات معتمدة متطابقة مع البحث حالياً.
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
    # تصحيح الخطأ لجلب أحدث طلب بناءً على id التنازلي
    my_truck = Truck.query.filter_by(driver_name=session['username']).order_by(Truck.id.desc()).first()
    return render_template_string(HTML_DRIVER, my_truck=my_truck)

@app.route('/customer')
def customer_dashboard():
    if session.get('role') != 'customer':
        return redirect(url_for('home'))
    
    from_search = request.args.get('from_search', '')
    to_search = request.args.get('to_search', '')

    query = Truck.query.filter_by(is_approved=True)

    if from_search:
        query = query.filter(Truck.from_wilaya.contains(from_search))
    if to_search:
        # تصحيح الاسم الإملائي للعمود to_wilaya
        query = query.filter(Truck.to_wilaya.contains(to_search))

    trucks = query.all()
    return render_template_string(HTML_CUSTOMER, trucks=trucks)

@app.route('/add_truck', methods=['POST'])
def add_truck():
    if session.get('role') == 'driver':
        national_id = request.form['national_id']
        phone_number = request.form['phone_number']
        whatsapp_number = request.form.get('whatsapp_number', '').replace('+', '').replace(' ', '')
        from_wilaya = request.form['from_wilaya']
        to_wilaya = request.form['to_wilaya']
        cargo_description = request.form['cargo_description']
        capacity = request.form['capacity']
        price = request.form['price']
        
        file = request.files.get('id_card_image')
        filename = None
        if file and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        new_truck = Truck(
            national_id=national_id,
            id_card_image=filename,
            phone_number=phone_number,
            whatsapp_number=whatsapp_number,
            from_wilaya=from_wilaya,
            to_wilaya=to_wilaya,
            cargo_description=cargo_description,
            driver_name=session['username'],
            capacity=float(capacity),
            price=float(price),
            is_approved=False
        )
        db.session.add(new_truck)
        db.session.commit()

        flash('تم إرسال الطلب بنجاح، وهو حالياً بانتظار موافقة المسؤول.', 'success')

    return redirect(url_for('driver_dashboard'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    if session.get('role') == 'admin' or session.get('username') == 'لعور حوسين':
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    return abort(403)

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
            if truck.id_card_image:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], truck.id_card_image)
                if os.path.exists(file_path):
                    os.remove(file_path)
            db.session.delete(truck)
            db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
