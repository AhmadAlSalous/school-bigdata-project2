

2️⃣ Technical Architecture
```
                     ┌────────────────────────┐
                     │   Raw Data (CSV/JSON)  │
                     └─────────────┬──────────┘
                                   ▼
                    ┌─────────────────────────────┐
                    │  HDFS Data Lake (Raw Zone)  │
                    └─────────────┬───────────────┘
                                   ▼
                    ┌───────────────────────────┐
                    │ Hive Clean Zone (Parquet) │
                    └─────────────┬─────────────┘
                                   ▼
                    ┌───────────────────────────┐
                    │     Star Schema Tables    │
                    │ dim_students / dim_date…  │
                    │ fact_attendance           │
                    └─────────────┬─────────────┘
                                   ▼
                 ┌──────────────────────────────────┐
                 │   Flask Backend (REST API)       │
                 └─────────────┬────────────────────┘
                                   ▼
                 ┌──────────────────────────────────┐
                 │  Frontend Dashboard (UI Team)    │
                 └──────────────────────────────────┘
```

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



5️⃣ Backend API (Flask)

Backend code is in:
`backend/app.py`

install dependencies
```
python3 -m venv venv
```
```
source venv/bin/activate
```
```
pip install -r backend/requirements-min.txt
```

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
```git clone https://github.com/AhmadAlSalous/school-bigdata-project2.git```
```cd school-bigdata-project2```

🧰 Step 2: Create a virtual environment
### Linux / macOS
```
python3 -m venv venv
```
```
source venv/bin/activate
```

### Windows (PowerShell)
```
python -m venv venv
```
```
venv\Scripts\activate
```

📦 Step 3: Install API dependencies
```
pip install -r backend/requirements-min.txt
```


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
```
python backend/app.py
```


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
```
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
```

✔ What You ALREADY support fully

These sections are 100% ready with your current backend + clean CSVs:

🔹 Section 1 — KPIs

✔ Total Students → /students/count

✔ Total Classes → can get from CSV or add tiny API

✔ Total Attendance Records → can get from CSV or add tiny API

✔ Average Grade → can calculate from fact_attendance

🔹 Section 2 — Students Analytics

You can build these using backend or frontend processing:

✔ Gender distribution → backend: /grades/by-gender OR directly from students.csv

✔ Students by nationality → frontend can read CSV directly

✔ Students per grade level → frontend or small API

✔ Student table → frontend can load CSV

🔹 Section 3 — Grades Analytics

✔ Average grade by gender → /grades/by-gender

✔ Grade distribution histogram → from CSV (fact_attendance)

✔ Trend of grades by date → from fact_attendance.csv + dim_date.csv (frontend join)

🔹 Section 4 — Attendance Analytics

You already have the data you need:

✔ Attendance by month → fact_attendance + dim_date join

✔ Attendance by weekday → dim_date

✔ Attendance by semester → fact_attendance + dim_semesters

These can be done either:

Via frontend loading CSVs OR

With 2–3 small API endpoints

🔹 Section 5 — Class Analytics

✔ Students per class → from students.csv

✔ Classes per grade level → dim_classes.csv

🔹 Section 6 — Semesters

✔ Table of semesters → dim_semesters.csv

❗ But here is what is missing

Just 3–4 tiny backend endpoints will make the dashboard MUCH easier for your UI team:

🔸 Missing Endpoint 1 — /classes/count

Returns total number of classes
→ trivial to add, 3 lines of code

🔸 Missing Endpoint 2 — /attendance/count

Returns 2M attendance rows
→ also trivial

🔸 Missing Endpoint 3 — /attendance/by-month

UI team will love this
→ small groupby

🔸 Missing Endpoint 4 — /attendance/by-weekday

Useful chart

⭐ But even without these APIs, the UI team CAN STILL BUILD THE DASHBOARD

Why?

Because all clean CSVs are already available in:

datasets/clean/*.csv


Meaning…

The UI can load CSVs directly using:

JavaScript CSV parser (Papaparse) or Python (if using Streamlit)

They don’t NEED the backend at all to draw charts.
The CSVs are clean, high-quality, and have complete dimensions + fact table.

🧠 So what is the BEST approach for your timeline?
Option A — Fastest (UI team loads CSV directly)

✔ No backend work needed
✔ UI team can start immediately
✔ They just import CSVs and do charts

Recommended because you have 4 days left

Option B — Clean API layer (Adds polish to the project)

You add 4–5 simple endpoints:

Endpoint	Purpose
/students/count	Already exists
/grades/by-gender	Already exists
/classes/count	Missing
/attendance/count	Missing
/attendance/by-month	Missing
/attendance/by-weekday	Missing

This looks more professional in your presentation.

🏆 My Recommendation for You

Because you want to impress:

✔ Let the UI team work directly with CSVs (fastest + safest)
✔ You add the missing 4 small endpoints later for extra polish

This way:

Your UI team doesn’t wait

Your backend isn’t a blocker

Your project has BOTH a data lake + API + dashboard

Your professor will be impressed by the completeness

🔥 Summary (very important)
You CAN build the entire dashboard RIGHT NOW using only CSVs.
💡 You DO NOT need any more data.

You DO NOT need new pipelines.
You DO NOT need to regenerate anything.

Only OPTIONAL backend polishing remains:

attendance count

classes count

attendance by month

attendance by weekday
