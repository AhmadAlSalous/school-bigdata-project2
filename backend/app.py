import csv
from collections import defaultdict
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

# -----------------------------------------------------------------------------
# Paths & in-memory "tables"
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "datasets" / "clean"

app = Flask(__name__)
CORS(app)

# Each table will be a list of dicts
tables: dict[str, list[dict]] = {
    "dim_students": [],
    "dim_classes": [],
    "dim_semesters": [],
    "dim_date": [],
    "fact_attendance": [],
}


# -----------------------------------------------------------------------------
# CSV loading helpers
# -----------------------------------------------------------------------------
def load_csv_table(name: str, filename: str, int_fields=None) -> None:
    """
    Load a CSV file into memory as a list of dicts.
    Optionally cast some columns to int.
    """
    if int_fields is None:
        int_fields = []

    path = DATA_DIR / filename
    if not path.exists():
        print(f"[WARN] {name}: file not found at {path}")
        tables[name] = []
        return

    print(f"[LOAD] Loading {name} from {path}")
    rows: list[dict] = []

    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Cast selected fields to int
            for col in int_fields:
                val = row.get(col, "")
                if val == "" or val is None:
                    row[col] = None
                else:
                    try:
                        row[col] = int(val)
                    except ValueError:
                        row[col] = None
            rows.append(row)

    print(f"[LOAD] {name}: {len(rows):,} rows")
    tables[name] = rows


def load_all_tables() -> None:
    """
    Load all star-schema tables from datasets/clean/*.csv
    """
    # dim_students.csv: student_key,student_id,first_name,last_name,gender,nationality,birthdate,grade_level,class_id
    load_csv_table(
        "dim_students",
        "dim_students.csv",
        int_fields=["student_key", "student_id", "grade_level", "class_id"],
    )

    # dim_classes.csv: class_key,class_id,class_name,grade_level
    load_csv_table(
        "dim_classes",
        "dim_classes.csv",
        int_fields=["class_key", "class_id", "grade_level"],
    )

    # dim_semesters.csv: semester_key,semester_id,semester_name,start_date,end_date
    load_csv_table(
        "dim_semesters",
        "dim_semesters.csv",
        int_fields=["semester_key", "semester_id"],
    )

    # dim_date.csv: date_key,date_value,year,month,day,day_of_week
    load_csv_table(
        "dim_date",
        "dim_date.csv",
        int_fields=["date_key", "year", "month", "day"],
    )

    # fact_attendance.csv: attendance_id,student_key,class_key,semester_key,date_key,grade
    load_csv_table(
        "fact_attendance",
        "fact_attendance.csv",
        int_fields=["attendance_id", "student_key", "class_key", "semester_key", "date_key", "grade"],
    )


print("[SERVER] Starting Flask API...")
print(f"[SERVER] Loading CSV datasets from: {DATA_DIR}")
load_all_tables()


# -----------------------------------------------------------------------------
# Utility
# -----------------------------------------------------------------------------
def ensure_tables(*names: str):
    """
    Check that given tables are loaded and non-empty.
    """
    missing = [n for n in names if not tables.get(n)]
    return missing


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@app.route("/health", methods=["GET"])
def health():
    return jsonify(
        status="ok",
        tables={name: len(rows) for name, rows in tables.items()},
    )


@app.route("/students/count", methods=["GET"])
def students_count():
    missing = ensure_tables("dim_students")
    if missing:
        return jsonify(
            error="Required tables not loaded",
            missing=missing,
        ), 500

    students = tables["dim_students"]
    total = len(students)

    # group by gender
    gender_counts: defaultdict[str, int] = defaultdict(int)
    for row in students:
        gender = row.get("gender") or "Unknown"
        gender_counts[gender] += 1

    by_gender = [
        {"gender": g, "count": c}
        for g, c in sorted(gender_counts.items())
    ]

    return jsonify(
        total_students=total,
        by_gender=by_gender,
    )


