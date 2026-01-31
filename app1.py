from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
import os
import uuid
import qrcode
from PIL import Image
import io

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change in production
UPLOAD_FOLDER = 'uploads'
QR_FOLDER = 'static/qr_codes'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(QR_FOLDER, exist_ok=True)

# In-memory storage (replace with DB in production)
users = {}  # {email: {'password': pwd, 'orders': []}}
orders = {}  # {order_id: {'user': email, 'file': filename, 'copies': int, 'color': bool, 'sides': str, 'price': float, 'status': str, 'qr': qr_path}}
admin_credentials = {'admin': 'password'}  # Simple admin login

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email in users and users[email]['password'] == password:
            session['user'] = email
            return redirect(url_for('upload'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email not in users:
            users[email] = {'password': password, 'orders': []}
            session['user'] = email
            return redirect(url_for('upload'))
        flash('User exists')
    return render_template('login.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.split('.')[-1].lower() in ['pdf', 'docx', 'jpg', 'png']:
            filename = str(uuid.uuid4()) + '.' + file.filename.split('.')[-1]
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            copies = int(request.form['copies'])
            color = request.form.get('color') == 'on'
            sides = request.form['sides']
            price = calculate_price(copies, color, sides)
            order_id = str(uuid.uuid4())[:8].upper()
            qr_path = generate_qr(order_id)
            orders[order_id] = {
                'user': session['user'],
                'file': filename,
                'copies': copies,
                'color': color,
                'sides': sides,
                'price': price,
                'status': 'Uploaded',
                'qr': qr_path
            }
            users[session['user']]['orders'].append(order_id)
            session['current_order'] = order_id
            return redirect(url_for('payment'))
    return render_template('upload.html')

@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if 'current_order' not in session:
        return redirect(url_for('upload'))
    order_id = session['current_order']
    if request.method == 'POST':
        # Simulate payment
        orders[order_id]['status'] = 'Paid'
        return redirect(url_for('tracking'))
    return render_template('payment.html', order=orders[order_id])

@app.route('/tracking')
def tracking():
    if 'user' not in session:
        return redirect(url_for('login'))
    user_orders = [orders[oid] for oid in users[session['user']]['orders']]
    return render_template('tracking.html', orders=user_orders)

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in admin_credentials and admin_credentials[username] == password:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        flash('Invalid admin credentials')
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    return render_template('admin_dashboard.html', orders=orders)

@app.route('/admin/mark_printed/<order_id>')
def mark_printed(order_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    if order_id in orders:
        orders[order_id]['status'] = 'Printed'
    return redirect(url_for('admin_dashboard'))

@app.route('/qr/<filename>')
def qr_code(filename):
    return send_from_directory(QR_FOLDER, filename)

def calculate_price(copies, color, sides):
    base = 2 if color else 1
    if sides == 'double':
        base *= 1.5
    return base * copies

def generate_qr(order_id):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(f"Order ID: {order_id}")
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    filename = f"{order_id}.png"
    img.save(os.path.join(QR_FOLDER, filename))
    return filename

if __name__ == '__main__':
    app.run(debug=True)
