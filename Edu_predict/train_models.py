"""
EduPredict — Model Training Script
Trains all 5 models used by app.py on synthetic Student Performance Dataset.

Models produced:
  models/exam_score_model.pkl  — RandomForestRegressor  (21 features → exam score)
  models/at_risk_model.pkl     — RandomForestClassifier (21 features → dropout risk)
  models/scaler.pkl            — StandardScaler         (fitted on 21 features)
  models/lr_model.pkl          — LinearRegression       (21 features → exam score)
  models/rf_model.pkl          — RandomForestRegressor  (21 features → exam score, backup)

Feature order (must match FEATURE_ORDER in app.py):
  Hours_Studied, Attendance, Parental_Involvement, Access_to_Resources,
  Sleep_Hours, Previous_Scores, Motivation_Level, Tutoring_Sessions,
  Family_Income, Teacher_Quality, Physical_Activity, Distance_from_Home,
  Extracurricular_Activities_Yes, Internet_Access_Yes, School_Type_Public,
  Peer_Influence_Neutral, Peer_Influence_Positive, Learning_Disabilities_Yes,
  Parental_Education_Level_High School, Parental_Education_Level_Postgraduate,
  Gender_Male
"""

import os
import pickle
import numpy as np
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

np.random.seed(42)
N = 2000

# ── Continuous features ──────────────────────────────────────────────────────
hours_studied       = np.random.uniform(1, 44, N)
attendance          = np.random.uniform(40, 100, N)
sleep_hours         = np.random.uniform(4, 10, N)
previous_scores     = np.random.uniform(30, 100, N)
tutoring_sessions   = np.random.randint(0, 10, N).astype(float)
physical_activity   = np.random.uniform(0, 6, N)

# ── Ordinal features (0/1/2) ─────────────────────────────────────────────────
parental_involvement  = np.random.randint(0, 3, N).astype(float)
access_to_resources   = np.random.randint(0, 3, N).astype(float)
motivation_level      = np.random.randint(0, 3, N).astype(float)
family_income         = np.random.randint(0, 3, N).astype(float)
teacher_quality       = np.random.randint(0, 3, N).astype(float)
distance_from_home    = np.random.randint(0, 3, N).astype(float)

# ── Binary features (0/1) ────────────────────────────────────────────────────
extracurricular       = np.random.randint(0, 2, N).astype(float)
internet_access       = np.random.randint(0, 2, N).astype(float)
school_public         = np.random.randint(0, 2, N).astype(float)
peer_neutral          = np.random.randint(0, 2, N).astype(float)
peer_positive         = (1 - peer_neutral) * np.random.randint(0, 2, N)
peer_positive         = peer_positive.astype(float)
learning_disabilities = np.random.choice([0, 1], N, p=[0.85, 0.15]).astype(float)
edu_hs                = np.random.randint(0, 2, N).astype(float)
edu_pg                = ((1 - edu_hs) * np.random.randint(0, 2, N)).astype(float)
gender_male           = np.random.randint(0, 2, N).astype(float)

# ── Build feature matrix (21 columns, matches FEATURE_ORDER) ─────────────────
X = np.column_stack([
    hours_studied, attendance, parental_involvement, access_to_resources,
    sleep_hours, previous_scores, motivation_level, tutoring_sessions,
    family_income, teacher_quality, physical_activity, distance_from_home,
    extracurricular, internet_access, school_public,
    peer_neutral, peer_positive, learning_disabilities,
    edu_hs, edu_pg, gender_male
])

# ── Exam score target (realistic weighted formula + noise) ───────────────────
exam_score = (
    0.30 * previous_scores +
    0.22 * attendance +
    0.18 * hours_studied * (40 / 44) +   # normalise to ~0-40 range contribution
    3.5  * parental_involvement +
    2.0  * motivation_level +
    1.8  * tutoring_sessions +
    2.5  * access_to_resources +
    1.5  * teacher_quality +
    -4.0 * learning_disabilities +
    2.0  * internet_access +
    np.random.normal(0, 4, N)
).clip(0, 100)

# ── Dropout risk target (1 = at risk) ────────────────────────────────────────
risk_score = (
    -0.4 * attendance +
    -0.3 * previous_scores +
    -1.5 * hours_studied * (10 / 44) +
    -2.0 * motivation_level +
    3.0  * learning_disabilities +
    -1.5 * access_to_resources +
    np.random.normal(0, 5, N)
)
at_risk = (risk_score > np.percentile(risk_score, 70)).astype(int)

# ── Train / test split ───────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(X, exam_score, test_size=0.2, random_state=42)
_, _, r_train, r_test = train_test_split(X, at_risk, test_size=0.2, random_state=42)

# ── Fit scaler on training data ──────────────────────────────────────────────
scaler = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)
X_test_sc  = scaler.transform(X_test)

# ── Train models ─────────────────────────────────────────────────────────────
exam_model = RandomForestRegressor(n_estimators=100, random_state=42)
exam_model.fit(X_train_sc, y_train)

at_risk_model = RandomForestClassifier(n_estimators=100, random_state=42)
at_risk_model.fit(X_train_sc, r_train)

lr_model = LinearRegression()
lr_model.fit(X_train_sc, y_train)

rf_model = RandomForestRegressor(n_estimators=50, random_state=42)
rf_model.fit(X_train_sc, y_train)

# ── Save all models ──────────────────────────────────────────────────────────
os.makedirs('models', exist_ok=True)
for name, obj in [
    ('exam_score_model.pkl', exam_model),
    ('at_risk_model.pkl',    at_risk_model),
    ('scaler.pkl',           scaler),
    ('lr_model.pkl',         lr_model),
    ('rf_model.pkl',         rf_model),
]:
    with open(os.path.join('models', name), 'wb') as f:
        pickle.dump(obj, f)

# ── Print metrics ─────────────────────────────────────────────────────────────
print(f"exam_score_model  R²       = {exam_model.score(X_test_sc, y_test):.4f}")
print(f"lr_model          R²       = {lr_model.score(X_test_sc, y_test):.4f}")
print(f"rf_model          R²       = {rf_model.score(X_test_sc, y_test):.4f}")
print(f"at_risk_model     Accuracy = {at_risk_model.score(X_test_sc, r_test):.4f}")
print("All 5 models saved to models/")
