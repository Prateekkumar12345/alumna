import pandas as pd
from sqlalchemy import create_engine, text

# ==============================
# DATABASE CONNECTION DETAILS
# ==============================
DATABASE_URI = "postgresql://ml_user:ml_password@3.7.255.54:5432/ml_db"

# ==============================
# STEP 1: CONNECT TO DATABASE
# ==============================
engine = create_engine(DATABASE_URI)

# ==============================
# STEP 2: FETCH 5 RECORDS
# ==============================
query = "SELECT * FROM college LIMIT 5;"

try:
    # Fetch data into a pandas DataFrame
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)

    # Display the fetched data
    print("✅ Successfully fetched 5 records:\n")
    print(df)

except Exception as e:
    print(f"⚠️ Error fetching data: {e}")
