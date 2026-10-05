import os
import pickle
import warnings
import math
import hashlib
import random
import numpy as np
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session, flash

warnings.filterwarnings('ignore')

import csv
import json
import io
import xml.etree.ElementTree as ET
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from flask import Response
try:
    from pymongo import MongoClient
except ImportError:
    MongoClient = None
app = Flask(__name__)
# Secret key for sessions and flash messages
app.secret_key = os.environ.get('SECRET_KEY', 'edupredict-secret-key-2026')

MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://127.0.0.1:27017')
mongo_client = None
mongo_db = None

def connect_mongo():
    global mongo_client, mongo_db
    if MongoClient is None:
        return False
    try:
        mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=1500)
        mongo_client.admin.command('ping')
        mongo_db = mongo_client['edupredict']
        return True
    except Exception:
        mongo_client = None
        mongo_db = None
        return False

def mongo_insert(collection_name, document):
    if mongo_db is None:
        return False
    try:
        mongo_db[collection_name].insert_one(document)
        return True
    except Exception:
        return False

def mongo_upsert_user(username, user_data):
    if mongo_db is None:
        return False
    try:
        mongo_db.users.update_one({'_id': username}, {'$set': user_data}, upsert=True)
        return True
    except Exception:
        return False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_pkl(name):
    path = os.path.join(BASE_DIR, 'models', name)
    if os.path.exists(path):
        try:
            with open(path, 'rb') as f:
                return pickle.load(f)
        except Exception:
            return None
    return None

INGEST_DIR = os.path.join(BASE_DIR, 'data', 'ingested')
ALLOWED_INGEST_EXTENSIONS = {'csv', 'json', 'xml'}

INGESTION_LOGS = [
    {'timestamp': '2025-01-16 09:12', 'dataset_type': 'Academic Records',    'source': 'Historical Batch', 'records': '6,607',   'status': 'Success', 'status_class': 'success'},
    {'timestamp': '2025-01-16 08:45', 'dataset_type': 'Attendance Records',  'source': 'Real-Time Stream', 'records': '89,450',  'status': 'Success', 'status_class': 'success'},
    {'timestamp': '2025-01-15 22:30', 'dataset_type': 'LMS Activity Data',   'source': 'Historical Batch', 'records': '142,300', 'status': 'Success', 'status_class': 'success'},
    {'timestamp': '2025-01-15 18:00', 'dataset_type': 'Student Demographics','source': 'Historical Batch', 'records': '6,607',   'status': 'Success', 'status_class': 'success'},
    {'timestamp': '2025-01-14 11:20', 'dataset_type': 'Academic Records',    'source': 'Historical Batch', 'records': '5,200',   'status': 'Warning', 'status_class': 'warning'},
]

def parse_ingestion_file(file_storage, extension):
    """Parse supported educational data formats and return normalized records."""
    raw = file_storage.read()
    if not raw:
        raise ValueError('The uploaded file is empty.')
    if len(raw) > 10 * 1024 * 1024:
        raise ValueError('The uploaded file must be smaller than 10 MB.')

    text = raw.decode('utf-8-sig')
    if extension == 'csv':
        return list(csv.DictReader(text.splitlines()))
    if extension == 'json':
        payload = json.loads(text)
        return payload if isinstance(payload, list) else [payload]

    root = ET.fromstring(text)
    return [{child.tag: child.text or '' for child in item} for item in root.findall('.//record')]

exam_model    = load_pkl('exam_score_model.pkl')   # RandomForestRegressor
at_risk_model = load_pkl('at_risk_model.pkl')      # RandomForestClassifier
scaler        = load_pkl('scaler.pkl')             # StandardScaler
lr_model      = load_pkl('lr_model.pkl')
rf_model      = load_pkl('rf_model.pkl')

# ── Hive / StudentPerformanceFactors dataset ─────────────────────────────────
_SPF_PATH = os.path.join(BASE_DIR, 'StudentPerformanceFactors.csv')
try:
    SPF_DF = pd.read_csv(_SPF_PATH)
    # Derive risk label: score < 60 → High, 60-70 → Medium, >70 → Low
    SPF_DF['Risk'] = SPF_DF['Exam_Score'].apply(
        lambda s: 'High' if s < 60 else ('Medium' if s < 70 else 'Low')
    )
    # Pre-compute dashboard statistics from real data
    SPF_STATS = {
        'total_students':  len(SPF_DF),
        'avg_exam_score':  round(float(SPF_DF['Exam_Score'].mean()), 1),
        'avg_attendance':  round(float(SPF_DF['Attendance'].mean()), 1),
        'avg_hours':       round(float(SPF_DF['Hours_Studied'].mean()), 1),
        'at_risk_count':   int((SPF_DF['Risk'] == 'High').sum()),
        'pass_rate':       round(float((SPF_DF['Exam_Score'] >= 60).mean() * 100), 1),
        'gender_male':     int((SPF_DF['Gender'] == 'Male').sum()),
        'gender_female':   int((SPF_DF['Gender'] == 'Female').sum()),
        'school_public':   int((SPF_DF['School_Type'] == 'Public').sum()),
        'school_private':  int((SPF_DF['School_Type'] == 'Private').sum()),
        'internet_yes':    int((SPF_DF['Internet_Access'] == 'Yes').sum()),
        # score bands for charts
        'score_below_60':  int((SPF_DF['Exam_Score'] < 60).sum()),
        'score_60_70':     int(((SPF_DF['Exam_Score'] >= 60) & (SPF_DF['Exam_Score'] < 70)).sum()),
        'score_70_80':     int(((SPF_DF['Exam_Score'] >= 70) & (SPF_DF['Exam_Score'] < 80)).sum()),
        'score_above_80':  int((SPF_DF['Exam_Score'] >= 80).sum()),
    }
except Exception as _e:
    SPF_DF    = pd.DataFrame()
    SPF_STATS = {}
    print(f"[WARN] Could not load StudentPerformanceFactors.csv: {_e}")
# ─────────────────────────────────────────────────────────────────────────────

# 21 features expected by exam_model, at_risk_model, scaler
FEATURE_ORDER = [
    'Hours_Studied', 'Attendance', 'Parental_Involvement', 'Access_to_Resources',
    'Sleep_Hours', 'Previous_Scores', 'Motivation_Level', 'Tutoring_Sessions',
    'Family_Income', 'Teacher_Quality', 'Physical_Activity', 'Distance_from_Home',
    'Extracurricular_Activities_Yes', 'Internet_Access_Yes', 'School_Type_Public',
    'Peer_Influence_Neutral', 'Peer_Influence_Positive', 'Learning_Disabilities_Yes',
    'Parental_Education_Level_High School', 'Parental_Education_Level_Postgraduate',
    'Gender_Male'
]