@app.route("/grades/by-gender", methods=["GET"])
def grades_by_gender():
    missing = ensure_tables("fact_attendance", "dim_students")
    if missing:
        return jsonify(
            error="Required tables not loaded",
            missing=missing,
        ), 500

    fact = tables["fact_attendance"]
    students = tables["dim_students"]

    # Build lookup: student_key -> gender
    gender_by_student_key: dict[int, str] = {}
    for s in students:
        sk = s.get("student_key")
        if isinstance(sk, int):
            gender_by_student_key[sk] = s.get("gender") or "Unknown"

    # Aggregate grades by gender
    sum_by_gender: defaultdict[str, int] = defaultdict(int)
    count_by_gender: defaultdict[str, int] = defaultdict(int)

    for row in fact:
        sk = row.get("student_key")
        grade = row.get("grade")

        if not isinstance(sk, int) or not isinstance(grade, int):
            continue

        gender = gender_by_student_key.get(sk, "Unknown")
        sum_by_gender[gender] += grade
        count_by_gender[gender] += 1

    result = []
    for gender, total_grade in sum_by_gender.items():
        n = count_by_gender[gender]
        avg = total_grade / n if n > 0 else None
        result.append(
            {
                "gender": gender,
                "avg_grade": round(avg, 2) if avg is not None else None,
                "num_records": n,
            }
        )

    # Sort for stable output
    result.sort(key=lambda r: r["gender"])

    return jsonify(data=result)


@app.route("/grades/by-class", methods=["GET"])
def grades_by_class():
    missing = ensure_tables("fact_attendance", "dim_classes")
    if missing:
        return jsonify(
            error="Required tables not loaded",
            missing=missing,
        ), 500

    fact = tables["fact_attendance"]
    classes = tables["dim_classes"]

    # class_key -> class_name
    name_by_class_key: dict[int, str] = {}
    for c in classes:
        ck = c.get("class_key")
        if isinstance(ck, int):
            name_by_class_key[ck] = c.get("class_name") or f"Class {ck}"

    sum_by_class: defaultdict[str, int] = defaultdict(int)
    count_by_class: defaultdict[str, int] = defaultdict(int)

    for row in fact:
        ck = row.get("class_key")
        grade = row.get("grade")

        if not isinstance(ck, int) or not isinstance(grade, int):
            continue

        cname = name_by_class_key.get(ck, f"Class {ck}")
        sum_by_class[cname] += grade
        count_by_class[cname] += 1

    result = []
    for cname, total_grade in sum_by_class.items():
        n = count_by_class[cname]
        avg = total_grade / n if n > 0 else None
        result.append(
            {
                "class_name": cname,
                "avg_grade": round(avg, 2) if avg is not None else None,
                "num_records": n,
            }
        )

    result.sort(key=lambda r: r["class_name"])

    return jsonify(data=result)


@app.route("/debug/sample", methods=["GET"])
def debug_sample():
    out = {}
    for name, rows in tables.items():
        out[name] = {
            "rows": len(rows),
            "head": rows[:3],  # first 3 rows
        }
    return jsonify(out)

@app.route("/kpis/total-classes", methods=["GET"])
def kpis_total_classes():
    missing = ensure_tables("dim_classes")
    if missing:
        return jsonify(error="Required tables not loaded", missing=missing), 500
    
    classes = tables["dim_classes"]
    total = len(classes)
    
    return jsonify(total_classes=total)


@app.route("/kpis/total-attendance", methods=["GET"])
def kpis_total_attendance():
    missing = ensure_tables("fact_attendance")
    if missing:
        return jsonify(error="Required tables not loaded", missing=missing), 500
    
    attendance = tables["fact_attendance"]
    total = len(attendance)
    
    return jsonify(total_attendance_records=total)


