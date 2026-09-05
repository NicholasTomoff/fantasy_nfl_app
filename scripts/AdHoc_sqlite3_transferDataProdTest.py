import sqlite3

src_db = "test_fantasy.db"
dest_db = "fantasy.db"
table_name = "seasons"
primary_key = "id"  # Adjust if your PK differs

# Connect to both databases
src_conn = sqlite3.connect(src_db)
dest_conn = sqlite3.connect(dest_db)
src_cursor = src_conn.cursor()
dest_cursor = dest_conn.cursor()

# ✅ Step 1: Get table schema from source
src_cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
create_stmt = src_cursor.fetchone()
if not create_stmt:
    raise Exception(f"Table '{table_name}' not found in {src_db}")
create_stmt = create_stmt[0]

# ✅ Step 2: Create table in destination if it doesn't exist
dest_cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
if not dest_cursor.fetchone():
    print(f"Creating '{table_name}' table in {dest_db}")
    dest_cursor.execute(create_stmt)

# ✅ Step 3: Get all existing PKs in destination
dest_cursor.execute(f"SELECT {primary_key} FROM {table_name}")
existing_ids = {row[0] for row in dest_cursor.fetchall()}

# ✅ Step 4: Pull all rows from source
src_cursor.execute(f"SELECT * FROM {table_name}")
rows = src_cursor.fetchall()

# ✅ Step 5: Prepare new inserts
columns = [description[0] for description in src_cursor.description]
columns_str = ", ".join(columns)
placeholders = ", ".join(["?"] * len(columns))
new_rows = [row for row in rows if row[columns.index(primary_key)] not in existing_ids]

# ✅ Step 6: Insert new rows
if new_rows:
    dest_cursor.executemany(
        f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})",
        new_rows
    )
    print(f"✅ Inserted {len(new_rows)} new rows into '{table_name}'.")
else:
    print(f"⚠️ No new rows to insert into '{table_name}'.")

# ✅ Finalize
dest_conn.commit()
src_conn.close()
dest_conn.close()