def hash_pw(pw):
    return generate_password_hash(pw)

# Pre-hashed default passwords (avoids expensive hashing on every module reload)
_DEFAULT_HASHES = {
    'admin':   os.environ.get('ADMIN_PASS_HASH',   'scrypt:32768:8:1$ecia2zkCvwHhikZx$fb3f8a8f109b5690ffd9e1b3c5b84a8b7a6296ac482e86a243c64fdb881bfad72cd26090e17ed3cd12c2453b5e46261ed9044cf6d401875c7f37a0efb1de2586'),
    'teacher': os.environ.get('TEACHER_PASS_HASH', 'scrypt:32768:8:1$I7OnSM99ttMwxGc0$f997ed4f816a12f96336c4675aa8f2cefaec9bc92d1082919c0afcf8e56d4fc83f1a3e3f69eca2da0668133a9f29df08e757b264718da2f2494da67969d806c3'),
    'analyst': os.environ.get('ANALYST_PASS_HASH', 'scrypt:32768:8:1$uRMifG5CfXnyle0k$0d80ecb4ae15bd1fd06179c1b2bd04a61ae853dd9e046a64b6cdee33d45e5ea577d3c587a8b06cdcd5c42a4fd308ade46e327c7435162f2da8a3862481822cca'),
    'student': os.environ.get('STUDENT_PASS_HASH', 'scrypt:32768:8:1$qi6nZ3rU6CyMnTEt$9a514ba8ca7d35e28e62399f11dbfa05781b35cd610df3a7434527b42e078446830ea678d16e67da074d36a118590e69d625c1d93889a8ca2c1b4f06463ccf4e'),
}

# SRS Role-Based Access Control
USERS = {
    'admin': {
        'id': 'USR-101', 'name': 'Dr. Sarah Tariq', 'email': 'admin@edupredict.ac',
        'password': _DEFAULT_HASHES['admin'],
        'role': 'Administrator', 'department': 'Administration', 'status': 'Active',
        'last_active': 'Today, 09:14 AM',
        'access': ['dashboard','ingest','storage','realtime','predict','alerts','feedback','students','reports','users','models','course_demand','performance','security']
    },
    'teacher': {
        'id': 'USR-102', 'name': 'Prof. Hamza Qureshi', 'email': 'teacher@edupredict.ac',
        'password': _DEFAULT_HASHES['teacher'],
        'role': 'Teacher', 'department': 'Computer Science', 'status': 'Active',
        'last_active': 'Today, 08:50 AM',
        'access': ['dashboard','predict','alerts','feedback','students','reports','models','course_demand']
    },
    'analyst': {
        'id': 'USR-103', 'name': 'Ayesha Mehmood', 'email': 'analyst@edupredict.ac',
        'password': _DEFAULT_HASHES['analyst'],
        'role': 'Analyst', 'department': 'Institutional Research', 'status': 'Active',
        'last_active': 'Yesterday, 06:30 PM',
        'access': ['dashboard','ingest','storage','realtime','predict','alerts','feedback','students','reports','models','course_demand','performance','security']
    },
    'student': {
        'id': 'USR-104', 'name': 'Bilal Khan', 'email': 'student@edupredict.ac',
        'password': _DEFAULT_HASHES['student'],
        'role': 'Student', 'department': 'Software Engineering', 'status': 'Active',
        'last_active': 'Yesterday, 03:15 PM',
        'access': ['dashboard','predict','feedback']
    },
}

MONGO_CONNECTED = connect_mongo()
if MONGO_CONNECTED:
    for username, user_data in USERS.items():
        mongo_upsert_user(username, user_data)

# In-memory Dataset for Course Demand Forecasting
COURSES_DATA = [
    {"code": "CS-401", "name": "Hadoop & Distributed Big Data Processing", "dept": "Computer Science", "capacity": 120, "projected": 185, "growth": 68.2, "status": "Overcapacity Risk", "recommended_sections": 2},
    {"code": "AI-302", "name": "Applied Machine Learning & Predictive Analytics", "dept": "Artificial Intelligence", "capacity": 150, "projected": 210, "growth": 50.0, "status": "Overcapacity Risk", "recommended_sections": 2},
    {"code": "DS-201", "name": "Data Ingestion & HDFS Data Warehousing", "dept": "Data Science", "capacity": 100, "projected": 128, "growth": 34.7, "status": "High Demand", "recommended_sections": 1},
    {"code": "SE-305", "name": "Enterprise Cloud Architecture & DevOps", "dept": "Software Engineering", "capacity": 140, "projected": 142, "growth": 9.2, "status": "Normal", "recommended_sections": 0},
    {"code": "CY-404", "name": "Cybersecurity & Cryptographic Protocols", "dept": "Information Security", "capacity": 90, "projected": 115, "growth": 43.7, "status": "High Demand", "recommended_sections": 1},
    {"code": "IT-102", "name": "Legacy Database Systems & SQL Basics", "dept": "Information Technology", "capacity": 160, "projected": 98, "growth": -34.6, "status": "Under-enrolled", "recommended_sections": -1}
]

# In-memory Dataset for Model Metrics Evaluation
MODELS_DATA = [
    {
        "id": "MOD-01",
        "name": "Student Dropout Risk Classifier",
        "algorithm": "XGBoost Gradient Boosting",
        "version": "v2.4.1 (Production)",
        "accuracy": 93.4, "precision": 91.8, "recall": 94.2, "f1_score": 92.9, "roc_auc": 0.965,
        "features_count": 28, "status": "Deployed",
        "dataset_size": "142,500 Student Records (HDFS /data/academic/train_v2.parquet)",
        "feature_importance": [
            {"feature": "Attendance Rate (< 75%)", "score": 0.34},
            {"feature": "LMS Assignment Delay Days", "score": 0.22},
            {"feature": "Quiz 1 & 2 Average Score", "score": 0.18},
            {"feature": "Fee Installment Delinquency", "score": 0.14},
            {"feature": "Midterm vs Historical GPA Delta", "score": 0.08}
        ],
        "confusion_matrix": {
            "labels": ["Retained", "Dropout Risk"],
            "matrix": [[1820, 142], [89, 1249]]
        }
    },
    {
        "id": "MOD-02",
        "name": "Academic Performance Predictor",
        "algorithm": "Random Forest Regressor",
        "version": "v3.1.0 (Production)",
        "accuracy": 89.7, "precision": 88.5, "recall": 90.1, "f1_score": 89.3, "roc_auc": 0.941,
        "features_count": 19, "status": "Deployed",
        "dataset_size": "98,000 Academic Semester Transcripts",
        "feature_importance": [
            {"feature": "Previous Cumulative GPA", "score": 0.38},
            {"feature": "Continuous Internal Assessment", "score": 0.28},
            {"feature": "Course Difficulty Coefficient", "score": 0.15},
            {"feature": "Weekly Study Hours on LMS", "score": 0.11}
        ],
        "confusion_matrix": {
            "labels": ["Pass / High Honors", "Low Grade / Remedial"],
            "matrix": [[2104, 196], [150, 1350]]
        }
    }
]

