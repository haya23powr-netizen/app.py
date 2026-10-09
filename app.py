import os
import uuid
from flask import Flask, render_template_string, request, redirect, url_for, session, flash, send_from_directory, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'super_secret_key_change_in_production')

# Database Setup
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

# Database Models
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
    from_wilaya = db.Column(db.String(50), nullable=False) # الولاية
    from_daira = db.Column(db.String(50), nullable=False, default="غير محدد") # المقاطعة / الدائرة
    lat = db.Column(db.Float, nullable=True) # إحداثيات العرض للخريطة
    lng = db.Column(db.Float, nullable=True) # إحداثيات الطول للخريطة
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

# HTML Layout Base Template
BASE_HEAD = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>منصة لوجستيك الجزائر للنقل</title>
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Leaflet CSS & JS (الخرائط) -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <!-- FontAwesome Icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');
        body { font-family: 'Tajawal', sans-serif; }
    </style>
</head>
<body class="bg-slate-50 text-slate-800 antialiased min-h-screen flex flex-col">
'''

HTML_LOGIN = BASE_HEAD + '''
<div class="flex-grow flex items-center justify-center p-4">
    <div class="bg-white p-8 rounded-2xl shadow-xl w-full max-w-md border border-slate-100">
        <div class="text-center mb-8">
            <div class="bg-blue-600 text-white w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4 text-2xl shadow-lg shadow-blue-500/30">
                <i class="fa-solid fa-truck-fast"></i>
            </div>
            <h2 class="text-2xl font-bold text-slate-900">تسجيل الدخول</h2>
            <p class="text-slate-500 text-sm mt-1">مرحباً بك في منصة شواحن الجزائر</p>
        </div>

        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, message in messages %}
              <div class="p-3 mb-4 text-sm rounded-xl bg-red-50 text-red-600 font-medium border border-red-100 text-center">
                  {{ message }}
              </div>
            {% endfor %}
          {% endif %}
        {% endwith %}

        <form action="/login" method="POST" class="space-y-4">
            <div>
                <label class="block text-sm font-semibold text-slate-700 mb-1">اسم المستخدم</label>
                <input type="text" name="username" class="w-full px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition" placeholder="أدخل اسم المستخدم" required>
            </div>
            <div>
                <label class="block text-sm font-semibold text-slate-700 mb-1">كلمة المرور</label>
                <input type="password" name="password" class="w-full px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition" placeholder="••••••••" required>
            </div>
            <button type="submit" class="w-full py-3.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl shadow-lg shadow-blue-500/30 transition duration-200">
                دخول للحساب
            </button>
        </form>
        <div class="mt-6 text-center text-sm text-slate-600">
            ليس لديك حساب؟ <a href="/register" class="text-blue-600 font-bold hover:underline">إنشاء حساب جديد</a>
        </div>
    </div>
</div>
</body>
</html>
'''

HTML_REGISTER = BASE_HEAD + '''
<div class="flex-grow flex items-center justify-center p-4">
    <div class="bg-white p-8 rounded-2xl shadow-xl w-full max-w-md border border-slate-100">
        <div class="text-center mb-8">
            <h2 class="text-2xl font-bold text-slate-900">حساب جديد</h2>
            <p class="text-slate-500 text-sm mt-1">اختر نوع حسابك للبدء في استخدام المنصة</p>
        </div>

        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, message in messages %}
              <div class="p-3 mb-4 text-sm rounded-xl bg-red-50 text-red-600 font-medium text-center">
                  {{ message }}
              </div>
            {% endfor %}
          {% endif %}
        {% endwith %}

        <form action="/register" method="POST" class="space-y-4">
            <div>
                <label class="block text-sm font-semibold text-slate-700 mb-1">اسم المستخدم</label>
                <input type="text" name="username" class="w-full px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-blue-500 outline-none transition" placeholder="اسم المستخدم" required>
            </div>
            <div>
                <label class="block text-sm font-semibold text-slate-700 mb-1">كلمة المرور</label>
                <input type="password" name="password" class="w-full px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-blue-500 outline-none transition" placeholder="••••••••" required>
            </div>
            <div>
                <label class="block text-sm font-semibold text-slate-700 mb-1">نوع الحساب</label>
                <select name="role" class="w-full px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-blue-500 outline-none bg-white transition">
                    <option value="customer">زبون (طالب خدمة نقل)</option>
                    <option value="driver">سائق شاحنة</option>
                </select>
            </div>
            <button type="submit" class="w-full py-3.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl shadow-lg shadow-emerald-500/30 transition duration-200">
                تسجيل الحساب
            </button>
        </form>
        <div class="mt-6 text-center text-sm text-slate-600">
            لديك حساب بالفعل؟ <a href="/" class="text-blue-600 font-bold hover:underline">تسجيل الدخول</a>
        </div>
    </div>
