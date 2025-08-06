from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session, flash
import os
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
import random
from pymongo import MongoClient
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from werkzeug.security import generate_password_hash, check_password_hash

MONGO_URI = "mongodb+srv://tiffinadmin:RCF%401508@rcf.ic4jzf6.mongodb.net/?retryWrites=true&w=majority&appName=RCF"

client = MongoClient(MONGO_URI)
db = client['tiffin_admin']             # Your database name
collection = db['credentials']          # Your collection name




app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a secure key
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = '1234'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'rcftifiin@gmail.com'  # ✅ Your Gmail ID
app.config['MAIL_PASSWORD'] = 'bfvo ajcl hbpf gukp'     # ✅ App password from Gmail

mail = Mail(app)
otp_store = {}  # Temporary dictionary

@app.route('/admin/send-otp', methods=['GET', 'POST'])
def send_otp():
    error = message = None
    if request.method == 'POST':
        email = request.form.get('email')

        if not email:
            error = "❌ Email is required."
        else:
            admin = collection.find_one({'email': email})

            if not admin:
                error = "❌ This email is not registered."
            else:
                otp = str(random.randint(100000, 999999))
                otp_store[email] = otp
                try:
                    msg = Message('Your OTP Code', sender=app.config['MAIL_USERNAME'], recipients=[email])
                    msg.body = f'Your OTP code is: {otp}'
                    mail.send(msg)
                    return redirect(url_for('verify_otp', email=email))
                except Exception as e:
                    print(e)
                    error = "❌ Failed to send OTP. Check email config."

    return render_template('send_otp.html', error=error, message=message)



@app.route('/admin/verify-otp/<email>', methods=['GET', 'POST'])
def verify_otp(email):
    message = error = None

    if request.method == 'POST':
        entered_otp = request.form.get('otp')

        # ✅ Use global dictionary directly
        stored_otp = otp_store.get(email)

        if not stored_otp:
            error = "Session expired or OTP not sent. Please request again."
        elif entered_otp == stored_otp:
            session['otp_verified'] = True
            session['verified_email'] = email
            return redirect(url_for('reset_password'))
        else:
            error = "❌ Invalid OTP. Please try again."

    return render_template('verify_otp.html', email=email, error=error, message=message)




@app.route('/admin/reset-password', methods=['GET', 'POST'])
def reset_password():
    if not session.get('otp_verified'):
        return redirect(url_for('admin_login'))

    error = message = None

    if request.method == 'POST':
        new_user = request.form.get('new_username')
        new_pass = request.form.get('new_password')

        hashed = generate_password_hash(new_pass)

        # Update admin in MongoDB
        result = collection.update_one(
            {"email": session.get('verified_email')},  # Find by email
            {"$set": {
                "username": new_user,
                "password": hashed
            }}
        )

        if result.modified_count:
            # Clear session after success
            session.pop('otp_verified', None)
            session.pop('verified_email', None)
            session['show_reset_message'] = True
            return render_template('reset_success.html')
        else:
            error = "❌ Failed to update credentials. Try again."

    return render_template('admin_reset_password.html', error=error, message=message)





# PDF Upload Allowed Types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 🏠 Home Page
@app.route('/')
def index():
    pdf_files = os.listdir(app.config['UPLOAD_FOLDER']) if os.path.exists(app.config['UPLOAD_FOLDER']) else []
    return render_template('index.html', menu_pdf=pdf_files[0] if pdf_files else None)

# 📩 Contact Form Handler
@app.route('/contact', methods=['POST'])
def contact():
    name = request.form.get('name')
    phone = request.form.get('phone')
    message = request.form.get('message')
    print(f"New Contact: {name}, {phone}, {message}")
    flash("Thank you! We'll contact you shortly.")
    return redirect('/')

# 🔐 Admin Login
import json

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        admin = collection.find_one({'username': username})

        if admin and check_password_hash(admin['password'], password):
            session['admin_logged_in'] = True
            return redirect(url_for('admin_upload'))
        else:
            error = '❌ Invalid credentials'

    return render_template('admin_login.html', error=error)





# ⬆️ Admin Upload PDF
@app.route('/admin/upload', methods=['GET', 'POST'])
def admin_upload():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    # PDF upload logic
    if request.method == 'POST' and 'menu_pdf' in request.files:
        file = request.files['menu_pdf']
        if file and allowed_file(file.filename):
            for f in os.listdir(app.config['UPLOAD_FOLDER']):
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], f))
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash("✅ PDF uploaded successfully!", 'pdf')  # ✅ PDF-specific message with category

            return redirect(url_for('admin_upload'))

    # Load gallery preview
    gallery_folder = os.path.join('static', 'gallery')
    gallery_images = []
    if os.path.exists(gallery_folder):
        gallery_images = [img for img in os.listdir(gallery_folder) if img.lower().endswith(('.jpg', '.jpeg', '.png'))][:4]

    return render_template('admin_upload.html', gallery_images=gallery_images)


# 🚪 Logout
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

# 📄 Serve PDF
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/admin/forgot', methods=['GET', 'POST'])
def admin_forgot():
    error = None
    message = None

    if request.method == 'POST':
        email = request.form.get('email')

        # ✅ STEP: Check if entered email matches MongoDB admin
        admin = collection.find_one({'email': email})

        if not admin:
            error = "❌ This email is not registered as admin."
        else:
            # Proceed to generate and store OTP
            otp = str(random.randint(100000, 999999))
            session['otp'] = otp
            session['reset_email'] = email
            message = f"✅ OTP has been sent to {email} (Actually not sent — just for demo: {otp})"
            return redirect(url_for('otp_verify'))

    return render_template('admin_forgot.html', error=error, message=message)





# Run


@app.route('/admin/reset', methods=['GET', 'POST'])
def admin_reset():
    error = None
    message = None

    if request.method == 'POST':
        old_user = request.form['old_username'].strip()
        old_pass = request.form['old_password'].strip()
        new_user = request.form['new_username'].strip()
        new_pass = request.form['new_password'].strip()

        try:
            # 🔍 Find admin with old username
            admin = collection.find_one({'username': old_user})

            if admin and check_password_hash(admin['password'], old_pass):
                # ✅ Update new credentials
                new_hashed_pass = generate_password_hash(new_pass)

                collection.update_one(
                    {'username': old_user},
                    {'$set': {
                        'username': new_user,
                        'password': new_hashed_pass
                    }}
                )

                # 🔐 Log out the current session
                session.pop('admin_logged_in', None)

                message = "✅ Credentials updated successfully! Please log in again."

            else:
                error = "❌ Old credentials are incorrect."

        except Exception as e:
            error = f"Error: {str(e)}"

    return render_template('admin_reset.html', error=error, message=message)


# 📸 Upload Gallery Images (4 inputs - fixed names)


GALLERY_FOLDER = 'static/gallery'
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png'}

app.config['GALLERY_FOLDER'] = GALLERY_FOLDER

def allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

@app.route('/admin/upload-gallery', methods=['POST'])
def admin_upload_images():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    for i in range(1, 5):
        file = request.files.get(f'image{i}')
        if file and allowed_image(file.filename):
            filename = f'gallery{i}.jpg'
            path = os.path.join(app.config['GALLERY_FOLDER'], filename)
            if os.path.exists(path):
                os.remove(path)  # Delete previous
            file.save(path)

    flash("✅ Gallery images uploaded successfully!", 'gallery')
    return redirect(url_for('admin_upload'))








# Run
if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)

    
