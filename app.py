from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
import qrcode
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Change in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///printsmart.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['QR_FOLDER'] = 'static/qr_codes'
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'docx', 'png', 'jpg', 'jpeg'}

db = SQLAlchemy(app)

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['QR_FOLDER'], exist_ok=True)

# Database Model
class Order(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = db.Column(db.String(100), nullable=False)
    copies = db.Column(db.Integer, nullable=False)
    color = db.Column(db.Boolean, nullable=False)  # True for color, False for black-white
    price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, paid
    qr_code_path = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f'<Order {self.id}>'

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Routes
@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        copies = int(request.form['copies'])
        color = request.form.get('color') == 'on'  # Checkbox for color
        price_per_copy = 10.0 if color else 2.0
        total_price = copies * price_per_copy
        
        order = Order(filename=filename, copies=copies, color=color, price=total_price)
        db.session.add(order)
        db.session.commit()
        
        return redirect(url_for('payment', order_id=order.id))
    else:
        flash('Invalid file type')
        return redirect(request.url)

@app.route('/payment/<order_id>')
def payment(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('payment.html', order=order)

@app.route('/pay/<order_id>', methods=['POST'])
def pay(order_id):
    order = Order.query.get_or_404(order_id)
    payment_method = request.form['payment_method']  # 'upi' or 'card'
    # Simulate payment success (always succeeds in demo)
    order.status = 'paid'
    
    # Generate QR code with Order ID
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(order.id)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    qr_filename = f'{order.id}.png'
    qr_path = os.path.join(app.config['QR_FOLDER'], qr_filename)
    img.save(qr_path)
    order.qr_code_path = qr_filename
    
    db.session.commit()
    return render_template('success.html', order=order)

@app.route('/admin')
def admin():
    orders = Order.query.filter_by(status='paid').all()
    return render_template('admin.html', orders=orders)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/qr/<filename>')
def qr_file(filename):
    return send_from_directory(app.config['QR_FOLDER'], filename)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