</div>
</body>
</html>
'''

HTML_DRIVER = BASE_HEAD + '''
<!-- Navbar -->
<nav class="bg-white border-b border-slate-200 px-6 py-4 flex justify-between items-center shadow-sm">
    <div class="flex items-center gap-3">
        <div class="bg-amber-500 text-white p-2 rounded-xl">
            <i class="fa-solid fa-truck text-xl"></i>
        </div>
        <span class="font-bold text-lg text-slate-800">واجهة السائق Professional</span>
    </div>
    <div class="flex items-center gap-4">
        <span class="text-sm font-medium text-slate-600"><i class="fa-regular fa-user ml-1"></i> {{ session['username'] }}</span>
        <a href="/logout" class="text-sm text-red-500 hover:text-red-700 font-semibold bg-red-50 px-3 py-1.5 rounded-lg border border-red-100">
            خروج <i class="fa-solid fa-right-from-bracket mr-1"></i>
        </a>
    </div>
</nav>

<div class="max-w-4xl mx-auto my-8 px-4 w-full">
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        {% for category, message in messages %}
          <div class="p-4 mb-6 rounded-2xl bg-emerald-50 text-emerald-700 border border-emerald-200 font-medium flex items-center gap-2">
              <i class="fa-solid fa-circle-check"></i> {{ message }}
          </div>
        {% endfor %}
      {% endif %}
    {% endwith %}

    {% if my_truck %}
        <div class="mb-6 p-4 rounded-2xl border {% if my_truck.is_approved %}bg-emerald-50 border-emerald-200 text-emerald-800{% else %}bg-amber-50 border-amber-200 text-amber-800{% endif %} flex items-center justify-between">
            <div class="flex items-center gap-3">
                <i class="fa-solid {% if my_truck.is_approved %}fa-circle-check text-2xl text-emerald-600{% else %}fa-clock text-2xl text-amber-600{% endif %}"></i>
                <div>
                    <div class="font-bold">حالة الطلب الحالي</div>
                    <div class="text-sm">{% if my_truck.is_approved %}حسابك شغال ومُعتمد وموقعك ظافر للزبائن على الخريطة ✅{% else %}طلبك قيد المراجعة والتدقيق من قِبل إدارة المنصة ⏳{% endif %}</div>
                </div>
            </div>
        </div>
    {% endif %}

    <div class="bg-white rounded-2xl shadow-xl border border-slate-100 overflow-hidden">
        <div class="bg-slate-900 text-white p-6">
            <h3 class="text-xl font-bold flex items-center gap-2"><i class="fa-solid fa-map-location-dot text-amber-400"></i> تسجِيل بيانات الشاحنة وتحديد موقعك</h3>
            <p class="text-slate-400 text-sm mt-1">حدد موقعك الدقيق على الخريطة ليصل إليك الزبائن القريبون في مقاطعتك</p>
        </div>

        <form action="/add_truck" method="POST" enctype="multipart/form-data" class="p-6 space-y-6">
            <!-- اختيار الموقع على الخريطة -->
            <div>
                <label class="block text-sm font-bold text-slate-700 mb-2">تحديد موقع شاحنتك على الخريطة (اضغط لتحديد مكانك الحالي):</label>
                <div id="map" class="h-64 rounded-xl border-2 border-slate-200 shadow-inner"></div>
                <input type="hidden" name="lat" id="lat" required>
                <input type="hidden" name="lng" id="lng" required>
                <p class="text-xs text-slate-500 mt-1"><i class="fa-solid fa-info-circle"></i> يمكنك النقر مباشرة على الخريطة أو السماح بالتحديد التلقائي.</p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <label class="block text-sm font-semibold text-slate-700 mb-1">الولاية</label>
                    <input type="text" name="from_wilaya" placeholder="مثال: سكيكدة، الجزائر، تمنراست..." class="w-full p-3 rounded-xl border border-slate-200 outline-none focus:ring-2 focus:ring-blue-500" required>
                </div>
                <div>
                    <label class="block text-sm font-semibold text-slate-700 mb-1">المقاطعة / الدائرة / البلدية</label>
                    <input type="text" name="from_daira" placeholder="مثال: الحروش، عزابة، تمانراست..." class="w-full p-3 rounded-xl border border-slate-200 outline-none focus:ring-2 focus:ring-blue-500" required>
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <label class="block text-sm font-semibold text-slate-700 mb-1">رقم التعريف الوطني</label>
                    <input type="text" name="national_id" class="w-full p-3 rounded-xl border border-slate-200 outline-none focus:ring-2 focus:ring-blue-500" required>
                </div>
                <div>
                    <label class="block text-sm font-semibold text-slate-700 mb-1">بطاقة التعريف الوطنية (صورة / PDF)</label>
                    <input type="file" name="id_card_image" accept="image/*,.pdf" class="w-full p-2.5 rounded-xl border border-slate-200 bg-slate-50 text-sm" required>
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <label class="block text-sm font-semibold text-slate-700 mb-1">رقم الهاتف للاتصال</label>
                    <input type="tel" name="phone_number" placeholder="0661234567" class="w-full p-3 rounded-xl border border-slate-200 outline-none focus:ring-2 focus:ring-blue-500" required>
                </div>
                <div>
                    <label class="block text-sm font-semibold text-slate-700 mb-1">رقم الواتساب (الصيغة الدولية)</label>
                    <input type="tel" name="whatsapp_number" placeholder="213661234567" class="w-full p-3 rounded-xl border border-slate-200 outline-none focus:ring-2 focus:ring-blue-500">
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div class="md:col-span-1">
                    <label class="block text-sm font-semibold text-slate-700 mb-1">الحمولة القصوى (طن)</label>
                    <input type="number" step="0.1" name="capacity" placeholder="مثال: 12.5" class="w-full p-3 rounded-xl border border-slate-200 outline-none focus:ring-2 focus:ring-blue-500" required>
                </div>
                <div class="md:col-span-1">
                    <label class="block text-sm font-semibold text-slate-700 mb-1">السعر التقريبي (دج)</label>
                    <input type="number" name="price" placeholder="مثال: 15000" class="w-full p-3 rounded-xl border border-slate-200 outline-none focus:ring-2 focus:ring-blue-500" required>
                </div>
                <div class="md:col-span-1">
                    <label class="block text-sm font-semibold text-slate-700 mb-1">نوع الشاحنة / الحمولة</label>
                    <input type="text" name="cargo_description" placeholder="شاحنة مغلقة، نقل مواد..." class="w-full p-3 rounded-xl border border-slate-200 outline-none focus:ring-2 focus:ring-blue-500" required>
                </div>
            </div>

            <button type="submit" class="w-full py-4 bg-amber-500 hover:bg-amber-600 text-slate-900 font-extrabold rounded-xl shadow-lg shadow-amber-500/20 text-lg transition duration-200">
                تحديث وحفظ بيانات الشاحنة <i class="fa-solid fa-paper-plane mr-2"></i>
            </button>
        </form>
    </div>