@app.route("/kpis/average-grade", methods=["GET"])
def kpis_average_grade():
    missing = ensure_tables("fact_attendance")
    if missing:
        return jsonify(error="Required tables not loaded", missing=missing), 500
    
    fact = tables["fact_attendance"]
    
    total_grade = 0
    count = 0
    
    for row in fact:
        grade = row.get("grade")
        if isinstance(grade, int):
            total_grade += grade
            count += 1
    
    avg_grade = round(total_grade / count, 2) if count > 0 else None
    
    return jsonify(
        average_grade=avg_grade,
        total_records=count
    )

@app.route("/students/by-nationality", methods=["GET"])
def students_by_nationality():
    missing = ensure_tables("dim_students")
    if missing:
        return jsonify(error="Required tables not loaded", missing=missing), 500
    
    students = tables["dim_students"]
    
    nationality_counts: defaultdict[str, int] = defaultdict(int)
    for row in students:
        nationality = row.get("nationality") or "Unknown"
        nationality_counts[nationality] += 1
    
    result = [
        {"nationality": n, "count": c}
        for n, c in sorted(nationality_counts.items(), key=lambda x: -x[1])
    ]
    
    return jsonify(data=result)


@app.route("/students/by-grade-level", methods=["GET"])
def students_by_grade_level():
    missing = ensure_tables("dim_students")
    if missing:
        return jsonify(error="Required tables not loaded", missing=missing), 500
    
    students = tables["dim_students"]
    
    grade_counts: defaultdict[int, int] = defaultdict(int)
    for row in students:
        grade_level = row.get("grade_level")
        if isinstance(grade_level, int):
            grade_counts[grade_level] += 1
    
    result = [
        {"grade_level": g, "count": c}
        for g, c in sorted(grade_counts.items())
    ]
    
    return jsonify(data=result)


@app.route("/students/list", methods=["GET"])
def students_list():
    missing = ensure_tables("dim_students")
    if missing:
        return jsonify(error="Required tables not loaded", missing=missing), 500
    
    students = tables["dim_students"]
    
    # Get filter parameters
    search = request.args.get("search", default=None, type=str)
    gender = request.args.get("gender", default=None, type=str)
    nationality = request.args.get("nationality", default=None, type=str)
    grade_level = request.args.get("grade_level", default=None, type=int)
    
    # Get pagination parameters
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=100, type=int)
    
    # Apply filters (AND logic - all filters must match)
    filtered_students = []
    
    for student in students:
        # Search filter (case-insensitive match in first_name or last_name)
        if search:
            search_lower = search.lower()
            first_name = (student.get("first_name") or "").lower()
            last_name = (student.get("last_name") or "").lower()
            if search_lower not in first_name and search_lower not in last_name:
                continue
        
        # Gender filter (exact match)
        if gender:
            student_gender = student.get("gender")
            if student_gender != gender:
                continue
        
        # Nationality filter (exact match)
        if nationality:
            student_nationality = student.get("nationality")
            if student_nationality != nationality:
                continue
        
        # Grade level filter (exact match)
        if grade_level is not None:
            student_grade = student.get("grade_level")
            if not isinstance(student_grade, int) or student_grade != grade_level:
                continue
        
        # All filters passed, include this student
        filtered_students.append(student)
    
    # Calculate pagination on filtered dataset
    total = len(filtered_students)
    start = (page - 1) * per_page
    end = start + per_page
    
    paginated_students = filtered_students[start:end]
    
    return jsonify(
        data=paginated_students,
        pagination={
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page if total > 0 else 0
        }
    )

@app.route("/grades/distribution", methods=["GET"])
def grades_distribution():
    missing = ensure_tables("fact_attendance")
    if missing:
        return jsonify(error="Required tables not loaded", missing=missing), 500
    
    fact = tables["fact_attendance"]
    
    bins = {
        "40-49": 0,
        "50-59": 0,
        "60-69": 0,
        "70-79": 0,
        "80-89": 0,
        "90-100": 0
    }
    
    for row in fact:
        grade = row.get("grade")
        if isinstance(grade, int):
            if 40 <= grade < 50:
                bins["40-49"] += 1
            elif 50 <= grade < 60:
                bins["50-59"] += 1
            elif 60 <= grade < 70:
                bins["60-69"] += 1
            elif 70 <= grade < 80:
                bins["70-79"] += 1
            elif 80 <= grade < 90:
                bins["80-89"] += 1
            elif 90 <= grade <= 100:
                bins["90-100"] += 1
    
    result = [
        {"range": range_name, "count": count}
        for range_name, count in bins.items()
    ]
    
    return jsonify(data=result)


