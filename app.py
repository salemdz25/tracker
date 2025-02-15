from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import shutil
import json
from werkzeug.utils import secure_filename
import time

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'orders.db')

# إنشاء مجلد النسخ الاحتياطي إذا لم يكن موجوداً
BACKUP_FOLDER = os.path.join(basedir, 'backups')
if not os.path.exists(BACKUP_FOLDER):
    os.makedirs(BACKUP_FOLDER)

# إنشاء مجلد للصور
UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dkjf84nf7@3nf83#nf8'  # More secure secret key
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=31)  # Session lasts for 31 days
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
db = SQLAlchemy(app)

# إعداد نظام تسجيل الدخول
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Algerian States List
ALGERIAN_STATES = [
    'Adrar', 'Chlef', 'Laghouat', 'Oum El Bouaghi', 'Batna', 'Béjaïa', 'Biskra',
    'Béchar', 'Blida', 'Bouira', 'Tamanrasset', 'Tébessa', 'Tlemcen', 'Tiaret',
    'Tizi Ouzou', 'Alger', 'Djelfa', 'Jijel', 'Sétif', 'Saïda', 'Skikda',
    'Sidi Bel Abbès', 'Annaba', 'Guelma', 'Constantine', 'Médéa', 'Mostaganem',
    "M'Sila", 'Mascara', 'Ouargla', 'Oran', 'El Bayadh', 'Illizi', 'Bordj Bou Arréridj',
    'Boumerdès', 'El Tarf', 'Tindouf', 'Tissemsilt', 'El Oued', 'Khenchela',
    'Souk Ahras', 'Tipaza', 'Mila', 'Aïn Defla', 'Naâma', 'Aïn Témouchent',
    'Ghardaïa', 'Relizane'
]

# دالة لتحويل البيانات إلى JSON
def serialize_data():
    data = {
        'users': [],
        'orders': []
    }
    
    # حفظ بيانات المستخدمين
    users = User.query.all()
    for user in users:
        user_data = {
            'id': user.id,
            'username': user.username,
            'password': user.password
        }
        data['users'].append(user_data)
    
    # حفظ بيانات الطلبيات
    orders = Order.query.all()
    for order in orders:
        order_data = {
            'id': order.id,
            'user_id': order.user_id,
            'customer_name': order.customer_name,
            'customer_phone': order.customer_phone,
            'customer_state': order.customer_state,
            'customer_address': order.customer_address,
            'product_type': order.product_type,
            'price': order.price,
            'delivery_type': order.delivery_type,
            'delivery_company': order.delivery_company,
            'status': order.status,
            'created_at': order.created_at.isoformat()
        }
        data['orders'].append(order_data)
    
    return data

# دالة لاستعادة البيانات من JSON
def deserialize_data(data):
    db.drop_all()
    db.create_all()
    
    # استعادة بيانات المستخدمين
    for user_data in data['users']:
        user = User(
            id=user_data['id'],
            username=user_data['username'],
            password=user_data['password']
        )
        db.session.add(user)
    
    # استعادة بيانات الطلبيات
    for order_data in data['orders']:
        order = Order(
            id=order_data['id'],
            user_id=order_data['user_id'],
            customer_name=order_data['customer_name'],
            customer_phone=order_data['customer_phone'],
            customer_state=order_data['customer_state'],
            customer_address=order_data['customer_address'],
            product_type=order_data['product_type'],
            price=order_data['price'],
            delivery_type=order_data['delivery_type'],
            delivery_company=order_data.get('delivery_company'),
            status=order_data['status'],
            created_at=datetime.fromisoformat(order_data['created_at'])
        )
        db.session.add(order)
    
    db.session.commit()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    profile_image = db.Column(db.String(200), default='default.png')
    orders = db.relationship('Order', backref='user', lazy=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    customer_state = db.Column(db.String(50), nullable=False)
    customer_address = db.Column(db.String(200), nullable=False)
    product_type = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    delivery_type = db.Column(db.String(20), nullable=False)  # 'office', 'home', 'free'
    delivery_company = db.Column(db.String(50))  # 'yalidin', 'zr_express'
    status = db.Column(db.String(50), default='pending')  # pending, processing, delivered
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Company(db.Model):
    __tablename__ = 'company'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(200))
    prices = db.relationship('DeliveryPrice', back_populates='company')