</div>

<script>
    // تهيئة الخريطة للسائق (المركز الافتراضي: الجزائر)
    var map = L.map('map').setView([36.75, 3.05], 6);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap'
    }).addTo(map);

    var marker;

    function updateMarker(lat, lng) {
        if (marker) {
            marker.setLatLng([lat, lng]);
        } else {
            marker = L.marker([lat, lng]).addTo(map);
        }
        document.getElementById('lat').value = lat;
        document.getElementById('lng').value = lng;
    }

    map.on('click', function(e) {
        updateMarker(e.latlng.lat, e.latlng.lng);
    });

    // جلب موقع الجهاز تلقائياً
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
            var lat = position.coords.latitude;
            var lng = position.coords.longitude;
            map.setView([lat, lng], 12);
            updateMarker(lat, lng);
        });
    }
</script>
</body>
</html>
'''

HTML_CUSTOMER = BASE_HEAD + '''
<!-- Navbar Header -->
<nav class="bg-slate-900 text-white px-6 py-4 flex justify-between items-center shadow-lg sticky top-0 z-50">
    <div class="flex items-center gap-3">
        <div class="bg-blue-600 text-white p-2.5 rounded-xl shadow-md">
            <i class="fa-solid fa-map-location-dot text-xl"></i>
        </div>
        <div>
            <span class="font-extrabold text-lg tracking-wide block">شواحن Express</span>
            <span class="text-xs text-slate-400">منصة النقل اللوجستي المباشر</span>
        </div>
    </div>
    <div class="flex items-center gap-4">
        <span class="text-sm font-medium text-slate-300 hidden md:inline"><i class="fa-regular fa-user ml-1"></i> {{ session['username'] }}</span>
        <a href="/logout" class="text-xs text-red-400 hover:text-red-300 font-bold bg-slate-800 px-3 py-2 rounded-xl border border-slate-700">
            تسجيل خروج
        </a>
    </div>
