# EduPredict — README

## Project Title
**EduPredict: AI-Powered Student Performance & Dropout Prediction System**
Built on Big Data (Hadoop/HDFS) + Machine Learning (Random Forest, XGBoost)

---

## Project Summary
EduPredict is a full-stack web application that uses predictive analytics and machine learning
to monitor student performance, detect dropout risks, and forecast course demand.
It supports 4 user roles (Administrator, Teacher, Analyst, Student) with role-based access control.

---

## Team / Submission Info
- Platform   : Aptech eProject
- Technology : Python, Flask, Scikit-learn, HTML/CSS/JS
- Dataset    : Synthetic Student Performance Dataset (2,000 records)

---

## Assumptions Made
1. HDFS and Hadoop are simulated locally within the Flask app (no actual Hadoop cluster required to run).
2. Real-time streaming (Kafka) is simulated with static event logs for demonstration purposes.
3. All student data is synthetically generated — no real student PII is used.
4. Models are pre-trained and saved as .pkl files; internet connection not required for predictions.
5. Demo account passwords are configured through environment variables when provided; fallback credentials are listed below.
6. The application runs on localhost (127.0.0.1:5000) by default.
7. Uploaded CSV, JSON, and XML files are validated and stored in the local `data/ingested/` directory as an HDFS simulation.

---

## Login Credentials (Demo)

| Role          | Username | Password     |
|---------------|----------|--------------|
| Administrator | admin    | Admin@123    |
| Teacher       | teacher  | Teach@123    |
| Analyst       | analyst  | Analyst@123  |
| Student       | student  | Student@123  |

---

## Project Structure

```
Edu_predict/
├── app.py                        # Main Flask application
├── train_models.py               # Model training script
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── TEST_DATA_DOCUMENTATION.md    # Test data & test cases
├── INSTALLATION_GUIDE.md         # Step-by-step setup guide
├── models/
│   ├── exam_score_model.pkl      # Random Forest Regressor (21 features)
│   ├── at_risk_model.pkl         # Dropout Risk Classifier
│   ├── lr_model.pkl              # Linear Regression model
│   ├── rf_model.pkl              # Random Forest model
│   └── scaler.pkl                # StandardScaler
├── templates/
│   ├── landing.html              # Home/landing page
│   ├── login.html                # Login page
│   ├── register.html             # Registration page
│   ├── dashboard.html            # Analytics dashboard
│   ├── predict.html              # ML predictions
│   ├── students.html             # Student directory
│   ├── alerts.html               # Alerts & notifications
│   ├── ingest.html               # Data ingestion
│   ├── storage.html              # HDFS storage view
│   ├── realtime.html             # Real-time stream
│   ├── reports.html              # Reports
│   ├── course_demand.html        # Course demand forecasting
│   ├── model_metrics.html        # ML model diagnostics
│   ├── user_management.html      # User management (Admin)
│   ├── feedback.html             # Support & feedback
│   ├── profile.html              # User profile
│   └── _sidebar.html             # Shared sidebar component
└── static/
    └── style.css                 # Global stylesheet
```

---

## How to Run
See INSTALLATION_GUIDE.md for full step-by-step instructions.

Quick start:
```
pip install -r requirements.txt
python app.py
```
Then open: http://127.0.0.1:5000

---

## Features Implemented
- Role-Based Authentication (Admin / Teacher / Analyst / Student)
- ML Predictions: Exam Score, Dropout Risk, Course Demand
- Interactive Dashboard with Chart.js visualizations
- HDFS Data Storage simulation with validated CSV/JSON/XML ingestion
- Real-Time Stream monitoring
- Automated Alerts with configurable thresholds
- Student Directory (50 records)
- Data Ingestion pipeline
- User Management & RBAC
- Support / Feedback system
- Reports with CSV and JSON export
- User Registration & Profile management