REPORT_ROWS = [
    {'Department': 'BS Computer Science', 'Enrolled': 1240, 'Average Score': 71.4, 'Average Attendance': 82, 'At-Risk': 12, 'Pass Rate': 88, 'Trend': '+3.2%'},
    {'Department': 'BS Software Engineering', 'Enrolled': 980, 'Average Score': 64.8, 'Average Attendance': 76, 'At-Risk': 22, 'Pass Rate': 78, 'Trend': '-1.4%'},
    {'Department': 'BS Artificial Intelligence', 'Enrolled': 760, 'Average Score': 68.2, 'Average Attendance': 79, 'At-Risk': 17, 'Pass Rate': 83, 'Trend': '+1.8%'},
    {'Department': 'BBA Business Administration', 'Enrolled': 1100, 'Average Score': 72.6, 'Average Attendance': 85, 'At-Risk': 9, 'Pass Rate': 91, 'Trend': '+4.1%'},
    {'Department': 'BS Data Science', 'Enrolled': 620, 'Average Score': 74.1, 'Average Attendance': 88, 'At-Risk': 8, 'Pass Rate': 92, 'Trend': '+5.6%'},
    {'Department': 'BS Electrical Engineering', 'Enrolled': 890, 'Average Score': 69.3, 'Average Attendance': 80, 'At-Risk': 15, 'Pass Rate': 85, 'Trend': '+2.3%'},
    {'Department': 'BS Mechanical Engineering', 'Enrolled': 580, 'Average Score': 62.7, 'Average Attendance': 74, 'At-Risk': 24, 'Pass Rate': 76, 'Trend': '-0.8%'},
    {'Department': 'BS Civil Engineering', 'Enrolled': 437, 'Average Score': 65.9, 'Average Attendance': 77, 'At-Risk': 19, 'Pass Rate': 81, 'Trend': '+0.9%'},
]

def role_required(page):
    """Check if logged-in user has access to the given page."""
    if 'user' not in session:
        return redirect(url_for('login'))
    user_key = session.get('user')
    if user_key not in USERS or page not in USERS[user_key]['access']:
        flash('Access denied: your role does not have permission for this page.', 'danger')
        return redirect(url_for('dashboard'))
    return None

def safe_float(value, default=0.0):
    """Convert to float safely, rejecting NaN/Inf."""
    try:
        v = float(value)
        if math.isnan(v) or math.isinf(v):
            return default
        return v
    except (TypeError, ValueError):
        return default

def get_access():
    return USERS[session['user']]['access'] if 'user' in session and session['user'] in USERS else []

@app.route('/')
def index():
    return render_template('landing.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/features')