</nav>

<div class="max-w-7xl mx-auto px-4 py-6 w-full grid grid-cols-1 lg:grid-cols-12 gap-6 flex-grow">
    
    <!-- الجانب الأيمن: الخريطة والفلترة والتصفية -->
    <div class="lg:col-span-7 flex flex-col space-y-4">
        <!-- خيارات الفلترة السريعة -->
        <div class="bg-white p-5 rounded-2xl shadow-sm border border-slate-200">
            <h3 class="font-bold text-slate-800 text-base mb-3 flex items-center gap-2">
                <i class="fa-solid fa-filter text-blue-600"></i> تصفية وتحديد نطاق البحث
            </h3>
            <form method="GET" action="/customer" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <input type="text" name="wilaya" placeholder="فلترة بالولاية..." value="{{ request.args.get('wilaya', '') }}" class="p-3 bg-slate-50 rounded-xl border border-slate-200 text-sm outline-none focus:ring-2 focus:ring-blue-500">
                <input type="text" name="daira" placeholder="فلترة بالمقاطعة / الدائرة..." value="{{ request.args.get('daira', '') }}" class="p-3 bg-slate-50 rounded-xl border border-slate-200 text-sm outline-none focus:ring-2 focus:ring-blue-500">
                <button type="submit" class="sm:col-span-2 py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl text-sm transition shadow-md shadow-blue-500/20">
                    تطبيق البحث <i class="fa-solid fa-magnifying-glass mr-1"></i>
                </button>
            </form>
        </div>

        <!-- الخريطة التفاعلية -->
        <div class="bg-white p-2 rounded-2xl shadow-sm border border-slate-200 flex-grow min-h-[400px] flex flex-col">
            <div id="customer-map" class="w-full flex-grow rounded-xl border border-slate-100 min-h-[380px]"></div>
        </div>
    </div>

    <!-- الجانب الأيسر: قائمة السائقين المتاحين بالقرب منك -->
    <div class="lg:col-span-5 space-y-4">
        <div class="flex items-center justify-between">
            <h3 class="font-extrabold text-slate-900 text-lg">السائقون المتاحون حالياً</h3>
            <span class="bg-blue-100 text-blue-800 text-xs font-bold px-3 py-1 rounded-full">{{ trucks|length }} شاحنة</span>
        </div>

        <div class="space-y-4 overflow-y-auto max-h-[calc(100vh-180px)] pr-1">
            {% for truck in trucks %}
            <div class="bg-white rounded-2xl p-5 shadow-sm hover:shadow-md border border-slate-200 transition duration-200 relative">
                <div class="flex justify-between items-start mb-2">
                    <div>
                        <h4 class="font-bold text-slate-900 text-base">{{ truck.cargo_description }}</h4>
                        <p class="text-xs text-slate-500 mt-0.5"><i class="fa-solid fa-user-gear text-slate-400"></i> السائق: <span class="font-semibold text-slate-700">{{ truck.driver_name }}</span></p>
                    </div>
                    <span class="bg-amber-100 text-amber-800 text-xs font-bold px-2.5 py-1 rounded-lg">
                        ⭐ {{ truck.rating }}
                    </span>
                </div>

                <div class="my-3 flex flex-wrap gap-2 text-xs">
                    <span class="bg-slate-100 text-slate-700 px-3 py-1 rounded-lg font-medium">
                        <i class="fa-solid fa-location-dot text-red-500 ml-1"></i> {{ truck.from_wilaya }} - {{ truck.from_daira }}
                    </span>
                    <span class="bg-slate-100 text-slate-700 px-3 py-1 rounded-lg font-medium">
                        <i class="fa-solid fa-weight-hanging text-blue-500 ml-1"></i> حمولة {{ truck.capacity }} طن
                    </span>
                </div>

                <div class="flex items-center justify-between border-t border-slate-100 pt-3 mt-3">
                    <div>
                        <span class="text-xs text-slate-400 block">السعر الأولي</span>
                        <span class="text-xl font-extrabold text-slate-900">{{ truck.price }} <span class="text-xs font-normal text-slate-500">دج</span></span>
                    </div>
                    <div class="flex gap-2">
                        <a href="tel:{{ truck.phone_number }}" class="px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold shadow-sm flex items-center gap-1.5 transition">
                            <i class="fa-solid fa-phone"></i> اتصال
                        </a>
                        {% if truck.whatsapp_number %}
                        <a href="https://wa.me/{{ truck.whatsapp_number }}?text=مرحباً،%20أنا%20مهتم%20بحجز%20خدمة%20النقل" target="_blank" class="px-4 py-2.5 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl text-xs font-bold shadow-sm flex items-center gap-1.5 transition">
                            <i class="fa-brands fa-whatsapp text-sm"></i> واتساب
                        </a>
                        {% endif %}
                    </div>
                </div>
            </div>
            {% else %}
            <div class="bg-white p-8 rounded-2xl text-center border border-slate-200">
                <i class="fa-solid fa-truck-empty text-4xl text-slate-300 mb-3"></i>
                <p class="text-slate-600 font-medium text-sm">لا يوجد سائقون متوفرون في النطاق المحدد حالياً.</p>
            </div>
            {% endfor %}
        </div>
    </div>
