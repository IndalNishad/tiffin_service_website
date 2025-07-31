from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session, flash
import os
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
import random



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
app.config['MAIL_USERNAME'] = 'shubhammaurya8840@gmail.com'  # ✅ Your Gmail ID
app.config['MAIL_PASSWORD'] = 'bogt rdls gfof mraa'     # ✅ App password from Gmail

mail = Mail(app)
otp_store = {}  # Temporary dictionary

@app.route('/admin/send-otp', methods=['GET', 'POST'])
def send_otp():
    message = error = None
    if request.method == 'POST':
        email = request.form.get('email')

        if not email:
            error = "❌ Email is required."
        else:
            # ✅ Load registered email from admin.json
            if os.path.exists('admin.json'):
                with open('admin.json', 'r') as f:
                    data = json.load(f)
                registered_email = data.get('email')

                # ✅ Match entered email
                if email != registered_email:
                    error = "❌ Enter your registered admin email."
                else:
                    # ✅ Proceed to send OTP
                    otp = str(random.randint(100000, 999999))
                    otp_store[email] = otp
                    try:
                        msg = Message('Your OTP Code', sender=app.config['MAIL_USERNAME'], recipients=[email])
                        msg.body = f'Your OTP code is: {otp}'
                        mail.send(msg)
                        return redirect(url_for('verify_otp', email=email))
                    except Exception as e:
                        print(e)
                        error = "❌ Failed to send OTP. Check email configuration."
            else:
                error = "❌ Admin email not found in system."

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

        # Update admin.json
        with open('admin.json', 'r') as f:
            data = json.load(f)

        data['username'] = new_user
        data['password'] = new_pass

        with open('admin.json', 'w') as f:
            json.dump(data, f)

        # Clear session
        session.pop('otp_verified', None)
        session.pop('verified_email', None)

        # Show success page
        return render_template('reset_success.html')

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

    # Load stored credentials from admin.json
    if os.path.exists('admin.json'):
        with open('admin.json', 'r') as f:
            creds = json.load(f)
        stored_username = creds.get('username', ADMIN_USERNAME)
        stored_password = creds.get('password', ADMIN_PASSWORD)
    else:
        stored_username = ADMIN_USERNAME
        stored_password = ADMIN_PASSWORD

    # 🔐 Show reset message only once
    if session.pop('show_reset_message', None):
        flash("✅ Credentials updated! Please login.")

    if request.method == 'POST':
        if request.form['username'] == stored_username and request.form['password'] == stored_password:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_upload'))
        else:
            error = 'Invalid Credentials'
    
    return render_template('admin_login.html', error=error)




# ⬆️ Admin Upload PDF
@app.route('/admin/upload', methods=['GET', 'POST'])
def admin_upload():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        file = request.files['menu_pdf']
        if file and allowed_file(file.filename):
            for f in os.listdir(app.config['UPLOAD_FOLDER']):
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], f))
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash("PDF Uploaded Successfully!")
            return redirect(url_for('admin_upload'))
    return render_template('admin_upload.html')

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

        with open('admin.json', 'r') as f:
            data = json.load(f)

        # ✅ STEP: Check if entered email matches registered admin email
        if email != data.get('email'):
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
            with open('admin.json', 'r') as f:
                data = json.load(f)

            if old_user == data.get('username') and old_pass == data.get('password'):
                # Update only username and password
                data['username'] = new_user
                data['password'] = new_pass

                with open('admin.json', 'w') as f:
                    json.dump(data, f, indent=4)

                message = "✅ Credentials updated successfully!"
            else:
                error = "❌ Old credentials are incorrect."
        except Exception as e:
            error = f"Error: {str(e)}"

    return render_template('admin_reset.html', error=error, message=message)



# Run
if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)

    