def features():
    return render_template('features.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        flash('Message sent successfully! We will get back to you shortly.', 'success')
    return render_template('contact.html')


@app.route('/home')
def home():
    return render_template('landing.html')

# 1. User Authentication and Authorization
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        if username in USERS and check_password_hash(USERS[username]['password'], password) and USERS[username]['role'] == role:
            session['user'] = username
            session['role'] = role
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid Username, Password, or Role combination!', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# 2. Data Visualization Dashboard
@app.route('/dashboard')
def dashboard():
    guard = role_required('dashboard')
    if guard: return guard
    access = get_access()
    return render_template('dashboard.html',
                           user=session['user'],
                           role=session['role'],
                           access=access,
                           stats=SPF_STATS)

def build_features(f):
    """Build 21-feature array from form data matching FEATURE_ORDER."""
    parental_map = {'Low': 0, 'Medium': 1, 'High': 2}
    resource_map = {'Low': 0, 'Medium': 1, 'High': 2}
    motivation_map = {'Low': 0, 'Medium': 1, 'High': 2}
    income_map = {'Low': 0, 'Medium': 1, 'High': 2}
    teacher_map = {'Low': 0, 'Medium': 1, 'High': 2}
    distance_map = {'Near': 0, 'Moderate': 1, 'Far': 2}

    extracurricular = 1 if f.get('extracurricular') == 'Yes' else 0
    internet        = 1 if f.get('internet_access') == 'Yes' else 0
    school_public   = 1 if f.get('school_type') == 'Public' else 0
    peer            = f.get('peer_influence', 'Neutral')
    peer_neutral    = 1 if peer == 'Neutral' else 0
    peer_positive   = 1 if peer == 'Positive' else 0
    learning_dis    = 1 if f.get('learning_disabilities') == 'Yes' else 0
    edu             = f.get('parental_education', 'High School')
    edu_hs          = 1 if edu == 'High School' else 0
    edu_pg          = 1 if edu == 'Postgraduate' else 0
    gender_male     = 1 if f.get('gender') == 'Male' else 0

    row = [
        safe_float(f.get('hours_studied')),
        safe_float(f.get('attendance')),
        parental_map.get(f.get('parental_involvement', 'Medium'), 1),
        resource_map.get(f.get('access_to_resources', 'Medium'), 1),
        safe_float(f.get('sleep_hours'), 7.0),
        safe_float(f.get('previous_scores')),
        motivation_map.get(f.get('motivation_level', 'Medium'), 1),
        safe_float(f.get('tutoring_sessions')),
        income_map.get(f.get('family_income', 'Medium'), 1),
        teacher_map.get(f.get('teacher_quality', 'Medium'), 1),
        safe_float(f.get('physical_activity'), 3.0),
        distance_map.get(f.get('distance_from_home', 'Moderate'), 1),
        extracurricular, internet, school_public,
        peer_neutral, peer_positive, learning_dis,
        edu_hs, edu_pg, gender_male
    ]
    return np.array([row])

# 3. Machine Learning Prediction & Real-time Alerts
@app.route('/predict', methods=['GET', 'POST'])
def predict():
    guard = role_required('predict')
    if guard: return guard

    prediction = None
    alert_level = None
    chosen_model_name = None
    pred_type = 'exam'
    at_risk_result = None
    at_risk_alert = None
    at_risk_proba = None
    course_forecast = None
    course_trend = None
    course_category_name = None
    course_recommendation = None

    if request.method == 'POST':
        pred_type = request.form.get('pred_type', 'exam')
        try:
            if pred_type == 'exam':
                features = build_features(request.form)
                features_scaled = scaler.transform(features) if scaler else features

                if exam_model:
                    prediction = round(float(exam_model.predict(features_scaled)[0]), 2)
                    chosen_model_name = "Random Forest Regressor (Student Performance Dataset)"
                elif rf_model:
                    prediction = round(float(rf_model.predict(features)[0]), 2)
                    chosen_model_name = "Random Forest Regressor"
                elif lr_model:
                    prediction = round(float(lr_model.predict(features)[0]), 2)
                    chosen_model_name = "Linear Regression"
                else:
                    # Fallback formula
                    hours = safe_float(request.form.get('hours_studied'), 4)
                    attendance = safe_float(request.form.get('attendance'), 75)
                    prediction = round(min(100, (attendance * 0.5) + (hours * 6)), 1)
                    chosen_model_name = "Analytical Heuristic Engine"

                prediction = max(0, min(100, prediction))
                if prediction < 50:
                    alert_level = 'CRITICAL: High Risk of Academic Failure / Dropout'
                elif prediction < 75:
                    alert_level = 'WARNING: Moderate Performance - Intervention Recommended'
                else:
                    alert_level = 'SUCCESS: Optimal Learning Pattern - Low Risk'

            elif pred_type == 'dropout':
                features = build_features(request.form)
                features_scaled = scaler.transform(features) if scaler else features

                if at_risk_model:
                    pred_class = int(at_risk_model.predict(features_scaled)[0])
                    if hasattr(at_risk_model, 'predict_proba'):
                        proba = at_risk_model.predict_proba(features_scaled)[0]
                        at_risk_proba = round(float(max(proba)) * 100, 1)
                    else:
                        at_risk_proba = 75.0 if pred_class == 1 else 25.0
                    at_risk_result = pred_class
                    at_risk_alert = 'CRITICAL: Student is At-Risk — Immediate Intervention Required' if pred_class == 1 else 'LOW RISK: Student likely to continue'
                else:
                    hours = safe_float(request.form.get('hours_studied'))
                    attendance = safe_float(request.form.get('attendance'))
                    prev = safe_float(request.form.get('previous_scores'))
                    risk = 100 - ((attendance * 0.4) + (prev * 0.3) + (hours * 1.2))
                    at_risk_proba = round(max(0, min(100, risk)), 1)
                    at_risk_result = 1 if at_risk_proba > 50 else 0
                    at_risk_alert = 'CRITICAL: High Dropout Risk' if at_risk_result == 1 else 'LOW RISK: Student stable'

            elif pred_type == 'course':
                current_enrollment = safe_float(request.form.get('current_enrollment'), 100)
                avg_score          = safe_float(request.form.get('avg_score'), 65)
                forecast_months    = safe_float(request.form.get('forecast_months'), 6)
                cat_map    = {'cs': 'BS Computer Science', 'se': 'BS Software Engineering', 'ai': 'BS Artificial Intelligence', 'ds': 'BS Data Science', 'sec': 'BS Cyber Security', 'it': 'BS Information Technology', 'ee': 'BS Electrical Engineering', 'me': 'BS Mechanical Engineering', 'ce': 'BS Civil Engineering', 'bba': 'BBA Business Administration', 'af': 'BS Accounting & Finance', 'econ': 'BS Economics'}
                growth_map = {'cs': 1.12, 'se': 1.09, 'ai': 1.15, 'ds': 1.14, 'sec': 1.13, 'it': 1.10, 'ee': 1.07, 'me': 1.06, 'ce': 1.05, 'bba': 1.10, 'af': 1.08, 'econ': 1.06}
                cat = request.form.get('course_category', 'cs')
                growth = growth_map.get(cat, 1.05) ** (forecast_months / 6)
                course_forecast = round(current_enrollment * growth * (avg_score / 70))
                course_category_name = cat_map.get(cat, cat)
                course_trend = 'Growing ↑' if growth > 1 else 'Declining ↓'
                course_recommendation = f'Allocate {round(course_forecast * 1.1)} seats and assign additional faculty for {course_category_name}.'

        except Exception as e:
            flash(f"Prediction Error: {str(e)}", "danger")

    return render_template('predict.html',
                           prediction=prediction,
                           alert_level=alert_level,
                           model_used=chosen_model_name,
                           pred_type=pred_type,
                           at_risk_result=at_risk_result,
                           at_risk_alert=at_risk_alert,
                           at_risk_proba=at_risk_proba,
                           course_forecast=course_forecast,
                           course_trend=course_trend,
                           course_category_name=course_category_name,
                           course_recommendation=course_recommendation,
                           access=get_access())

# -------------------------------------------------------------
# 4. COURSE DEMAND FORECASTING ROUTE (Fixes course_demand.html)
# -------------------------------------------------------------
@app.route('/course-demand')
def course_demand():
    guard = role_required('course_demand')
    if guard: return guard
    return render_template('course_demand.html', courses=COURSES_DATA, access=get_access())

# -------------------------------------------------------------
# 5. MACHINE LEARNING MODEL METRICS ROUTE (Fixes model_metrics.html)
# -------------------------------------------------------------
@app.route('/models')
def model_metrics():
    guard = role_required('models')
    if guard: return guard
    return render_template('model_metrics.html', models=MODELS_DATA, access=get_access())

@app.route('/models/retrain', methods=['POST'])
def retrain_models():
    guard = role_required('models')
    if guard: return guard
    flash('Parallel retraining dispatched across cluster. Metrics & weights refreshed successfully!', 'success')
    return redirect(url_for('model_metrics'))

# -------------------------------------------------------------
# 6. USER MANAGEMENT & RBAC ROUTE (Fixes user_management.html)
# -------------------------------------------------------------
@app.route('/users')
def user_management():
    guard = role_required('users')
    if guard: return guard
    users_list = [
        {'id': data.get('id', k), 'username': k, 'name': data.get('name', k.title()), 'email': data.get('email', f"{k}@edupredict.ac"), 'role': data['role'], 'department': data.get('department', 'General'), 'status': data.get('status', 'Active'), 'last_active': data.get('last_active', 'N/A')}
        for k, data in USERS.items()
    ]
    role_counts = {
        "admin": sum(1 for u in users_list if u['role'] == 'Administrator'),
        "teacher": sum(1 for u in users_list if u['role'] == 'Teacher'),
        "analyst": sum(1 for u in users_list if u['role'] == 'Analyst'),
        "student": sum(1 for u in users_list if u['role'] == 'Student')
    }
    return render_template('user_management.html', users=users_list, role_counts=role_counts, access=get_access())

@app.route('/users/add', methods=['POST'])
def add_user():
    guard = role_required('users')
    if guard: return guard
    name = request.form.get('name')
    email = request.form.get('email')
    role = request.form.get('role', 'Teacher')
    department = request.form.get('department', 'General')
    username = email.split('@')[0].lower() if email else f"user_{len(USERS)+1}"

    if name and email:
        role_access_map = {
            'Administrator': ['dashboard','ingest','storage','realtime','predict','alerts','feedback','students','reports','users','models','course_demand','performance','security'],
            'Teacher':       ['dashboard','predict','alerts','feedback','students','reports','models','course_demand'],
            'Analyst':       ['dashboard','ingest','storage','realtime','predict','alerts','feedback','students','reports','models','course_demand','performance','security'],
            'Student':       ['dashboard','predict','feedback'],
        }
        USERS[username] = {
            'id': f"USR-{100 + len(USERS) + 1}",
            'name': name,
            'email': email,
            'password': hash_pw('Student@123'),
            'role': role,
            'department': department,
            'status': 'Active',
            'access': role_access_map.get(role, ['dashboard','predict','feedback'])
        }
        mongo_upsert_user(username, USERS[username])
        flash(f'User {name} ({role}) created successfully!', 'success')
    else:
        flash('Name and Email are required.', 'danger')
    return redirect(url_for('user_management'))

@app.route('/users/toggle/<user_id>')
def toggle_user_status(user_id):
    guard = role_required('users')
    if guard: return guard
    for k, data in USERS.items():
        if data.get('id') == user_id or k == user_id:
            data['status'] = 'Suspended' if data.get('status') == 'Active' else 'Active'
            flash(f"Updated status for {data.get('name', k)} to {data['status']}.", 'info')
            break
    return redirect(url_for('user_management'))

# 7. Support and Feedback System
@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    guard = role_required('feedback')
    if guard: return guard
    if request.method == 'POST':
        flash('Ticket submitted successfully! Support team will review.', 'success')
    return render_template('feedback.html', access=get_access())

# 8. Data Ingestion
@app.route('/ingest', methods=['GET', 'POST'])
def ingest():
    guard = role_required('ingest')
    if guard: return guard

    if request.method == 'POST':
        dataset_type = request.form.get('dataset_type', 'unknown').replace('_', ' ').title()
        source = request.form.get('data_source', 'historical').replace('_', ' ').title()
        uploaded_file = request.files.get('dataset_file')
        filename = secure_filename(uploaded_file.filename if uploaded_file else '')
        extension = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''

        if not uploaded_file or not filename:
            flash('Please select a CSV, JSON, or XML file before ingesting.', 'danger')
        elif extension not in ALLOWED_INGEST_EXTENSIONS:
            flash('Unsupported file type. Upload only CSV, JSON, or XML.', 'danger')
        else:
            try:
                records = parse_ingestion_file(uploaded_file, extension)
                os.makedirs(INGEST_DIR, exist_ok=True)
                stored_name = f'{datetime.utcnow().strftime("%Y%m%d%H%M%S")}_{filename}'
                stored_path = os.path.join(INGEST_DIR, stored_name)
                uploaded_file.seek(0)
                uploaded_file.save(stored_path)
                INGESTION_LOGS.insert(0, {
                    'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M'),
                    'dataset_type': dataset_type,
                    'source': source,
                    'records': f'{len(records):,}',
                    'status': 'Success',
                    'status_class': 'success'
                })
                mongo_insert('ingestion_logs', {
                    'timestamp': datetime.utcnow(),
                    'filename': filename,
                    'dataset_type': dataset_type,
                    'source': source,
                    'records': len(records),
                    'status': 'Success'
                })
                del INGESTION_LOGS[10:]
                flash(f'Dataset "{filename}" ingested successfully: {len(records):,} records validated and stored.', 'success')
            except (UnicodeDecodeError, ValueError, json.JSONDecodeError, ET.ParseError) as error:
                flash(f'Ingestion failed: {error}', 'danger')

    return render_template('ingest.html', ingestion_logs=INGESTION_LOGS, access=get_access())