</div>

<script>
    var map = L.map('customer-map').setView([36.75, 3.05], 6);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap'
    }).addTo(map);

    // إضافة مواقع السائقين كعلامات على الخريطة
    var drivers = [
        {% for truck in trucks %}
            {% if truck.lat and truck.lng %}
            {
                name: "{{ truck.driver_name }}",
                desc: "{{ truck.cargo_description }}",
                phone: "{{ truck.phone_number }}",
                price: "{{ truck.price }}",
                lat: {{ truck.lat }},
                lng: {{ truck.lng }}
            },
            {% endif %}
        {% endfor %}
    ];

    var bounds = [];
    drivers.forEach(function(d) {
        var marker = L.marker([d.lat, d.lng]).addTo(map);
        marker.bindPopup(`
            <div style="direction: rtl; text-align: right; font-family: 'Tajawal', sans-serif;">
                <b style="font-size:14px; color:#1e293b;">${d.name}</b><br>
                <span style="font-size:12px; color:#64748b;">${d.desc}</span><br>
                <b style="color:#2563eb;">السعر: ${d.price} دج</b><br>
                <a href="tel:${d.phone}" style="display:inline-block; margin-top:5px; padding:4px 8px; background:#2563eb; color:white; border-radius:6px; text-decoration:none; font-size:11px;">اتصال الآن</a>
            </div>
        `);
        bounds.push([d.lat, d.lng]);
    });

    if (bounds.length > 0) {
        map.fitBounds(bounds);
    }
</script>
</body>
</html>
'''

HTML_ADMIN = BASE_HEAD + '''
<nav class="bg-slate-900 text-white px-6 py-4 flex justify-between items-center">
    <div class="font-bold text-lg">لوحة التحكم الإدارية - لعور حوسين</div>
    <a href="/logout" class="text-xs bg-red-600 px-3 py-1.5 rounded-lg text-white font-bold">تسجيل الخروج</a>
</nav>

