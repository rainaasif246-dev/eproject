# EduPredict — Installation Guide

## System Requirements

| Component | Minimum | Recommended |
|---|---|---|
| Processor | Intel i5 (4 Cores) | Intel i7 or higher |
| RAM | 8 GB | 16 GB |
| Storage | 2 GB free space | 10 GB SSD |
| OS | Windows 10 64-bit | Windows 11 64-bit |
| Python | 3.9+ | 3.11 |

---

## Step 1 — Install Python

1. Go to https://www.python.org/downloads/
2. Download Python 3.11 (Windows 64-bit installer)
3. Run the installer
4. ✅ IMPORTANT: Check "Add Python to PATH" before clicking Install
5. Click "Install Now"
6. Verify installation — open Command Prompt and type:
   ```
   python --version
   ```
   Expected output: `Python 3.11.x`

---

## Step 2 — Download / Extract the Project

1. Extract the project zip file to a folder, e.g.:
   ```
   C:\Users\YourName\Desktop\Edu_predict\
   ```
2. Make sure the folder contains:
   - app.py
   - requirements.txt
   - models/ folder (with .pkl files)
   - templates/ folder
   - static/ folder

---

## Step 3 — Open Command Prompt in Project Folder

**Option A (Easy):**
1. Open the project folder in File Explorer
2. Click on the address bar at the top
3. Type `cmd` and press Enter
4. Command Prompt opens directly in that folder

**Option B:**
1. Press `Win + R`, type `cmd`, press Enter
2. Navigate to project folder:
   ```
   cd "C:\Users\YourName\Desktop\Edu_predict"
   ```

---

## Step 4 — (Optional) Create Virtual Environment

It is recommended to use a virtual environment to avoid conflicts:

```
python -m venv env
env\Scripts\activate
```

You will see `(env)` appear at the start of your command prompt line.

---

## Step 5 — Install Dependencies

Run this command in the project folder:

```
pip install -r requirements.txt
```

This will install:
- Flask 3.1.3
- NumPy 1.26.2
- Pandas 2.1.4
- Scikit-learn 1.5.2
- Jinja2 3.1.4

Wait for all packages to finish installing (may take 2-5 minutes).

---

## Step 6 — (Optional) Retrain Models

The pre-trained `.pkl` model files are already included in the `models/` folder.
You only need this step if the models are missing or corrupted:

```
python train_models.py
```

Expected output:
```
Linear Regression  R² = 0.91xx
Random Forest      R² = 0.97xx
Models saved: models/lr_model.pkl, models/rf_model.pkl
```

---

## Step 7 — Run the Application

```
python app.py
```

Expected output:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

---

## Step 8 — Open in Browser

1. Open any web browser (Chrome recommended)
2. Go to: http://127.0.0.1:5000
3. You will see the EduPredict landing page
4. Click "Get Started" or go to http://127.0.0.1:5000/login

---

## Step 9 — Login

Use any of the demo credentials:

| Role          | Username | Password    |
|---------------|----------|-------------|
| Administrator | admin    | Admin@123   |
| Teacher       | teacher  | Teach@123   |
| Analyst       | analyst  | Analyst@123 |
| Student       | student  | Student@123 |

---

## Troubleshooting

**Problem:** `pip` is not recognized
**Solution:** Reinstall Python and make sure "Add to PATH" is checked

---

**Problem:** `ModuleNotFoundError: No module named 'flask'`
**Solution:** Run `pip install -r requirements.txt` again

---

**Problem:** Port 5000 already in use
**Solution:** Change port in app.py last line:
```python
app.run(host='127.0.0.1', port=5001, debug=True)
```
Then open http://127.0.0.1:5001

---

**Problem:** `.pkl` model files missing
**Solution:** Run `python train_models.py` to regenerate basic models

---

**Problem:** White screen or template error
**Solution:** Make sure you are running `python app.py` from inside the project folder,
not from a parent directory.

---

## Stopping the Application

Press `Ctrl + C` in the Command Prompt to stop the Flask server.
