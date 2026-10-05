"""
EduPredict — HDFS Dataset Generator
Generates 4 realistic CSV datasets for HDFS simulation:
  1. academic_records.csv       — 2000 records
  2. student_demographics.csv  — 2000 records
  3. attendance_records.csv    — 6000 records (3 months × 2000 students)
  4. lms_activity.csv          — 3000 records
"""

import csv
import os
import random
from datetime import date, timedelta

random.seed(42)

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_DIR  = os.path.join(BASE_DIR, 'data', 'ingested')
os.makedirs(DATA_DIR, exist_ok=True)

# ─── shared lookup tables ────────────────────────────────────────────────────
FIRST_NAMES = [
    'Ali','Sara','Ahmed','Fatima','Usman','Ayesha','Bilal','Zara','Omar','Hina',
    'Kamran','Nadia','Faisal','Sana','Tariq','Rabia','Imran','Mehwish','Asad','Lubna',
    'Hassan','Maria','Zubair','Amna','Shahzad','Rida','Waseem','Komal','Adeel','Huma',
    'Junaid','Samia','Fahad','Noor','Rana','Bushra','Zahid','Sidra','Naeem','Saima',
    'Danish','Laiba','Hamza','Maryam','Irfan','Saira','Murad','Aisha','Rizwan','Nimra',
]
LAST_NAMES = [
    'Khan','Ali','Ahmed','Malik','Raza','Sheikh','Butt','Chaudhry','Mirza','Qureshi',
    'Siddiqui','Javed','Tariq','Iqbal','Shah','Baig','Nawaz','Riaz','Mehmood','Farooq',
]
COURSES = [
    'Computer Science','Mathematics','Physics','Business Administration',
    'Data Science','Software Engineering','Electrical Engineering','Civil Engineering',
]
SEMESTERS = [1, 2, 3, 4, 5, 6, 7, 8]
CITIES    = ['Karachi','Lahore','Islamabad','Peshawar','Quetta','Multan','Faisalabad','Rawalpindi']
SCHOOLS   = ['Public','Private']
INCOME    = ['Low','Medium','High']
PARENT_EDU= ['Matric','Intermediate','Bachelor','Master','PhD']

def rand_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

def student_ids(n=2000):
    return [f"STU-{1000 + i}" for i in range(n)]

IDS = student_ids()

# ─── 1. academic_records.csv ─────────────────────────────────────────────────
def gen_academic():
    path = os.path.join(DATA_DIR, 'academic_records.csv')
    fields = [
        'student_id','name','course','semester',
        'hours_studied','attendance_pct','previous_score',
        'quiz_avg','midterm_score','assignment_avg',
        'tutoring_sessions','sleep_hours','physical_activity_days',
        'motivation_level','teacher_quality','access_to_resources',
        'internet_access','extracurricular','learning_disabilities',
        'peer_influence','predicted_score','at_risk','pass_fail'
    ]
    rows = []
    for sid in IDS:
        attendance = random.randint(45, 100)
        prev       = random.randint(35, 95)
        hours      = round(random.uniform(1.0, 10.0), 1)
        quiz       = round(random.uniform(30, 95), 1)
        midterm    = round(random.uniform(30, 95), 1)
        assign     = round(random.uniform(40, 98), 1)
        tutor      = random.randint(0, 8)
        sleep      = round(random.uniform(4.0, 10.0), 1)
        pa         = random.randint(0, 7)
        motiv      = random.choice(['Low','Medium','High'])
        tq         = random.choice(['Low','Medium','High'])
        atr        = random.choice(['Low','Medium','High'])
        internet   = random.choice(['Yes','No'])
        extra      = random.choice(['Yes','No'])
        ld         = random.choice(['Yes','No','No','No'])   # weighted No
        peer       = random.choice(['Negative','Neutral','Positive'])

        # simple predicted score formula (realistic)
        base  = attendance * 0.35 + prev * 0.30 + hours * 2.5
        bonus = (1 if motiv == 'High' else 0) * 4 + tutor * 1.2
        pred  = round(min(100, max(0, base + bonus + random.gauss(0, 4))), 1)

        at_risk   = 'Yes' if (pred < 50 or attendance < 60) else 'No'
        pass_fail = 'Pass' if pred >= 50 else 'Fail'

        rows.append([
            sid, rand_name(), random.choice(COURSES), random.choice(SEMESTERS),
            hours, attendance, prev, quiz, midterm, assign,
            tutor, sleep, pa, motiv, tq, atr,
            internet, extra, ld, peer, pred, at_risk, pass_fail
        ])

    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        writer.writerows(rows)
    print(f"[OK] academic_records.csv    -- {len(rows):,} records -> {path}")
    return path

# ─── 2. student_demographics.csv ─────────────────────────────────────────────
def gen_demographics():
    path = os.path.join(DATA_DIR, 'student_demographics.csv')
    fields = [
        'student_id','name','age','gender','city','school_type',
        'family_income','parental_education','distance_from_home',
        'siblings','has_scholarship','enrollment_year','nationality'
    ]
    rows = []
    for sid in IDS:
        age        = random.randint(17, 26)
        gender     = random.choice(['Male','Female'])
        city       = random.choice(CITIES)
        school     = random.choice(SCHOOLS)
        income     = random.choice(INCOME)
        par_edu    = random.choice(PARENT_EDU)
        distance   = random.choice(['Near','Moderate','Far'])
        siblings   = random.randint(0, 5)
        scholar    = random.choice(['Yes','No','No'])   # weighted No
        enroll_yr  = random.choice([2020, 2021, 2022, 2023, 2024])

        rows.append([
            sid, rand_name(), age, gender, city, school,
            income, par_edu, distance,
            siblings, scholar, enroll_yr, 'Pakistani'
        ])

    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        writer.writerows(rows)
    print(f"[OK] student_demographics.csv -- {len(rows):,} records -> {path}")
    return path