<div class="max-w-7xl mx-auto px-4 py-8 w-full">
    <div class="bg-white rounded-2xl shadow-xl overflow-hidden border border-slate-200">
        <div class="p-6 bg-slate-800 text-white flex justify-between items-center">
            <h3 class="font-bold text-lg">مراجعة وإدارة كافة الشاحنات السائقين</h3>
            <span class="bg-slate-700 px-3 py-1 rounded-full text-xs font-semibold">إجمالي الطلبات: {{ trucks|length }}</span>
        </div>
        
        <div class="overflow-x-auto">
            <table class="w-full text-right text-sm">
                <thead class="bg-slate-100 text-slate-700 uppercase font-bold border-b border-slate-200">
                    <tr>
                        <th class="p-4">السائق</th>
                        <th class="p-4">الموقع (الولاية / المقاطعة)</th>
                        <th class="p-4">الهاتف / الواتس</th>
                        <th class="p-4">الهوية الوطنية</th>
                        <th class="p-4">نوع الحمولة</th>
                        <th class="p-4">السعر</th>
                        <th class="p-4">الحالة</th>
                        <th class="p-4 text-center">الإجراء</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-slate-200">
                    {% for truck in trucks %}
                    <tr class="hover:bg-slate-50 transition">
                        <td class="p-4 font-bold text-slate-900">{{ truck.driver_name }}</td>
                        <td class="p-4"><span class="bg-blue-50 text-blue-700 px-2.5 py-1 rounded-lg font-medium text-xs">{{ truck.from_wilaya }} - {{ truck.from_daira }}</span></td>
                        <td class="p-4">{{ truck.phone_number }}<br><span class="text-xs text-slate-400">واتس: {{ truck.whatsapp_number or 'غير محدد' }}</span></td>
                        <td class="p-4">
                            {% if truck.id_card_image %}
                            <a href="/uploads/{{ truck.id_card_image }}" target="_blank" class="text-blue-600 underline font-semibold text-xs">معاينة الوثيقة</a>
                            {% else %}
                            <span class="text-slate-400">لا يوجد</span>
                            {% endif %}
                        </td>
                        <td class="p-4">{{ truck.cargo_description }} ({{ truck.capacity }} طن)</td>
                        <td class="p-4 font-bold">{{ truck.price }} دج</td>
                        <td class="p-4">
                            {% if truck.is_approved %}
                            <span class="bg-emerald-100 text-emerald-800 text-xs font-bold px-2.5 py-1 rounded-full">مُعتمَد</span>
                            {% else %}
                            <span class="bg-amber-100 text-amber-800 text-xs font-bold px-2.5 py-1 rounded-full">معلق</span>
                            {% endif %}
                        </td>
                        <td class="p-4 text-center space-x-2 space-x-reverse">
                            {% if not truck.is_approved %}
                            <a href="/approve_truck/{{ truck.id }}" class="bg-emerald-600 hover:bg-emerald-700 text-white px-3 py-1.5 rounded-lg text-xs font-bold">موافقة</a>
                            {% endif %}
                            <a href="/delete_truck/{{ truck.id }}" onclick="return confirm('تأكيد الحذف؟');" class="bg-red-600 hover:bg-red-700 text-white px-3 py-1.5 rounded-lg text-xs font-bold">حذف</a>
                        </td>
                    </tr>
                    {% else %}
                    <tr><td colspan="8" class="p-6 text-center text-slate-400">لا توجد شاحنات مسجلة.</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
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
    my_truck = Truck.query.filter_by(driver_name=session['username']).last()
    return render_template_string(HTML_DRIVER, my_truck=my_truck)

@app.route('/customer')
def customer_dashboard():
    if session.get('role') != 'customer':
        return redirect(url_for('home'))
    
    wilaya = request.args.get('wilaya', '')
    daira = request.args.get('daira', '')

    query = Truck.query.filter_by(is_approved=True)

    if wilaya:
        query = query.filter(Truck.from_wilaya.contains(wilaya))
    if daira:
        query = query.filter(Truck.from_daira.contains(daira))

    trucks = query.all()
    return render_template_string(HTML_CUSTOMER, trucks=trucks)

@app.route('/add_truck', methods=['POST'])
def add_truck():
    if session.get('role') == 'driver':
        national_id = request.form['national_id']
        phone_number = request.form['phone_number']
        whatsapp_number = request.form.get('whatsapp_number', '').replace('+', '').replace(' ', '')
        from_wilaya = request.form['from_wilaya']
        from_daira = request.form['from_daira']
        lat = request.form.get('lat', type=float)
        lng = request.form.get('lng', type=float)
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
            from_daira=from_daira,
            lat=lat,
            lng=lng,
            cargo_description=cargo_description,
            driver_name=session['username'],
            capacity=float(capacity),
            price=float(price),
            is_approved=False
        )
        db.session.add(new_truck)
        db.session.commit()

        flash('تم حفظ بيانات موقع الشاحنة بنجاح، وهي قيد الاعتماد من إدارة المنصة.', 'success')

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