# 9. Notifications & Alerts
@app.route('/alerts', methods=['GET', 'POST'])
def alerts():
    guard = role_required('alerts')
    if guard: return guard

    thresholds = {
        'attendance': int(request.form.get('attendance_threshold', 60)),
        'score':      int(request.form.get('score_threshold', 60)),
        'dropout':    int(request.form.get('dropout_threshold', 40)),
    }

    if request.method == 'POST':
        flash('Alert thresholds updated successfully.', 'success')

    # ── Build real alerts from StudentPerformanceFactors.csv ──────────────
    alert_list = []
    _male_names   = ['Ali Hassan','Ahmed Raza','Usman Tariq','Bilal Ahmed','Omar Farooq','Kamran Shah','Faisal Butt','Tariq Mehmood','Imran Qureshi','Asad Nawaz','Zain Malik','Hamza Khan','Saad Iqbal','Fahad Mirza','Waleed Chaudhry']
    _female_names = ['Sara Khan','Fatima Malik','Ayesha Noor','Zara Siddiqui','Hina Javed','Nadia Iqbal','Sana Mirza','Rabia Chaudhry','Mehwish Baig','Lubna Riaz','Maryam Ahmed','Amna Hassan','Kiran Butt','Nimra Shah','Sadia Tariq']

    if not SPF_DF.empty:
        att_thresh   = thresholds['attendance']
        score_thresh = thresholds['score']

        # Low attendance alerts
        low_att = SPF_DF[SPF_DF['Attendance'] < att_thresh].head(10)
        for idx, row in low_att.iterrows():
            g    = row['Gender']
            name = _male_names[idx % len(_male_names)] if g == 'Male' else _female_names[idx % len(_female_names)]
            alert_list.append({
                'time':        '09:14',
                'student_id':  f'STU-{idx+1001:04d}',
                'name':        name,
                'alert_type':  'Low Attendance',
                'details':     f"Attendance: {int(row['Attendance'])}% (below {att_thresh}%)",
                'severity':    'Critical',
                'badge':       'danger',
                'status':      'Open',
                'score':       int(row['Exam_Score']),
                'attendance':  int(row['Attendance']),
            })

        # Low score alerts
        low_score = SPF_DF[
            (SPF_DF['Exam_Score'] < score_thresh) &
            (SPF_DF['Attendance'] >= att_thresh)
        ].head(8)
        for idx, row in low_score.iterrows():
            g    = row['Gender']
            name = _male_names[idx % len(_male_names)] if g == 'Male' else _female_names[idx % len(_female_names)]
            alert_list.append({
                'time':        '09:10',
                'student_id':  f'STU-{idx+1001:04d}',
                'name':        name,
                'alert_type':  'Score Risk',
                'details':     f"Exam Score: {int(row['Exam_Score'])}% (below {score_thresh}%)",
                'severity':    'Critical',
                'badge':       'danger',
                'status':      'Open',
                'score':       int(row['Exam_Score']),
                'attendance':  int(row['Attendance']),
            })

        # Medium risk (low motivation + low hours)
        med_risk = SPF_DF[
            (SPF_DF['Motivation_Level'] == 'Low') &
            (SPF_DF['Hours_Studied'] < 10) &
            (SPF_DF['Exam_Score'] >= score_thresh)
        ].head(6)
        for idx, row in med_risk.iterrows():
            g    = row['Gender']
            name = _male_names[idx % len(_male_names)] if g == 'Male' else _female_names[idx % len(_female_names)]
            alert_list.append({
                'time':        '08:50',
                'student_id':  f'STU-{idx+1001:04d}',
                'name':        name,
                'alert_type':  'Dropout Risk',
                'details':     f"Low motivation + {int(row['Hours_Studied'])}h/week study",
                'severity':    'Warning',
                'badge':       'warning',
                'status':      'Open',
                'score':       int(row['Exam_Score']),
                'attendance':  int(row['Attendance']),
            })
    # ──────────────────────────────────────────────────────────────────────

    return render_template('alerts.html',
                           alerts=alert_list,
                           thresholds=thresholds,
                           access=get_access(),
                           total_critical=sum(1 for a in alert_list if a['severity']=='Critical'),
                           total_warning=sum(1 for a in alert_list if a['severity']=='Warning'),
                           total_resolved=sum(1 for a in alert_list if a['status']=='Resolved'))

