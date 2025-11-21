import csv
from collections import defaultdict
from pathlib import Path

from flask import Flask, jsonify
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


if __name__ == "__main__":
    # Run on localhost:5000 so UI can call it
    app.run(host="0.0.0.0", port=5000, debug=True)

