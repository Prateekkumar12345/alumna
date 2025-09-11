import pandas as pd
import json
import re
from sqlalchemy import create_engine, text

# ==============================
# DATABASE CONNECTION DETAILS
# ==============================
DATABASE_URI = "postgresql://ml_user:ml_password@3.7.255.54:5432/ml_db"

# ==============================
# STEP 1: READ EXCEL FILE
# ==============================
file_path = "College_dataset_merged.xlsx"  # <-- Replace with your actual Excel file path
df = pd.read_excel(file_path)

# ==============================
# STEP 2: CONNECT TO POSTGRESQL
# ==============================
engine = create_engine(DATABASE_URI)

# ==============================
# STEP 3: CREATE TABLE IF NOT EXISTS
# ==============================
create_table_query = """
CREATE TABLE IF NOT EXISTS college (
    College_ID VARCHAR(50) PRIMARY KEY,
    College_Name TEXT,
    Name TEXT,
    Type TEXT,
    Affiliation TEXT,
    Location TEXT,
    Website TEXT,
    Contact TEXT,
    Email TEXT,
    Courses JSON,
    Scholarship TEXT,
    Admission_Process TEXT
);
"""
with engine.connect() as conn:
    conn.execute(text(create_table_query))
    conn.commit()

# ==============================
# STEP 4: REMOVE OLD DATA
# ==============================
with engine.connect() as conn:
    conn.execute(text("DELETE FROM college;"))
    conn.commit()
print("🗑️ Old data removed successfully.")

# ==============================
# STEP 5: ESCAPE SINGLE QUOTES
# ==============================
def escape_quotes(value):
    if isinstance(value, str):
        return value.replace("'", "''")
    return value

# ==============================
# STEP 6: CLEAN CONTACT NUMBERS
# ==============================
def clean_contact_numbers(raw_contact):
    """Cleans messy contact strings into neat comma-separated numbers"""
    if pd.isna(raw_contact):
        return None
    raw_contact = str(raw_contact)
    raw_contact = raw_contact.replace(" ", "").replace("-", "")
    numbers = re.findall(r'\+?\d+', raw_contact)
    return ", ".join(numbers) if numbers else None

# ==============================
# STEP 7: INSERT CLEANED DATA WITH ERROR HANDLING
# ==============================
skipped_rows = []

for index, row in df.iterrows():
    try:
        college_id = escape_quotes(str(row["College ID"]))
        college_name = escape_quotes(str(row["College"]))
        name = escape_quotes(str(row["Name"]))
        college_type = escape_quotes(str(row["Type"]))
        affiliation = escape_quotes(str(row["Affiliation"]))
        location = escape_quotes(str(row["Location"]))
        website = escape_quotes(str(row["Website"]))
        contact = clean_contact_numbers(row["Contact"])
        email = escape_quotes(str(row["E-mail"]))
        scholarship = escape_quotes(str(row["Scholarship"]))
        admission = escape_quotes(str(row["Admission Process"]))

        # 🟢 Format Courses into JSON
        courses_raw = str(row["Courses (ID, Category, Duration, Eligibility, Language, Accreditation, Fees)"])
        courses_list = []
        for course in courses_raw.replace("\n", ";").replace(",", ";").split(";"):
            course = course.strip()
            if not course:
                continue
            parts = course.split("-")
            if len(parts) >= 2:
                name_part = parts[0].strip()
                fees_part = parts[-1].strip()
                courses_list.append({
                    "Course_ID": name_part[:5].upper().replace(" ", ""),
                    "Category": name_part,
                    "Duration": "N/A",
                    "Fees": fees_part
                })
            else:
                courses_list.append({
                    "Course_ID": course[:5].upper().replace(" ", ""),
                    "Category": course,
                    "Duration": "N/A",
                    "Fees": "N/A"
                })

        courses_json = json.dumps(courses_list, ensure_ascii=False)

        # 🟢 Build Insert Query
        insert_query = f"""
        INSERT INTO college
        (College_ID, College_Name, Name, Type, Affiliation, Location, Website, Contact, Email, Courses, Scholarship, Admission_Process)
        VALUES
        ('{college_id}', '{college_name}', '{name}', '{college_type}', '{affiliation}',
        '{location}', '{website}', '{contact}', '{email}', '{courses_json}'::json,
        '{scholarship}', '{admission}')
        ON CONFLICT (College_ID) DO NOTHING;
        """

        # Execute Query
        with engine.connect() as conn:
            conn.execute(text(insert_query))
            conn.commit()

    except Exception as e:
        print(f"⚠️ Skipping row {index + 1} due to error: {e}")
        skipped_rows.append((index + 1, str(e)))
        continue

print("✅ Data insertion completed successfully!")
print(f"⚠️ Total skipped rows: {len(skipped_rows)}")

if skipped_rows:
    print("\n🚨 Skipped Rows:")
    for row, reason in skipped_rows:
        print(f" - Row {row}: {reason}")

# ==============================
# STEP 8: VERIFY INSERTED DATA
# ==============================
with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM college;"))
    count = result.fetchone()[0]
    print(f"\n📌 Total successfully inserted rows: {count}")