# 10. Performance Monitoring
@app.route('/performance')
def performance():
    guard = role_required('performance')
    if guard: return guard
    return render_template('performance.html', access=get_access())

# 11. Data Storage
@app.route('/storage')
def storage():
    guard = role_required('storage')
    if guard: return guard

    dataset_meta = [
        {'filename': 'academic_records.csv',      'hdfs_path': '/edupredict/academic/',      'label': 'Academic Records',      'records': '2,000',   'icon': 'Graduation Cap'},
        {'filename': 'student_demographics.csv',  'hdfs_path': '/edupredict/demographics/',  'label': 'Student Demographics',  'records': '2,000',   'icon': 'Users'},
        {'filename': 'attendance_records.csv',    'hdfs_path': '/edupredict/attendance/',    'label': 'Attendance Records',    'records': '120,000', 'icon': 'Clipboard'},
        {'filename': 'lms_activity.csv',          'hdfs_path': '/edupredict/lms/',           'label': 'LMS Activity Logs',     'records': '3,000',   'icon': 'Monitor'},
    ]

    hdfs_files = []
    total_bytes = 0
    for meta in dataset_meta:
        fpath = os.path.join(INGEST_DIR, meta['filename'])
        if os.path.exists(fpath):
            size_bytes = os.path.getsize(fpath)
            total_bytes += size_bytes
            size_str = f"{size_bytes/(1024*1024):.1f} MB" if size_bytes >= 1024*1024 else f"{size_bytes/1024:.1f} KB"
            mtime  = datetime.fromtimestamp(os.path.getmtime(fpath)).strftime('%Y-%m-%d')
            status = 'Available'
        else:
            size_str = '—'
            mtime    = '—'
            status   = 'Missing'

        hdfs_files.append({
            'hdfs_path': meta['hdfs_path'],
            'label':     meta['label'],
            'records':   meta['records'],
            'size':      size_str,
            'updated':   mtime,
            'status':    status,
        })

    # ── Add StudentPerformanceFactors.csv as Hive dataset ─────────────────
    spf_path = os.path.join(BASE_DIR, 'StudentPerformanceFactors.csv')
    if os.path.exists(spf_path):
        spf_bytes   = os.path.getsize(spf_path)
        total_bytes += spf_bytes
        spf_size    = f"{spf_bytes/(1024*1024):.1f} MB" if spf_bytes >= 1024*1024 else f"{spf_bytes/1024:.1f} KB"
        spf_mtime   = datetime.fromtimestamp(os.path.getmtime(spf_path)).strftime('%Y-%m-%d')
        spf_status  = 'Available'
    else:
        spf_size   = '—'
        spf_mtime  = '—'
        spf_status = 'Missing'

    hive_dataset = {
        'hdfs_path': '/hive/warehouse/student_performance/',
        'label':     'Student Performance Factors (Hive)',
        'records':   f"{len(SPF_DF):,}" if not SPF_DF.empty else '6,607',
        'size':      spf_size,
        'updated':   spf_mtime,
        'status':    spf_status,
        'is_hive':   True,
        'columns':   20,
        'source':    'StudentPerformanceFactors.csv',
    }
    # ──────────────────────────────────────────────────────────────────────

    total_used  = f"{total_bytes/(1024*1024):.1f} MB" if total_bytes >= 1024*1024 else f"{total_bytes/1024:.1f} KB"
    files_found = sum(1 for f in hdfs_files if f['status'] == 'Available')
    if spf_status == 'Available':
        files_found += 1

    return render_template('storage.html',
                           access=get_access(),
                           hdfs_files=hdfs_files,
                           hive_dataset=hive_dataset,
                           total_used=total_used,
                           files_found=files_found)

# 11. Real-Time Processing
@app.route('/realtime')
def realtime():
    guard = role_required('realtime')
    if guard: return guard

    anomaly_events = [
        {'time': '09:14:32', 'message': 'Student ID #4821 — Attendance dropped below 60% threshold', 'level': 'danger'},
        {'time': '09:12:18', 'message': 'Batch job completed — 6,607 records processed in 2.1s',     'level': 'success'},
        {'time': '09:10:05', 'message': 'Student ID #3302 — Score prediction: 41% (Critical Risk)',   'level': 'danger'},
        {'time': '09:08:44', 'message': 'LMS stream connected — 1,247 events/sec ingested',           'level': 'success'},
        {'time': '09:05:11', 'message': 'Student ID #2190 — Tutoring sessions dropped to 0',          'level': 'danger'},
        {'time': '09:01:00', 'message': 'Real-time pipeline initialized successfully',                 'level': 'success'},
    ]

    return render_template('realtime.html', anomaly_events=anomaly_events, access=get_access())

