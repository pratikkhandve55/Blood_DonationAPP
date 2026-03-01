from flask import Flask, render_template, request, jsonify, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random
import math
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from flask import session

app = Flask(__name__)
app.config['SECRET_KEY'] = "supersecretekey"
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# DATABASE MODELS

class Hospital(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    phone = db.Column(db.String(15), unique=True)
    password = db.Column(db.String(200))
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)


class Donor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    phone = db.Column(db.String(15))
    blood_group = db.Column(db.String(10))
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)


# =====================
# ROUTES (PAGES)
# =====================

@app.route("/")
def home():
    return render_template("/home.html")

@app.route("/hospital_register")
def hospital_register():
    return render_template("hospital_register.html")

@app.route("/donor_register")
def donor_register():
    return render_template("donor_register.html")

@app.route("/hospital_login")
def hospital_login_page():
    return render_template("hospital_login.html")

@app.route("/hospital_dashboard")
def hospital_dashboard():

    if "hospital_id" not in session:
        return redirect("/hospital_login")

    return render_template("hospital_dashboard.html")


# nearest neighbor algo
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Radius of Earth in KM

    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)

    a = (math.sin(d_lat/2) * math.sin(d_lat/2) +
         math.cos(math.radians(lat1)) *
         math.cos(math.radians(lat2)) *
         math.sin(d_lon/2) * math.sin(d_lon/2))

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    distance = R * c
    return distance
#  
# =====================
# API ROUTES
# =====================


@app.route("/api/register_hospital", methods=["POST"])
def register_hospital():
    data = request.json

    existing = Hospital.query.filter_by(phone=data["phone"]).first()
    if existing:
        return jsonify({"error": "Hospital already exists"}), 400

    hashed_password = generate_password_hash(data["password"])

    hospital = Hospital(
        name=data["name"],
        phone=data["phone"],
        password=hashed_password,
        lat=float(data["lat"]),
        lng=float(data["lng"])
    )

    db.session.add(hospital)
    db.session.commit()

    return jsonify({"message": "Hospital Registered Successfully"})

@app.route("/api/register_donor", methods=["POST"])
def register_donor():
    data = request.json

    donor = Donor(
        name=data["name"],
        phone=data["phone"],
        blood_group=data["blood_group"],
        lat=float(data["lat"]),
        lng=float(data["lng"])
    )

    db.session.add(donor)
    db.session.commit()

    return jsonify({"message": "Donor Registered Successfully"})




@app.route("/api/hospital_login", methods=["POST"])
def hospital_login():

    data = request.json

    hospital = Hospital.query.filter_by(phone=data["phone"]).first()

    if not hospital:
        return jsonify({"error": "Hospital not found"}), 404

    if not check_password_hash(hospital.password, data["password"]):
        return jsonify({"error": "Incorrect password"}), 401

    session["hospital_id"] = hospital.id

    return jsonify({"message": "Login Successful"})



# nearest donor fetching 
@app.route('/sos', methods=['POST'])
def sos():

    required_blood = request.form['blood_group']
    patient_name = request.form['patient_name']

    hospital_id = session.get('hospital_id')
    hospital = Hospital.query.get(hospital_id)

    hospital_lat = hospital.lat
    hospital_lng = hospital.lng

    # Filter donors by blood group
    donors = Donor.query.filter_by(blood_group=required_blood).all()

    nearby_donors = []

    for donor in donors:
        distance = calculate_distance(
            hospital_lat, hospital_lng,
            donor.lat, donor.lng
        )

        if distance <= 5:  # 5 KM radius
            nearby_donors.append({
                "name": donor.name,
                "phone": donor.phone,
                "distance": round(distance, 2)
            })

    # Sort by nearest first
    nearby_donors = sorted(nearby_donors, key=lambda x: x['distance'])

    return render_template(
        "hospital_dashboard.html",
        donors=nearby_donors,
        patient_name=patient_name,
        blood_group=required_blood
    )

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=False)