from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session, flash
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a secure key
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = '1234'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
        new_username = request.form.get('new_username')
        new_password = request.form.get('new_password')

        if new_username and new_password:
            with open('admin.json', 'w') as f:
                json.dump({'username': new_username, 'password': new_password}, f)
            message = "✅ Credentials updated successfully. You can now login."
        else:
            error = "❌ Please fill both fields."

    return render_template('admin_forgot.html', error=error, message=message)


# Run
@app.route('/admin/reset', methods=['GET', 'POST'])
def admin_reset():
    error = None
    message = None

    if request.method == 'POST':
        old_user = request.form['old_username']
        old_pass = request.form['old_password']
        new_user = request.form['new_username']
        new_pass = request.form['new_password']

        with open('admin.json', 'r') as f:
            data = json.load(f)

        if old_user == data['username'] and old_pass == data['password']:
            with open('admin.json', 'w') as f:
                json.dump({'username': new_user, 'password': new_pass}, f)
            message = "✅ Credentials updated successfully!"
        else:
            error = "❌ Old credentials are incorrect."

    return render_template('admin_reset.html', error=error, message=message)


# Run
if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)

    