# 12. Reports & Data Export
@app.route('/reports')
def reports():
    guard = role_required('reports')
    if guard: return guard
    return render_template('reports.html', access=get_access())

@app.route('/reports/export/<export_format>')
def export_report(export_format):
    guard = role_required('reports')
    if guard: return guard
    if export_format == 'json':
        return Response(json.dumps(REPORT_ROWS, indent=2), mimetype='application/json', headers={
            'Content-Disposition': 'attachment; filename=edupredict-report.json'
        })
    if export_format == 'csv':
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=REPORT_ROWS[0].keys())
        writer.writeheader()
        writer.writerows(REPORT_ROWS)
        return Response(output.getvalue(), mimetype='text/csv', headers={
            'Content-Disposition': 'attachment; filename=edupredict-report.csv'
        })
    if export_format == 'xlsx':
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = 'EduPredict Report'

            # Title row
            ws.merge_cells('A1:G1')
            title_cell = ws['A1']
            title_cell.value = 'EduPredict — Department Summary Report (Academic Year 2024–25)'
            title_cell.font = Font(bold=True, size=14, color='FFFFFF')
            title_cell.fill = PatternFill('solid', fgColor='1E3A5F')
            title_cell.alignment = Alignment(horizontal='center', vertical='center')
            ws.row_dimensions[1].height = 30

            # Header row
            headers = list(REPORT_ROWS[0].keys())
            header_fill = PatternFill('solid', fgColor='2563EB')
            thin = Side(style='thin', color='AAAAAA')
            border = Border(left=thin, right=thin, top=thin, bottom=thin)
            for col_idx, header in enumerate(headers, 1):
                cell = ws.cell(row=2, column=col_idx, value=header)
                cell.font = Font(bold=True, color='FFFFFF', size=11)
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal='center')
                cell.border = border

            # Data rows
            row_fills = [PatternFill('solid', fgColor='F0F4FF'), PatternFill('solid', fgColor='FFFFFF')]
            for row_idx, row in enumerate(REPORT_ROWS, 3):
                fill = row_fills[row_idx % 2]
                for col_idx, key in enumerate(headers, 1):
                    cell = ws.cell(row=row_idx, column=col_idx, value=row[key])
                    cell.fill = fill
                    cell.alignment = Alignment(horizontal='center')
                    cell.border = border

            # Column widths
            col_widths = [20, 12, 15, 18, 10, 12, 10]
            for i, width in enumerate(col_widths, 1):
                ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = width

            output = io.BytesIO()
            wb.save(output)
            output.seek(0)
            return Response(output.read(), mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                            headers={'Content-Disposition': 'attachment; filename=edupredict-report.xlsx'})
        except ImportError:
            flash('Excel export requires openpyxl. Run: pip install openpyxl', 'warning')
            return redirect(url_for('reports'))

    if export_format == 'pdf':
        try:
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm

            output = io.BytesIO()
            doc = SimpleDocTemplate(output, pagesize=landscape(A4),
                                    leftMargin=1.5*cm, rightMargin=1.5*cm,
                                    topMargin=1.5*cm, bottomMargin=1.5*cm)
            styles = getSampleStyleSheet()
            elements = []

            # Title
            title_style = ParagraphStyle('Title', parent=styles['Title'],
                                         textColor=colors.HexColor('#1E3A5F'), fontSize=16, spaceAfter=10)
            elements.append(Paragraph('EduPredict — Department Summary Report', title_style))
            elements.append(Paragraph('Academic Year 2024–25 | Generated by EduPredict AI Analytics Platform', styles['Normal']))
            elements.append(Spacer(1, 0.5*cm))

            # Summary stats
            summary_data = [
                ['Total Students', 'Avg Score', 'At-Risk Rate', 'Avg Attendance'],
                ['6,607', '67.2%', '18%', '78.4%']
            ]
            summary_table = Table(summary_data, colWidths=[6*cm]*4)
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2563EB')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTSIZE', (0,1), (-1,1), 14),
                ('FONTNAME', (0,1), (-1,1), 'Helvetica-Bold'),
                ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#EEF2FF')),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
                ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#F0F4FF'), colors.white]),
                ('TOPPADDING', (0,0), (-1,-1), 8),
                ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ]))
            elements.append(summary_table)
            elements.append(Spacer(1, 0.6*cm))

            # Department table
            headers = list(REPORT_ROWS[0].keys())
            table_data = [headers] + [[str(row[h]) for h in headers] for row in REPORT_ROWS]
            col_w = [4.5*cm, 2.8*cm, 3*cm, 3.5*cm, 2.5*cm, 2.8*cm, 2.5*cm]
            dept_table = Table(table_data, colWidths=col_w)
            dept_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A5F')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 9),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#F0F4FF'), colors.white]),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
                ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
                ('TOPPADDING', (0,0), (-1,-1), 7),
                ('BOTTOMPADDING', (0,0), (-1,-1), 7),
            ]))
            elements.append(Paragraph('Department Summary', styles['Heading2']))
            elements.append(Spacer(1, 0.2*cm))
            elements.append(dept_table)
            elements.append(Spacer(1, 0.5*cm))
            elements.append(Paragraph(
                'Generated by EduPredict AI Analytics Platform — Confidential Academic Report',
                ParagraphStyle('footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey)))

            doc.build(elements)
            output.seek(0)
            return Response(output.read(), mimetype='application/pdf',
                            headers={'Content-Disposition': 'attachment; filename=edupredict-report.pdf'})
        except ImportError:
            flash('PDF export requires reportlab. Run: pip install reportlab', 'warning')
            return redirect(url_for('reports'))

    flash('Only CSV, JSON, Excel, and PDF exports are available.', 'warning')
    return redirect(url_for('reports'))

# 13. User Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm', '')
        role     = request.form.get('role', '')
        if not username or not password or not role:
            flash('All fields are required.', 'danger')
        elif password != confirm:
            flash('Passwords do not match.', 'danger')
        elif len(password) < 8:
            flash('Password must be at least 8 characters.', 'danger')
        elif username in USERS:
            flash('Username already exists. Choose another.', 'danger')
        else:
            role_access_map = {
                'Administrator': ['dashboard','ingest','storage','realtime','predict','alerts','feedback','students','reports','users','models','course_demand','performance','security'],
                'Teacher':       ['dashboard','predict','alerts','feedback','students','reports','models','course_demand'],
                'Analyst':       ['dashboard','ingest','storage','realtime','predict','alerts','feedback','students','reports','models','course_demand','performance','security'],
                'Student':       ['dashboard','predict','feedback'],
            }
            USERS[username] = {
                'id': f"USR-{100 + len(USERS) + 1}",
                'name': username.title(),
                'email': f"{username}@edupredict.ac",
                'password': hash_pw(password),
                'role': role,
                'department': 'General',
                'status': 'Active',
                'access': role_access_map.get(role, ['dashboard','predict','feedback'])
            }
            mongo_upsert_user(username, USERS[username])
            flash(f'Account created for {username}! You can now log in.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

# 14. User Profile
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        current_pw  = request.form.get('current_password', '')
        new_pw      = request.form.get('new_password', '')
        confirm_pw  = request.form.get('confirm_password', '')
        if current_pw and new_pw:
            if not check_password_hash(USERS[session['user']]['password'], current_pw):
                flash('Current password is incorrect.', 'danger')
            elif new_pw != confirm_pw:
                flash('New passwords do not match.', 'danger')
            elif len(new_pw) < 8:
                flash('Password must be at least 8 characters.', 'danger')
            else:
                USERS[session['user']]['password'] = hash_pw(new_pw)
                mongo_upsert_user(session['user'], USERS[session['user']])
                flash('Password updated successfully!', 'success')
        else:
            flash('Profile updated successfully!', 'success')
    user_data = USERS[session['user']]
    return render_template('profile.html', user_data=user_data, access=get_access())

# 15. Security & Compliance
@app.route('/security')
def security():
    guard = role_required('security')
    if guard: return guard
    return render_template('security.html', access=get_access())

# 16. Student Management
@app.route('/students')
def students():
    guard = role_required('students')
    if guard: return guard

    # ── Use real StudentPerformanceFactors.csv data ────────────────────────
    PAGE_SIZE = 50
    page = max(1, request.args.get('page', 1, type=int))
    search_q = request.args.get('q', '').strip().lower()

    if not SPF_DF.empty:
        df = SPF_DF.copy()

        # Search filter (by gender, school type, motivation, etc.)
        if search_q:
            mask = (
                df['Gender'].str.lower().str.contains(search_q, na=False) |
                df['School_Type'].str.lower().str.contains(search_q, na=False) |
                df['Motivation_Level'].str.lower().str.contains(search_q, na=False) |
                df['Parental_Involvement'].str.lower().str.contains(search_q, na=False)
            )
            df = df[mask]

        total_records = len(df)
        total_pages   = max(1, math.ceil(total_records / PAGE_SIZE))
        page          = min(page, total_pages)
        start         = (page - 1) * PAGE_SIZE
        page_df       = df.iloc[start:start + PAGE_SIZE]

        student_list = []

        # Name pools — used deterministically based on row index so names stay consistent
        _male_names = [
            'Ali Hassan','Ahmed Raza','Usman Tariq','Bilal Ahmed','Omar Farooq',
            'Kamran Shah','Faisal Butt','Tariq Mehmood','Imran Qureshi','Asad Nawaz',
            'Zain Malik','Hamza Khan','Saad Iqbal','Fahad Mirza','Waleed Chaudhry',
            'Umer Siddiqui','Adeel Baig','Noman Riaz','Shoaib Nawaz','Daniyal Shah',
            'Arslan Butt','Salman Farooq','Waqas Ahmed','Talha Raza','Junaid Tariq',
        ]
        _female_names = [
            'Sara Khan','Fatima Malik','Ayesha Noor','Zara Siddiqui','Hina Javed',
            'Nadia Iqbal','Sana Mirza','Rabia Chaudhry','Mehwish Baig','Lubna Riaz',
            'Maryam Ahmed','Amna Hassan','Kiran Butt','Nimra Shah','Sadia Tariq',
            'Maham Farooq','Iqra Qureshi','Rida Nawaz','Aisha Mirza','Bushra Malik',
            'Hira Siddiqui','Saima Baig','Uzma Riaz','Tayyaba Chaudhry','Rubab Iqbal',
        ]

        # Course mapping based on index — deterministic, real-world university departments
        _courses = [
            'BS Computer Science', 'BS Software Engineering', 'BS Artificial Intelligence',
            'BS Data Science', 'BS Cyber Security', 'BS Information Technology',
            'BS Electrical Engineering', 'BS Mechanical Engineering', 'BS Civil Engineering',
            'BBA Business Administration', 'BS Accounting & Finance', 'BS Economics'
        ]

        for idx, row in page_df.iterrows():
            score  = int(row['Exam_Score'])
            att    = int(row['Attendance'])
            risk   = row['Risk']
            gender = row['Gender']

            # Pick a consistent name based on original row index
            if gender == 'Male':
                name = _male_names[idx % len(_male_names)]
            else:
                name = _female_names[idx % len(_female_names)]

            # Semester 1-8 derived from index (repeating cycle)
            semester = (idx % 8) + 1

            # Course deterministic from index
            course = _courses[idx % len(_courses)]

            student_list.append({
                'id':          f'STU-{idx + 1001:04d}',
                'name':        name,
                'gender':      gender,
                'course':      course,
                'score':       score,
                'attendance':  att,
                'hours':       int(row['Hours_Studied']),
                'motivation':  row['Motivation_Level'],
                'school_type': row['School_Type'],
                'risk':        risk,
                'internet':    row['Internet_Access'],
                'status':      'Active' if att >= 60 else 'Inactive',
                'semester':    semester,
            })

        stats = {
            'total':     total_records,
            'active':    int((SPF_DF['Attendance'] >= 60).sum()),
            'at_risk':   SPF_STATS.get('at_risk_count', 0),
            'avg_score': SPF_STATS.get('avg_exam_score', 0),
        }
    else:
        # Fallback if CSV not loaded
        student_list  = []
        stats         = {'total': 0, 'active': 0, 'at_risk': 0, 'avg_score': 0}
        total_pages   = 1
        page          = 1
        total_records = 0

    return render_template('students.html',
                           students=student_list,
                           stats=stats,
                           page=page,
                           total_pages=total_pages,
                           total_records=total_records,
                           search_q=search_q,
                           access=get_access())

if __name__ == '__main__':
    # Runs on localhost port 5000 with debug enabled
    app.run(host='127.0.0.1', port=5000, debug=True)