class DeliveryPrice(db.Model):
    __tablename__ = 'delivery_prices'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    wilaya = db.Column(db.String(100), nullable=False)
    home_delivery_price = db.Column(db.Float, default=0.0)
    office_delivery_price = db.Column(db.Float, default=0.0)
    
    company = db.relationship("Company", back_populates="prices")

def is_valid_algerian_phone(phone):
    """التحقق من صحة رقم الهاتف الجزائري"""
    import re
    pattern = r'^(05|06|07)[0-9]{8}$'
    return bool(re.match(pattern, phone))

def check_yalidin_status(tracking_number, api_id, api_token):
    """التحقق من حالة الطلب في Yalidin"""
    try:
        # هنا سيتم إضافة طلب API الفعلي إلى Yalidin
        # مثال افتراضي للتجربة
        statuses = {
            'pending': 'في الانتظار',
            'processing': 'قيد المعالجة',
            'delivered': 'تم التسليم'
        }
        return {'status': 'success', 'delivery_status': 'processing'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def check_zr_express_status(tracking_number, token, cle):
    """التحقق من حالة الطلب في ZR Express"""
    try:
        # هنا سيتم إضافة طلب API الفعلي إلى ZR Express
        # مثال افتراضي للتجربة
        statuses = {
            'pending': 'في الانتظار',
            'processing': 'جاري التوصيل',
            'delivered': 'تم التوصيل'
        }
        return {'status': 'success', 'delivery_status': 'processing'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        activation_code = request.form['activation_code']
        
        # التحقق من كود التفعيل
        if activation_code != '2008':
            flash('كود التفعيل غير صحيح')
            return redirect(url_for('register'))
        
        # التحقق من وجود المستخدم
        if User.query.filter_by(username=username).first():
            flash('اسم المستخدم مستخدم بالفعل')
            return redirect(url_for('register'))
        
        # إنشاء مستخدم جديد
        user = User(username=username, password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        
        flash('تم التسجيل بنجاح')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            remember = True if request.form.get('remember') else False
            login_user(user, remember=remember)
            flash('تم تسجيل الدخول بنجاح')
            return redirect(url_for('index'))
        flash('خطأ في اسم المستخدم أو كلمة المرور')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    # إنشاء نسخة احتياطية قبل تسجيل الخروج
    if current_user.username == 'admin':
        try:
            # حفظ البيانات
            data = serialize_data()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'backup_auto_{timestamp}.json'
            filepath = os.path.join(BACKUP_FOLDER, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            
            # نسخ قاعدة البيانات
            db_backup = f'orders_auto_{timestamp}.db'
            db_backup_path = os.path.join(BACKUP_FOLDER, db_backup)
            shutil.copy2(db_path, db_backup_path)
            
            # حذف النسخ القديمة (الاحتفاظ بآخر 5 نسخ فقط)
            auto_backups = [f for f in os.listdir(BACKUP_FOLDER) if f.startswith('backup_auto_')]
            auto_backups.sort(reverse=True)
            
            for old_backup in auto_backups[5:]:  # حذف كل النسخ بعد الخمس نسخ الأحدث
                old_path = os.path.join(BACKUP_FOLDER, old_backup)
                os.remove(old_path)
                # حذف ملف قاعدة البيانات المقابل
                old_db = old_backup.replace('backup_auto_', 'orders_auto_').replace('.json', '.db')
                old_db_path = os.path.join(BACKUP_FOLDER, old_db)
                if os.path.exists(old_db_path):
                    os.remove(old_db_path)
            
            flash('تم حفظ نسخة احتياطية بنجاح')
        except Exception as e:
            flash(f'حدث خطأ أثناء حفظ النسخة الاحتياطية: {str(e)}')
    
    logout_user()
    flash('تم تسجيل الخروج بنجاح')
    return redirect(url_for('login'))

@app.route('/create_order', methods=['GET', 'POST'])
@login_required
def create_order():
    if request.method == 'POST':
        phone = request.form['customer_phone']
        if not is_valid_algerian_phone(phone):
            flash('رقم الهاتف غير صحيح. يجب أن يبدأ بـ 05 أو 06 أو 07 ويتكون من 10 أرقام')
            return redirect(url_for('create_order'))
            
        order = Order(
            user_id=current_user.id,
            customer_name=request.form['customer_name'],
            customer_phone=phone,
            customer_state=request.form['customer_state'],
            customer_address=request.form['customer_address'],
            product_type=request.form['product_type'],
            price=float(request.form['price']),
            delivery_type=request.form['delivery_type'],
            delivery_company=request.form.get('delivery_company')
        )
        db.session.add(order)
        db.session.commit()
        flash('تم إنشاء الطلب بنجاح')
        return redirect(url_for('track_orders'))
    return render_template('create_order.html', states=ALGERIAN_STATES)

@app.route('/track_orders', methods=['GET'])
@login_required
def track_orders():
    search_name = request.args.get('search_name', '').strip()
    orders = Order.query.filter_by(user_id=current_user.id)
    
    if search_name:
        orders = orders.filter(Order.customer_name.ilike(f'%{search_name}%'))
    
    orders = orders.order_by(Order.created_at.desc()).all()
    return render_template('track_orders.html', orders=orders, search_name=search_name)

@app.route('/revenue', methods=['GET'])
@login_required
def revenue():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # تحويل التواريخ إلى كائنات datetime
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        # تعيين نهاية اليوم
        end_date = end_date.replace(hour=23, minute=59, second=59)
    
    # الحصول على الطلبيات
    orders_query = Order.query.filter_by(user_id=current_user.id)
    
    if start_date:
        orders_query = orders_query.filter(Order.created_at >= start_date)
    if end_date:
        orders_query = orders_query.filter(Order.created_at <= end_date)
    
    orders = orders_query.order_by(Order.created_at.desc()).all()
    
    # حساب الإحصائيات
    total_revenue = sum(order.price for order in orders)
    home_delivery = sum(order.price for order in orders if order.delivery_type == 'home')
    office_delivery = sum(order.price for order in orders if order.delivery_type == 'office')
    free_delivery = sum(order.price for order in orders if order.delivery_type == 'free')
    
    # حساب الإيرادات حسب الحالة
    pending_revenue = sum(order.price for order in orders if order.status == 'pending')
    processing_revenue = sum(order.price for order in orders if order.status == 'processing')
    delivered_revenue = sum(order.price for order in orders if order.status == 'delivered')
    
    # حساب إيرادات الشهر الحالي
    current_month = datetime.now().month
    current_year = datetime.now().year
    monthly_orders = [order for order in orders 
                     if order.created_at.month == current_month 
                     and order.created_at.year == current_year]
    monthly_revenue = sum(order.price for order in monthly_orders)
    
    return render_template('revenue.html',
                         orders=orders,
                         total_revenue=total_revenue,
                         home_delivery=home_delivery,
                         office_delivery=office_delivery,
                         free_delivery=free_delivery,
                         pending_revenue=pending_revenue,
                         processing_revenue=processing_revenue,
                         delivered_revenue=delivered_revenue,
                         monthly_revenue=monthly_revenue,
                         start_date=start_date.strftime('%Y-%m-%d') if start_date else '',
                         end_date=end_date.strftime('%Y-%m-%d') if end_date else '')

@app.route('/backup', methods=['GET', 'POST'])
@login_required
def backup():
    if not current_user.username == 'admin':
        flash('عذراً، هذه الصفحة للمشرف فقط')
        return redirect(url_for('index'))
    
    backups = []
    for filename in os.listdir(BACKUP_FOLDER):
        if filename.endswith('.json'):
            filepath = os.path.join(BACKUP_FOLDER, filename)
            backup_time = datetime.fromtimestamp(os.path.getctime(filepath))
            backups.append({
                'filename': filename,
                'created_at': backup_time,
                'size': os.path.getsize(filepath)
            })
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'create':
            # إنشاء نسخة احتياطية جديدة
            data = serialize_data()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'backup_{timestamp}.json'
            filepath = os.path.join(BACKUP_FOLDER, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            
            # نسخ ملف قاعدة البيانات
            db_backup = f'orders_{timestamp}.db'
            db_backup_path = os.path.join(BACKUP_FOLDER, db_backup)
            shutil.copy2(db_path, db_backup_path)
            
            flash('تم إنشاء نسخة احتياطية بنجاح')
            return redirect(url_for('backup'))
        
        elif action == 'restore':
            # استعادة من نسخة احتياطية
            backup_file = request.form.get('backup_file')
            if backup_file:
                filepath = os.path.join(BACKUP_FOLDER, backup_file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                try:
                    deserialize_data(data)
                    flash('تم استعادة النسخة الاحتياطية بنجاح')
                except Exception as e:
                    flash(f'حدث خطأ أثناء استعادة النسخة الاحتياطية: {str(e)}')
            
            return redirect(url_for('backup'))
    
    return render_template('backup.html', backups=backups)

@app.route('/delivery_companies', methods=['GET', 'POST'])
@login_required
def delivery_companies():
    # الحصول على بيانات الشركات
    yalidin = Company.query.filter_by(name='yalidin').first()
    zr_express = Company.query.filter_by(name='zr_express').first()
    
    if request.method == 'POST':
        company_name = request.form.get('company_name')
        
        if company_name == 'yalidin':
            # تحديث بيانات Yalidin
            if not yalidin:
                yalidin = Company(name='yalidin')
            yalidin.api_id = request.form.get('api_id')
            yalidin.api_token = request.form.get('api_token')
            db.session.add(yalidin)
            
        elif company_name == 'zr_express':
            # تحديث بيانات ZR Express
            if not zr_express:
                zr_express = Company(name='zr_express')
            zr_express.token = request.form.get('token')
            zr_express.cle = request.form.get('cle')
            db.session.add(zr_express)
        
        db.session.commit()
        flash('تم تحديث بيانات الشركة بنجاح')
        return redirect(url_for('delivery_companies'))
    
    return render_template('delivery_companies.html', yalidin=yalidin, zr_express=zr_express)

@app.route('/delivery_prices')
@login_required
def delivery_prices():
    from wilayas import ALGERIA_WILAYAS
    companies = Company.query.all()
    return render_template('delivery_prices.html', companies=companies, wilayas=ALGERIA_WILAYAS)

@app.route('/add_price', methods=['POST'])
@login_required
def add_price():
    data = request.get_json()
    price_type = data.get('price_type')
    value = float(data.get('value', 0))
    wilaya = data.get('wilaya')
    company_id = data.get('company_id')
    
    if not all([price_type, wilaya, company_id]):
        return jsonify({'success': False, 'message': 'بيانات غير مكتملة'})
    
    company = Company.query.get(company_id)
    if not company:
        return jsonify({'success': False, 'message': 'الشركة غير موجودة'})
    
    # البحث عن السعر الحالي أو إنشاء واحد جديد
    price = DeliveryPrice.query.filter_by(company_id=company_id, wilaya=wilaya).first()
    if not price:
        price = DeliveryPrice(company_id=company_id, wilaya=wilaya)
        db.session.add(price)
    
    # تحديث السعر المناسب
    if price_type == 'home':
        price.home_delivery_price = value
    else:
        price.office_delivery_price = value
    
    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'تم إضافة/تحديث السعر بنجاح',
            'price_id': price.id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/update_price/<int:price_id>', methods=['POST'])
@login_required
def update_price(price_id):
    data = request.get_json()
    price = DeliveryPrice.query.get_or_404(price_id)
    
    price_type = data.get('price_type')
    value = float(data.get('value', 0))
    
    if price_type == 'home':
        price.home_delivery_price = value
    elif price_type == 'office':
        price.office_delivery_price = value
    
    try:
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/delete_price/<int:price_id>', methods=['POST'])
@login_required
def delete_price(price_id):
    price = DeliveryPrice.query.get_or_404(price_id)
    
    try:
        # بدلاً من حذف السعر، نقوم بتصفير القيم
        price.home_delivery_price = 0
        price.office_delivery_price = 0
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        username = request.form.get('username')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        profile_image = request.files.get('profile_image')
        
        # التحقق من صحة كلمة المرور الحالية
        if not check_password_hash(current_user.password, current_password):
            flash('كلمة المرور الحالية غير صحيحة')
            return redirect(url_for('settings'))
        
        # تحديث اسم المستخدم إذا تم تغييره
        if username and username != current_user.username:
            if User.query.filter_by(username=username).first():
                flash('اسم المستخدم مستخدم بالفعل')
                return redirect(url_for('settings'))
            current_user.username = username
        
        # تحديث كلمة المرور إذا تم تغييرها
        if new_password:
            current_user.password = generate_password_hash(new_password)
        
        # تحديث صورة الملف الشخصي إذا تم تحميلها
        if profile_image:
            # التحقق من امتداد الملف
            if profile_image.filename != '':
                file_ext = os.path.splitext(profile_image.filename)[1].lower()
                if file_ext not in ['.jpg', '.jpeg', '.png']:
                    flash('يرجى تحميل صورة بامتداد jpg أو jpeg أو png')
                    return redirect(url_for('settings'))
                
                # حفظ الصورة
                filename = secure_filename(f'profile_{current_user.id}{file_ext}')
                profile_image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                current_user.profile_image = filename
        
        db.session.commit()
        flash('تم تحديث البيانات بنجاح')
        return redirect(url_for('settings'))
    
    return render_template('settings.html')

@app.route('/delete_order/<int:order_id>')
@login_required
def delete_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('لا يمكنك حذف هذا الطلب')
        return redirect(url_for('track_orders'))
    
    db.session.delete(order)
    db.session.commit()
    flash('تم حذف الطلب بنجاح')
    return redirect(url_for('track_orders'))

@app.route('/edit_order/<int:order_id>', methods=['GET', 'POST'])
@login_required
def edit_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('لا يمكنك تعديل هذا الطلب')
        return redirect(url_for('track_orders'))
    
    if request.method == 'POST':
        # التحقق من رقم الهاتف
        phone = request.form['customer_phone']
        if not is_valid_algerian_phone(phone):
            flash('رقم الهاتف غير صحيح. يجب أن يبدأ بـ 05 أو 06 أو 07 ويتكون من 10 أرقام')
            return redirect(url_for('edit_order', order_id=order_id))
        
        order.customer_name = request.form['customer_name']
        order.customer_phone = phone
        order.customer_state = request.form['customer_state']
        order.customer_address = request.form['customer_address']
        order.product_type = request.form['product_type']
        order.price = request.form['price']
        order.delivery_type = request.form['delivery_type']
        order.delivery_company = request.form.get('delivery_company')
        order.status = request.form['status']
        
        db.session.commit()
        flash('تم تحديث الطلب بنجاح')
        return redirect(url_for('track_orders'))
    
    return render_template('edit_order.html', order=order)

@app.route('/update_status/<int:order_id>', methods=['POST'])
@login_required
def update_status(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'لا يمكنك تعديل هذا الطلب'})
    
    new_status = request.form.get('status')
    if new_status not in ['pending', 'processing', 'delivered']:
        return jsonify({'success': False, 'message': 'حالة غير صالحة'})
    
    order.status = new_status
    db.session.commit()
    
    status_text = {
        'pending': 'قيد الانتظار',
        'processing': 'قيد المعالجة',
        'delivered': 'تم التوصيل'
    }
    
    return jsonify({
        'success': True,
        'message': 'تم تحديث الحالة بنجاح',
        'status': new_status,
        'status_text': status_text[new_status]
    })

@app.route('/check_delivery_status/<int:order_id>')
@login_required
def check_delivery_status(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'لا يمكنك التحقق من حالة هذا الطلب'})
    
    # التحقق من شركة التوصيل
    if not order.delivery_company:
        return jsonify({'success': False, 'message': 'لم يتم تحديد شركة التوصيل'})
    
    # الحصول على بيانات API لشركة التوصيل
    delivery_company = Company.query.filter_by(name=order.delivery_company).first()
    if not delivery_company:
        return jsonify({'success': False, 'message': 'لم يتم العثور على بيانات شركة التوصيل'})
    
    # التحقق من الحالة حسب الشركة
    status_result = None
    if order.delivery_company == 'yalidin':
        if not delivery_company.api_id or not delivery_company.api_token:
            return jsonify({'success': False, 'message': 'بيانات API غير مكتملة'})
        status_result = check_yalidin_status(
            order.id,
            delivery_company.api_id,
            delivery_company.api_token
        )
    elif order.delivery_company == 'zr_express':
        if not delivery_company.token or not delivery_company.cle:
            return jsonify({'success': False, 'message': 'بيانات API غير مكتملة'})
        status_result = check_zr_express_status(
            order.id,
            delivery_company.token,
            delivery_company.cle
        )
    
    if status_result and status_result['status'] == 'success':
        # تحديث حالة الطلب
        new_status = status_result['delivery_status']
        if new_status != order.status:
            order.status = new_status
            db.session.commit()
        
        status_text = {
            'pending': 'قيد الانتظار',
            'processing': 'قيد المعالجة',
            'delivered': 'تم التوصيل'
        }
        
        return jsonify({
            'success': True,
            'status': new_status,
            'status_text': status_text[new_status],
            'message': 'تم تحديث حالة الطلب'
        })
    
    return jsonify({'success': False, 'message': 'فشل في التحقق من حالة الطلب'})

@app.route('/check_all_orders_status')
@login_required
def check_all_orders_status():
    """تحديث حالة جميع الطلبات"""
    orders = Order.query.filter_by(user_id=current_user.id).all()
    updated_orders = []
    
    for order in orders:
        if order.delivery_company:
            response = check_delivery_status(order.id)
            if response.json['success']:
                updated_orders.append(order.id)
    
    return jsonify({
        'success': True,
        'message': f'تم تحديث حالة {len(updated_orders)} طلبات',
        'updated_orders': updated_orders
    })

@app.route('/upload_company_image/<int:company_id>', methods=['POST'])
@login_required
def upload_company_image(company_id):
    company = Company.query.get_or_404(company_id)
    
    if 'image' not in request.files:
        flash('لم يتم اختيار صورة', 'error')
        return redirect(url_for('delivery_prices'))
    
    file = request.files['image']
    if file.filename == '':
        flash('لم يتم اختيار صورة', 'error')
        return redirect(url_for('delivery_prices'))
    
    if file and allowed_file(file.filename):
        # حذف الصورة القديمة إذا كانت موجودة وليست الصورة الافتراضية
        if company.image and company.image != 'default_company.png':
            old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], company.image)
            if os.path.exists(old_image_path):
                os.remove(old_image_path)
        
        # حفظ الصورة الجديدة
        filename = secure_filename(f"company_{company_id}_{int(time.time())}{os.path.splitext(file.filename)[1]}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        # تحديث اسم الصورة في قاعدة البيانات
        company.image = filename
        db.session.commit()
        
        flash('تم تحميل الصورة بنجاح', 'success')
    else:
        flash('نوع الملف غير مسموح به', 'error')
    
    return redirect(url_for('delivery_prices'))

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

if __name__ == '__main__':
    app.app_context().push()  # Push an application context
    db.create_all()
    
    # إضافة شركات التوصيل الافتراضية إذا لم تكن موجودة
    if not Company.query.first():
        yalidin = Company(
            name='yalidin',
            image='default_company.png'
        )
        db.session.add(yalidin)
        
        zr_express = Company(
            name='zr_express',
            image='default_company.png'
        )
        db.session.add(zr_express)
        db.session.commit()
        
        # تهيئة أسعار التوصيل للولايات
        from wilayas import initialize_wilaya_prices
        initialize_wilaya_prices()
    
    app.run(debug=True)