# ─── 3. attendance_records.csv ───────────────────────────────────────────────
def gen_attendance():
    path = os.path.join(DATA_DIR, 'attendance_records.csv')
    fields = ['record_id','student_id','date','status','subject','semester','remarks']
    rows   = []
    rid    = 1

    # 3 months: Jan, Feb, Mar 2025
    start = date(2025, 1, 6)   # first Monday
    end   = date(2025, 3, 29)  # last Saturday

    # collect weekdays only
    school_days = []
    cur = start
    while cur <= end:
        if cur.weekday() < 5:   # Mon–Fri
            school_days.append(cur)
        cur += timedelta(days=1)

    # pick ~3 days per week per student (sample)
    sample_size = 3   # avg classes per student per week

    subjects_map = {
        'Computer Science':         ['OOP','DBMS','OS','Networks','AI'],
        'Mathematics':              ['Calculus','Algebra','Statistics','Discrete Math','Numerical Methods'],
        'Physics':                  ['Mechanics','Electromagnetism','Optics','Thermodynamics','Modern Physics'],
        'Business Administration':  ['Marketing','Finance','HRM','Accounting','Business Law'],
        'Data Science':             ['Machine Learning','Big Data','Data Viz','Python','Statistics'],
        'Software Engineering':     ['SE Principles','Testing','DevOps','Agile','Design Patterns'],
        'Electrical Engineering':   ['Circuit Analysis','Digital Logic','Signals','Power Systems','Electronics'],
        'Civil Engineering':        ['Structures','Fluid Mechanics','Surveying','Materials','Soil Mechanics'],
    }

    # Assign each student a course (consistent)
    course_assign = {sid: random.choice(COURSES) for sid in IDS}

    for sid in IDS:
        course   = course_assign[sid]
        subjects = subjects_map[course]
        semester = random.randint(1, 8)

        # each student attends ~60 records over 3 months (20 per month × 3)
        chosen_days = random.sample(school_days, min(60, len(school_days)))
        chosen_days.sort()

        for d in chosen_days:
            subject = random.choice(subjects)
            # attendance probability based on day
            if d.weekday() == 0:  # Monday slightly lower
                p_present = 0.82
            elif d.weekday() == 4:  # Friday slightly lower
                p_present = 0.80
            else:
                p_present = 0.88

            roll = random.random()
            if roll < p_present:
                status  = 'Present'
                remark  = ''
            elif roll < p_present + 0.06:
                status  = 'Late'
                remark  = 'Arrived late'
            else:
                status  = 'Absent'
                remark  = random.choice(['Medical Leave','Personal Reason','No Reason','Transport Issue'])

            rows.append([rid, sid, d.isoformat(), status, subject, semester, remark])
            rid += 1

    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        writer.writerows(rows)
    print(f"[OK] attendance_records.csv   -- {len(rows):,} records -> {path}")
    return path

# ─── 4. lms_activity.csv ─────────────────────────────────────────────────────
def gen_lms():
    path = os.path.join(DATA_DIR, 'lms_activity.csv')
    fields = [
        'log_id','student_id','date','activity_type','course',
        'duration_mins','resource_accessed','score_obtained',
        'submission_status','device_type','session_id'
    ]
    activity_types = [
        'Video Lecture Viewed','Assignment Submitted','Quiz Attempted',
        'Forum Post','Resource Downloaded','Live Session Attended',
        'Practice Test','Peer Review Submitted','Flashcard Study','Discussion Reply'
    ]
    resources = [
        'Lecture_01.mp4','Lecture_02.mp4','Chapter_3_Notes.pdf','Assignment_1.pdf',
        'Quiz_2.html','Practice_Set_A.pdf','Lab_Manual.pdf','Slides_Week5.pptx',
        'Recorded_Session.mp4','Reading_Material.pdf','Case_Study_1.pdf','Formula_Sheet.pdf'
    ]
    devices = ['Laptop','Mobile','Tablet','Desktop']
    submissions = ['On Time','Late','Not Submitted','Resubmitted']

    rows = []
    start = date(2025, 1, 1)

    # 3000 activity logs across 2000 students (~1.5 per student avg)
    # but some students are very active, some less
    for i in range(3000):
        sid          = random.choice(IDS)
        log_date     = start + timedelta(days=random.randint(0, 89))
        activity     = random.choice(activity_types)
        course       = random.choice(COURSES)
        duration     = random.randint(5, 120)
        resource     = random.choice(resources)
        score        = round(random.uniform(0, 100), 1) if 'Quiz' in activity or 'Test' in activity or 'Assignment' in activity else ''
        sub_status   = random.choice(submissions) if 'Submit' in activity or 'Assignment' in activity else ''
        device       = random.choice(devices)
        session_id   = f"SES-{random.randint(10000,99999)}"

        rows.append([
            i + 1, sid, log_date.isoformat(), activity, course,
            duration, resource, score, sub_status, device, session_id
        ])

    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        writer.writerows(rows)
    print(f"[OK] lms_activity.csv         -- {len(rows):,} records -> {path}")
    return path


# ─── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print("\n[*] EduPredict -- Generating HDFS datasets...\n")
    p1 = gen_academic()
    p2 = gen_demographics()
    p3 = gen_attendance()
    p4 = gen_lms()
    print(f"\n[DONE] All 4 datasets saved to: {DATA_DIR}")
    print("   -> academic_records.csv      (2,000 records)")
    print("   -> student_demographics.csv  (2,000 records)")
    print("   -> attendance_records.csv    (see above)")
    print("   -> lms_activity.csv          (3,000 records)")
