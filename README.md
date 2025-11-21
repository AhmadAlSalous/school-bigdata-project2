📚 School Big Data Management Project

A full end-to-end Big Data pipeline using synthetic educational data

🚀 Overview

This project implements a complete Big Data architecture for a UAE-based school, following the academic requirements of the ISIT312 – Big Data Management course.

The solution includes:

A synthetic large-scale dataset (2M+ rows) representing student, class, semester, and attendance data

A full data lake architecture using Hadoop + Hive

ETL pipelines transforming raw CSV/JSONL into optimized Parquet tables

A Star Schema (dimensional model) for analytics

A Flask backend API exposing analytics endpoints for dashboards

Clear instructions for the Frontend/UI team to connect to the API

This README provides everything required to run, understand, and extend the system.

1️⃣ Motivation

The school lacked:

A centralized analytics platform

A unified way to store, clean, and query large volumes of attendance data

Ability to derive insights such as grade distribution, gender performance, class comparisons, etc.

Big Data tools are well-suited because:

The datasets are large (millions of rows)

Hive and Hadoop support distributed storage + processing

Parquet improves compression + analytics performance

The API exposes data for any UI/dashboard system

2️⃣ Technical Architecture
                     ┌────────────────────────┐
                     │   Raw Data (CSV/JSON)  │
                     └─────────────┬──────────┘
                                   ▼
                    ┌───────────────────────────┐
                    │  HDFS Data Lake (Raw Zone) │
                    └─────────────┬─────────────┘
                                   ▼
                    ┌───────────────────────────┐
                    │ Hive Clean Zone (Parquet) │
                    └─────────────┬─────────────┘
                                   ▼
                    ┌───────────────────────────┐
                    │     Star Schema Tables     │
                    │ dim_students / dim_date…   │
                    │ fact_attendance            │
                    └─────────────┬─────────────┘
                                   ▼
                 ┌──────────────────────────────────┐
                 │   Flask Backend (REST API)        │
                 └─────────────┬────────────────────┘
                                   ▼
                 ┌──────────────────────────────────┐
                 │  Frontend Dashboard (UI Team)     │
                 └──────────────────────────────────┘

3️⃣ Dataset Description

Synthetic data was generated using Python (generate_data.py).

Included Tables (Clean Zone – CSV)

datasets/clean/dim_students.csv

datasets/clean/dim_classes.csv

datasets/clean/dim_semesters.csv

datasets/clean/dim_date.csv

datasets/clean/fact_attendance.csv

| Table           | Rows             |
| --------------- | ---------------- |
| dim_students    | 2,000,000        |
| dim_classes     | 4001             |
| dim_semesters   | 87               |
| dim_date        | 3 years of dates |
| fact_attendance | 2,000,000        |
Raw zone files (CSV + JSONL) are not included in GitHub to avoid large file limits.

4️⃣ Hive Setup
Start Hive (no metastore needed)
schematool -initSchema -dbType derby
hive
Create database
CREATE DATABASE school2;
USE school2;
Create raw tables (CSV + JSONL)

(omitted here for brevity; available in project SQL scripts)

Convert to clean Parquet tables

Parquet tables were created for:

dim_students

dim_classes

dim_semesters

dim_date

fact_attendance

Build Star Schema

Primary keys:

dim_students → student_key

dim_classes → class_key

dim_semesters → semester_key

dim_date → date_key

Fact table links all dimensions using foreign keys.

5️⃣ Backend API (Flask)

Backend code is in:
backend/app.py

install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements-min.txt

Run server
python backend/app.py

API Root
http://localhost:5000

| Endpoint            | Description                           |
| ------------------- | ------------------------------------- |
| `/health`           | Check if datasets loaded successfully |
| `/students/count`   | Total students                        |
| `/grades/by-gender` | Avg grade per gender                  |
| (Extendable)        | Add more endpoints easily             |


6️⃣ For the Frontend/UI Team
⭐ This is everything the UI team needs.

You do not need Hadoop or Hive.
You only need the CSVs and the Flask API.

🔧 Step 1: Clone the project
git clone https://github.com/AhmadAlSalous/school-bigdata-project2.git
cd school-bigdata-project2

🧰 Step 2: Create a virtual environment
Linux / macOS
python3 -m venv venv
source venv/bin/activate

Windows (PowerShell)
python -m venv venv
venv\Scripts\activate

📦 Step 3: Install API dependencies
pip install -r backend/requirements-min.txt


Files included:

Flask==3.0.0
flask-cors==4.0.0

📁 Step 4: Ensure clean CSVs exist

Inside:

datasets/clean/


You should see:

dim_students.csv

dim_classes.csv

dim_semesters.csv

dim_date.csv

fact_attendance.csv

If not → tell Ahmad to re-commit them.

▶️ Step 5: Start the backend API
python backend/app.py


You should see:

[SERVER] Starting Flask API...
 * Running on http://localhost:5000

🌐 Step 6: Test API Endpoints
Health
GET http://localhost:5000/health

Students count
GET http://localhost:5000/students/count

Grades by gender
GET http://localhost:5000/grades/by-gender

🎨 Step 7: Using the API in React / JavaScript

Example:

useEffect(() => {
  fetch("http://localhost:5000/students/count")
    .then(res => res.json())
    .then(data => setStudentCount(data.total_students))
}, []);


Bar chart example:

useEffect(() => {
  fetch("http://localhost:5000/grades/by-gender")
    .then(res => res.json())
    .then(data => setGenderStats(data));
}, []);


You can now build:

KPI cards

Gender grade chart

Class performance chart

Attendance trends

Student-detail pages

Everything the UI needs comes from the API.

7️⃣ Project File Structure
school-bigdata-project2/
│
├── backend/
│   ├── app.py
│   └── requirements-min.txt
│
├── datasets/
│   └── clean/
│       ├── dim_students.csv
│       ├── dim_classes.csv
│       ├── dim_date.csv
│       ├── dim_semesters.csv
│       └── fact_attendance.csv
│
├── generate_data.py
├── README.md
└── .gitignore

8️⃣ Lessons Learned

Hive joins require clean keys → solved using careful ETL

Avoid GitHub large files → clean CSVs only

Keep backend lightweight → Flask + CSV is enough for UI

Metastore issues can be avoided using default Derby mode

Frontend should not depend on Hadoop → API abstraction solves it

9️⃣ Conclusion

This project demonstrates:

✔ Full Big Data pipeline
✔ Data Lake architecture
✔ Hive + Parquet optimization
✔ Dimensional modeling
✔ JSON & CSV raw data ingestion
✔ Flask API for analytics
✔ UI-ready endpoints
