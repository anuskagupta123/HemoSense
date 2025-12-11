# app.py
import os
import pickle
from flask_mail import Mail, Message

from datetime import timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from models import db, User, Prediction
from ml_utils import prepare_features, get_tips
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "Flask", "templates"),
    static_folder=os.path.join(BASE_DIR, "Flask", "static")
)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "hemosense.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = os.environ.get("HEMO_SECRET", "change_this_secret_please")

db.init_app(app)
app.permanent_session_lifetime = timedelta(minutes=60)

# load model
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model file not found at {MODEL_PATH}. Place your model.pkl here.")

with open(MODEL_PATH, "rb") as f:
    ml_model = pickle.load(f)
    print("✅ Loaded model.pkl!")

# HOME
@app.route("/")
def index():
    return render_template("index.html")

# AUTH (combined login/register)
@app.route("/auth")
def auth():
    return render_template("auth.html")

@app.route("/register", methods=["POST"])
def register():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not name or not email or not password:
        flash("Please fill all fields.", "error")
        return redirect(url_for("auth"))

    existing = User.query.filter_by(email=email).first()
    if existing:
        flash("Email already registered. Please login.", "error")
        return redirect(url_for("auth"))

    user = User(name=name, email=email, password=password)
    db.session.add(user)
    db.session.commit()

    flash("Registration successful. Please login.", "success")
    return redirect(url_for("auth"))

@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    user = User.query.filter_by(email=email).first()
    if user and user.password == password:
        session.permanent = True
        session["user"] = {"id": user.id, "name": user.name, "email": user.email}
        flash(f"Welcome back, {user.name}!", "success")
        return redirect(url_for("dashboard"))
    else:
        flash("Invalid email/password.", "error")
        return redirect(url_for("auth"))

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Logged out.", "info")
    return redirect(url_for("index"))

# PROFILE
@app.route("/profile")
def profile():
    if "user" not in session:
        flash("Please login to continue.", "error")
        return redirect(url_for("auth"))
    user = User.query.filter_by(email=session["user"]["email"]).first()
    return render_template("profile.html", user=user)

# CHANGE PASSWORD
@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    if "user" not in session:
        flash("Please login to continue.", "error")
        return redirect(url_for("auth"))

    user = User.query.filter_by(email=session["user"]["email"]).first()
    if request.method == "POST":
        old = request.form.get("old_password")
        new = request.form.get("new_password")
        confirm = request.form.get("confirm_new")
        if old != user.password:
            flash("Old password incorrect.", "error")
        elif new != confirm:
            flash("New passwords do not match.", "error")
        else:
            user.password = new
            db.session.commit()
            flash("Password updated.", "success")
            return redirect(url_for("profile"))

    return render_template("change_password.html", user=user)

# DASHBOARD
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        flash("Please login to continue.", "error")
        return redirect(url_for("auth"))

    email = session["user"]["email"]
    user = User.query.filter_by(email=email).first()
    preds = Prediction.query.filter_by(user_email=email).order_by(Prediction.timestamp).all()

    total_predictions = len(preds)
    recent_predictions = preds[-6:] if preds else []

    category_counts = {"Normal": 0, "Anemia": 0}
    hb_ranges = {"<7": 0, "7-9.9": 0, "10-12": 0, ">12": 0}

    for p in preds:
        category_counts[p.category] = category_counts.get(p.category, 0) + 1
        hb = p.hb
        if hb < 7:
            hb_ranges["<7"] += 1
        elif hb < 10:
            hb_ranges["7-9.9"] += 1
        elif hb <= 12:
            hb_ranges["10-12"] += 1
        else:
            hb_ranges[">12"] += 1

    return render_template(
        "dashboard.html",
        user_name=user.name,
        total_predictions=total_predictions,
        recent_predictions=recent_predictions,
        category_counts=category_counts,
        hb_ranges=hb_ranges
    )

# PREDICT
@app.route("/predict", methods=["GET", "POST"])
def predict():
    if "user" not in session:
        flash("Please login to continue.", "error")
        return redirect(url_for("auth"))

    result_category = None
    confidence = None
    tips = []
    form_data = {}
    if request.method == "POST":
        form_data = request.form.to_dict()
        try:
            age = int(request.form.get("age", 0))
        except:
            age = 0
        gender = request.form.get("gender", "")
        try:
            hb = float(request.form.get("hb", 0))
        except:
            hb = 0.0

        mch = request.form.get("mch", "")
        mchc = request.form.get("mchc", "")
        mcv = request.form.get("mcv", "")

        if age <= 0 or not gender or hb <= 0:
            flash("Please enter valid Age, Gender and Hemoglobin.", "error")
        else:
            X = prepare_features(age, gender, hb, mch, mchc, mcv)
            try:
                pred = ml_model.predict(X)[0]
            except Exception as e:
                flash(f"Model prediction error: {e}", "error")
                return redirect(url_for("predict"))

            # Try to get probabilities if available
            try:
                prob = ml_model.predict_proba(X)[0]
                confidence = round(float(max(prob) * 100), 2)
            except:
                confidence = None

            label_map = {0: "Normal", 1: "Anemia"}
            result_category = label_map.get(pred, str(pred))

            tips = get_tips(result_category)

            # save
            saved = Prediction(
                user_email=session["user"]["email"],
                age=age,
                gender=gender,
                hb=hb,
                mch=float(mch) if mch else None,
                mchc=float(mchc) if mchc else None,
                mcv=float(mcv) if mcv else None,
                category=result_category,
                confidence=confidence
            )
            db.session.add(saved)
            db.session.commit()
            flash("Prediction completed.", "success")

    return render_template(
        "predict.html",
        result_category=result_category,
        confidence=confidence,
        tips=tips,
        form_data=form_data
    )
    

# Simple API to return tip categories (optional)
@app.route("/api/tips/<category>")
def api_tips(category):
    return jsonify(get_tips(category))

# Create DB tables if needed
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
