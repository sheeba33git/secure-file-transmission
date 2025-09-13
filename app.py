from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, File
from blockchain import Blockchain
from config import Config
from datetime import datetime
import os
import hashlib

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
blockchain = Blockchain()

@app.route("/")
def home():
    if "username" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        role ="user"
        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for("register"))
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists!", "danger")
            return redirect(url_for("register"))
        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_pw, role=role)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please login.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session["username"] = user.username
            session["role"] = user.role
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password!", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully!", "info")
    return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))
    if session["role"] == "admin":
        files = File.query.all()
    else:
        files = File.query.filter_by(uploaded_by=session["username"]).all()
    return render_template("index.html", username=session["username"], role=session["role"], files=files)

@app.route("/upload", methods=["POST"])
def upload():
    if "username" not in session:
        return redirect(url_for("login"))
    upfile = request.files["file"]
    if upfile:
        filename = secure_filename(upfile.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        upfile.save(filepath)
        with open(filepath, "rb") as f:
            content = f.read()
        encrypted_content = hashlib.sha256(content).hexdigest()
        encrypted_filename = f"enc_{filename}"
        with open(os.path.join(app.config["UPLOAD_FOLDER"], encrypted_filename), "w") as f:
            f.write(encrypted_content)
        new_file = File(
            filename=filename,
            encrypted_filename=encrypted_filename,
            uploaded_by=session["username"],
            timestamp=datetime.now()
        )
        db.session.add(new_file)
        db.session.commit()
        blockchain.add_block(f"File uploaded: {filename} by {session['username']}")
        flash("File uploaded and encrypted successfully!", "success")
    return render_template("success.html")  # Go to success page after upload

@app.route("/download/<int:file_id>")
def download(file_id):
    if "username" not in session:
        return redirect(url_for("login"))
    file = File.query.get_or_404(file_id)
    if file.uploaded_by != session["username"] and session["role"] != "admin":
        flash("You are not authorized to download this file.", "danger")
        return redirect(url_for("dashboard"))
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    blockchain.add_block(f"File downloaded: {file.filename} by {session['username']}")
    return send_file(filepath, as_attachment=True)

@app.route("/logs")
def logs():
    if "role" not in session or session["role"] != "admin":
        flash("Only admin can view logs!", "danger")
        return redirect(url_for("dashboard"))
    return render_template("logs.html", chain=blockchain.chain)

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403

@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=False)