@app.route("/grades/trend-by-date", methods=["GET"])
def grades_trend_by_date():
    missing = ensure_tables("fact_attendance", "dim_date")
    if missing:
        return jsonify(error="Required tables not loaded", missing=missing), 500
    
    fact = tables["fact_attendance"]
    dates = tables["dim_date"]
    
    date_by_key: dict[int, str] = {}
    for d in dates:
        dk = d.get("date_key")
        if isinstance(dk, int):
            date_by_key[dk] = d.get("date_value") or ""
    
    sum_by_date: defaultdict[str, int] = defaultdict(int)
    count_by_date: defaultdict[str, int] = defaultdict(int)
    
    for row in fact:
        dk = row.get("date_key")
        grade = row.get("grade")
        
        if not isinstance(dk, int) or not isinstance(grade, int):
            continue
        
        date_value = date_by_key.get(dk, "")
        if date_value:
            sum_by_date[date_value] += grade
            count_by_date[date_value] += 1
    
    result = []
    for date_value in sorted(sum_by_date.keys()):
        total = sum_by_date[date_value]
        count = count_by_date[date_value]
        avg = round(total / count, 2) if count > 0 else None
        result.append({
            "date": date_value,
            "average_grade": avg,
            "count": count
        })
    
    return jsonify(data=result)


@app.route("/attendance/by-month", methods=["GET"])
def attendance_by_month():
    missing = ensure_tables("fact_attendance", "dim_date")
    if missing:
        return jsonify(error="Required tables not loaded", missing=missing), 500
    
    fact = tables["fact_attendance"]
    dates = tables["dim_date"]
    
    year_month_by_key: dict[int, tuple[int, int]] = {}
    for d in dates:
        dk = d.get("date_key")
        year = d.get("year")
        month = d.get("month")
        if isinstance(dk, int) and isinstance(year, int) and isinstance(month, int):
            year_month_by_key[dk] = (year, month)
    
    count_by_month: defaultdict[tuple[int, int], int] = defaultdict(int)
    
    for row in fact:
        dk = row.get("date_key")
        if isinstance(dk, int):
            ym = year_month_by_key.get(dk)
            if ym:
                count_by_month[ym] += 1
    
    result = []
    for (year, month), count in sorted(count_by_month.items()):
        result.append({
            "year": year,
            "month": month,
            "month_name": ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][month - 1],
            "count": count
        })
    
    return jsonify(data=result)


@app.route("/attendance/by-weekday", methods=["GET"])
def attendance_by_weekday():
    missing = ensure_tables("fact_attendance", "dim_date")
    if missing:
        return jsonify(error="Required tables not loaded", missing=missing), 500
    
    fact = tables["fact_attendance"]
    dates = tables["dim_date"]
    
    weekday_by_key: dict[int, str] = {}
    for d in dates:
        dk = d.get("date_key")
        if isinstance(dk, int):
            weekday_by_key[dk] = d.get("day_of_week") or "Unknown"

    count_by_weekday: defaultdict[str, int] = defaultdict(int)
    
    for row in fact:
        dk = row.get("date_key")
        if isinstance(dk, int):
            weekday = weekday_by_key.get(dk, "Unknown")
            count_by_weekday[weekday] += 1

    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    result = []
    for day in weekday_order:
        if day in count_by_weekday:
            result.append({
                "weekday": day,
                "count": count_by_weekday[day]
            })
    
    for day, count in count_by_weekday.items():
        if day not in weekday_order:
            result.append({
                "weekday": day,
                "count": count
            })
    
    return jsonify(data=result)


