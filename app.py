from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "haya_secret_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# جدول المستخدمين (أدمن / سائق / زبون)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False) # 'admin', 'driver', 'customer'

# جدول الشاحنات
class Truck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plate_number = db.Column(db.String(50), nullable=False)
    driver_name = db.Column(db.String(100), nullable=False)
    capacity = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='متاحة')

# جدول طلبات النقل (للزبائن)
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    cargo_type = db.Column(db.String(100), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    pickup_location = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default='قيد الانتظار')

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    role = session.get('role')
    username = session.get('username')
    
    if username == "لعور حوسين" or role == 'admin':
        return redirect(url_for('admin'))
    elif role == 'driver':
        return redirect(url_for('driver_dashboard'))
    else:
        # واجهة الزبون
        trucks = Truck.query.filter_by(status='متاحة').all()
        my_bookings = Booking.query.filter_by(customer_name=username).all()
        return render_template('index.html', trucks=trucks, bookings=my_bookings)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username, password=password).first()
        
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            
            if user.username == "لعور حوسين" or user.role == 'admin':
                return redirect(url_for('admin'))
            elif user.role == 'driver':
                return redirect(url_for('driver_dashboard'))
            else:
                return redirect(url_for('home'))
        else:
            flash("بيانات الدخول غير صحيحة!")
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'customer')
        
        # لعور حوسين هو المسؤول دائماً
        if username == "لعور حوسين":
            role = 'admin'
            
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("اسم المستخدم مسجل مسبقاً!")
            return redirect(url_for('register'))
            
        new_user = User(username=username, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()
        
        flash("تم إنشاء الحساب بنجاح!")
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/admin')
def admin():
    if session.get('username') != "لعور حوسين" and session.get('role') != 'admin':
        flash("غير مسموح لك بالدخول هنا!")
        return redirect(url_for('login'))
        
    trucks = Truck.query.all()
    bookings = Booking.query.all()
    return render_template('admin.html', trucks=trucks, bookings=bookings)

@app.route('/driver')
def driver_dashboard():
    if session.get('role') != 'driver':
        return redirect(url_for('login'))
    
    driver_name = session.get('username')
    my_trucks = Truck.query.filter_by(driver_name=driver_name).all()
    return render_template('driver.html', trucks=my_trucks)

@app.route('/book_truck', methods=['POST'])
def book_truck():
    if session.get('role') == 'customer':
        cargo = request.form.get('cargo_type')
        weight = request.form.get('weight')
        pickup = request.form.get('pickup_location')
        dest = request.form.get('destination')
        
        new_booking = Booking(
            customer_name=session['username'],
            cargo_type=cargo,
            weight=weight,
            pickup_location=pickup,
            destination=dest
        )
        db.session.add(new_booking)
        db.session.commit()
        flash("تم تقديم طلب النقل بنجاح!")
        
    return redirect(url_for('home'))

@app.route('/add_truck', methods=['POST'])
def add_truck():
    if session.get('username') == "لعور حوسين" or session.get('role') == 'admin':
        plate = request.form.get('plate_number')
        driver = request.form.get('driver_name')
        capacity = request.form.get('capacity')
        
        new_truck = Truck(plate_number=plate, driver_name=driver, capacity=capacity)
        db.session.add(new_truck)
        db.session.commit()
        
    return redirect(url_for('admin'))

@app.route('/delete_truck/<int:id>')
def delete_truck(id):
    if session.get('username') == "لعور حوسين" or session.get('role') == 'admin':
        truck = Truck.query.get(id)
        if truck:
            db.session.delete(truck)
            db.session.commit()
            
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

