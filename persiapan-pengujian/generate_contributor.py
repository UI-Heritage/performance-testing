import uuid
import json
import random
from datetime import datetime

# Load the units data from the provided JSON
with open('units.json', 'r') as f:
    units_data = json.load(f)

# Filter out deleted units
active_units = [unit for unit in units_data if unit["deleted_at"] is None]

# Output file paths
sql_file_path = 'insert_contributors.sql'
delete_sql_file_path = 'delete_contributors.sql'
json_file_path = 'contributor_logins.json'

# Role ID for contributors is 3
CONTRIBUTOR_ROLE = 3

# List of common Indonesian university department/faculty names to use in usernames
faculty_prefixes = [
    "fmipa", "fib", "fh", "fe", "ft", "fkg", "fk", "fisip", "fasilkom", "fik", 
    "ff", "fpsi", "vokasi", "fia", "ppsg"
]

# List of common Indonesian first names and last names to combine
first_names = [
    "Budi", "Siti", "Agus", "Dewi", "Joko", "Rina", "Wayan", "Putri", "Ahmad", "Sri",
    "Dimas", "Indah", "Bambang", "Lestari", "Putra", "Rini", "Adi", "Nita", "Hendra", "Maya"
]

last_names = [
    "Wijaya", "Susanto", "Hartono", "Santoso", "Kusuma", "Wati", "Setiawan", "Purnama", "Permana", "Maulana",
    "Hidayat", "Nugraha", "Pratama", "Saputra", "Utama", "Nugroho", "Suryanto", "Irawan", "Gunawan", "Heriyanto"
]

# List to store all user IDs for deletion later
all_user_ids = []

# List to store login information
login_data = []

# Open file for writing SQL statements
with open(sql_file_path, 'w') as sql_file:
    # Write SQL header and transaction begin
    sql_file.write("-- SQL script to insert 200 contributor users\n")
    sql_file.write("BEGIN TRANSACTION;\n\n")
    
    # Set to track used usernames
    used_usernames = set()
    
    # Generate 200 users
    for i in range(200):
        # Generate a UUID for the user
        user_id = uuid.uuid4()
        credential_id = uuid.uuid4()
        
        # Store user ID for deletion script
        all_user_ids.append(str(user_id))
        
        # Assign a random unit
        unit = random.choice(active_units)
        
        # Generate username (faculty based + sequential ID to ensure uniqueness)
        faculty_prefix = random.choice(faculty_prefixes)
        
        # Create username with dot format for SSO login
        first = random.choice(first_names).lower()
        last = random.choice(last_names).lower()
        username = f"{first}.{last}{i+1000}"  # Start from 1000 to avoid conflicts
        
        # Just in case, verify it's unique
        while username in used_usernames:
            username = f"{first}.{last}{random.randint(1000, 9999)}"
        
        # Add to used usernames set
        used_usernames.add(username)
        
        # Generate email with @ui.ac.id
        email = f"{username}@ui.ac.id"
        
        # Generate full name by combining first and last names
        full_name = f"{first.capitalize()} {last.capitalize()}"
        
        # Generate Indonesian phone number
        phone_number = f"+62{random.randint(8, 9)}{random.randint(1, 9)}{random.randint(1000000, 99999999)}"
        
        # Generate personal email (not UI email)
        personal_email = f"{username}_{random.randint(1, 999)}@gmail.com"
        
        # Generate position based on common academic positions
        positions = ["Mahasiswa", "Dosen", "Asisten Dosen", "Peneliti", "Staff", "Koordinator Unit", "Kepala Program"]
        position = random.choice(positions)
        
        # Current timestamp for PostgreSQL
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # SQL insert statement for users table
        user_sql = f"""
INSERT INTO users (
    id, username, full_name, email, role, unit_id, position, 
    phone_number, personal_email, created_at, updated_at, deleted_at
) VALUES (
    '{user_id}', 
    '{username}', 
    '{full_name}', 
    '{email}', 
    {CONTRIBUTOR_ROLE}, 
    '{unit["id"]}', 
    '{position}', 
    '{phone_number}', 
    '{personal_email}', 
    '{now}', 
    '{now}', 
    NULL
);
"""
        sql_file.write(user_sql)
        
        # SQL insert statement for user_credentials table
        credential_sql = f"""
INSERT INTO user_credentials (
    id, user_id, hashed_password, password_changed_at, 
    created_at, updated_at, deleted_at
) VALUES (
    '{credential_id}', 
    '{user_id}', 
    NULL, 
    NULL, 
    '{now}', 
    '{now}', 
    NULL
);
"""
        sql_file.write(credential_sql)
        sql_file.write("\n")
        
        # Create SSO login data in required format
        npm = f"21{random.randint(10000000, 99999999)}"  # Random NPM number
        kd_org = f"0{random.randint(1, 9)}.00.{random.randint(10, 20)}.0{random.randint(1, 9)}"  # Random organization code
        
        login_info = {
            "user": username,
            "ldap_cn": full_name,
            "kd_org": kd_org,
            "peran_user": position.lower(),
            "npm": npm,
            "nama": full_name
        }
        
        login_data.append(login_info)
    
    # Write commit statement
    sql_file.write("COMMIT;\n")

# Write JSON file for logins
with open(json_file_path, 'w') as json_file:
    json.dump(login_data, json_file, indent=2)

# Create delete SQL script
with open(delete_sql_file_path, 'w') as delete_file:
    delete_file.write("-- SQL script to delete the contributor users\n")
    delete_file.write("BEGIN TRANSACTION;\n\n")
    
    # First delete user_credentials (due to foreign key constraint)
    delete_file.write("-- Delete all user credentials\n")
    user_ids_string = "', '".join(all_user_ids)
    delete_file.write(f"DELETE FROM user_credentials WHERE user_id IN ('{user_ids_string}');\n\n")
    
    # Then delete users
    delete_file.write("-- Delete all users\n")
    delete_file.write(f"DELETE FROM users WHERE id IN ('{user_ids_string}');\n\n")
    
    delete_file.write("COMMIT;\n")

print(f"SQL insert script generated at: {sql_file_path}")
print(f"SQL delete script generated at: {delete_sql_file_path}")
print(f"Login JSON data generated at: {json_file_path}")