@app.route("/attendance/by-semester", methods=["GET"])
def attendance_by_semester():
    missing = ensure_tables("fact_attendance", "dim_semesters")
    if missing:
        return jsonify(error="Required tables not loaded", missing=missing), 500
    
    fact = tables["fact_attendance"]
    semesters = tables["dim_semesters"]
    
    name_by_key: dict[int, str] = {}
    for s in semesters:
        sk = s.get("semester_key")
        if isinstance(sk, int):
            name_by_key[sk] = s.get("semester_name") or f"Semester {sk}"
    
    count_by_semester: defaultdict[str, int] = defaultdict(int)
    null_count = 0
    
    for row in fact:
        sk = row.get("semester_key")
        if sk is None or (isinstance(sk, str) and sk == "\\N"):
            null_count += 1
        elif isinstance(sk, int):
            semester_name = name_by_key.get(sk, f"Semester {sk}")
            count_by_semester[semester_name] += 1
    
    result = []
    for semester_name, count in sorted(count_by_semester.items()):
        result.append({
            "semester_name": semester_name,
            "count": count
        })
    
    if null_count > 0:
        result.append({
            "semester_name": "Unknown/Null",
            "count": null_count
        })
    
    return jsonify(data=result)


@app.route("/classes/students-per-class", methods=["GET"])
def classes_students_per_class():
    missing = ensure_tables("dim_students", "dim_classes")
    if missing:
        return jsonify(error="Required tables not loaded", missing=missing), 500
    
    students = tables["dim_students"]
    classes = tables["dim_classes"]

    name_by_class_id: dict[int, str] = {}
    for c in classes:
        cid = c.get("class_id")
        cname = c.get("class_name")
        if isinstance(cid, int):
            name_by_class_id[cid] = cname or f"Class {cid}"
    
    count_by_class: defaultdict[int, int] = defaultdict(int)
    for row in students:
        cid = row.get("class_id")
        if isinstance(cid, int):
            count_by_class[cid] += 1
    
    result = []
    for cid, count in sorted(count_by_class.items()):
        result.append({
            "class_id": cid,
            "class_name": name_by_class_id.get(cid, f"Class {cid}"),
            "student_count": count
        })
    
    return jsonify(data=result)


@app.route("/classes/by-grade-level", methods=["GET"])
def classes_by_grade_level():
    missing = ensure_tables("dim_classes")
    if missing:
        return jsonify(error="Required tables not loaded", missing=missing), 500
    
    classes = tables["dim_classes"]

    classes_by_grade: defaultdict[int, list] = defaultdict(list)
    for row in classes:
        grade_level = row.get("grade_level")
        if isinstance(grade_level, int):
            classes_by_grade[grade_level].append({
                "class_id": row.get("class_id"),
                "class_name": row.get("class_name"),
                "class_key": row.get("class_key")
            })
    
    result = []
    for grade_level in sorted(classes_by_grade.keys()):
        result.append({
            "grade_level": grade_level,
            "classes": classes_by_grade[grade_level],
            "total_classes": len(classes_by_grade[grade_level])
        })
    
    return jsonify(data=result)


@app.route("/semesters/list", methods=["GET"])
def semesters_list():
    missing = ensure_tables("dim_semesters")
    if missing:
        return jsonify(error="Required tables not loaded", missing=missing), 500
    
    semesters = tables["dim_semesters"]
    
    result = []
    for row in semesters:
        result.append({
            "semester_key": row.get("semester_key"),
            "semester_id": row.get("semester_id"),
            "semester_name": row.get("semester_name"),
            "start_date": row.get("start_date"),
            "end_date": row.get("end_date")
        })
    
    result.sort(key=lambda x: x.get("start_date", ""))
    
    return jsonify(data=result)


if __name__ == "__main__":
    # Run on localhost:5000 so UI can call it
    app.run(host="0.0.0.0", port=5000, debug=True)

