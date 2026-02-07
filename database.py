import sqlite3
import pandas as pd
from datetime import datetime
import hashlib
import logging

# Configure Logging
logging.basicConfig(filename='system.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

DB_NAME = "property_payroll.db"

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 1. Base History Table
    c.execute('''CREATE TABLE IF NOT EXISTS payroll_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                emp_id TEXT, emp_name TEXT, month TEXT, year INTEGER, 
                basic_salary REAL, gross_salary REAL, total_deduction REAL, 
                net_salary REAL, processed_date TIMESTAMP)''')

    # Migration Loop
    needed_columns = [
        "nopay_amount REAL", "total_tax REAL", 
        "epf_employee REAL", "epf_company REAL", "etf_company REAL"
    ]
    for col_def in needed_columns:
        try:
            c.execute(f"ALTER TABLE payroll_history ADD COLUMN {col_def}")
        except sqlite3.OperationalError:
            pass

    # 2. Employees & 3. Users
    c.execute('CREATE TABLE IF NOT EXISTS employees (emp_id TEXT PRIMARY KEY, name TEXT, designation TEXT, department TEXT, nic TEXT, bank_name TEXT, account_no TEXT, joined_date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)')
    
    # Default Admin
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        admin_pw = hash_password("admin123")
        c.execute("INSERT INTO users VALUES ('admin', ?, 'Admin')", (admin_pw,))
        logging.info("System Initialized: Default Admin account created.")
        
    conn.commit()
    conn.close()

# --- USER MANAGEMENT ---
def add_user(username, password, role):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users VALUES (?, ?, ?)", (username, hash_password(password), role))
        conn.commit()
        logging.info(f"ADMIN ACTION: New user '{username}' ({role}) created.")
        return True
    except Exception as e:
        logging.error(f"Failed to create user {username}: {e}")
        return False
    finally: conn.close()

def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT username, role FROM users", conn)
    conn.close()
    return df

def delete_user(username):
    if username == 'admin': return False 
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE username=?", (username,))
    conn.commit()
    conn.close()
    logging.warning(f"ADMIN ACTION: User '{username}' was deleted.")
    return True

def login_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT role FROM users WHERE username=? AND password=?", (username, hash_password(password)))
    user = c.fetchone()
    conn.close()
    if user:
        logging.info(f"LOGIN SUCCESS: User '{username}' logged in as {user[0]}.")
        return user[0]
    else:
        logging.warning(f"LOGIN FAILED: Attempt for username '{username}'.")
        return None

# --- EMPLOYEE MANAGEMENT ---
def add_employee(emp_id, name, desig, dept, nic, bank, acc_no, date):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO employees VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (emp_id, name, desig, dept, nic, bank, acc_no, date))
        conn.commit()
        logging.info(f"Employee Added: {emp_id} - {name}")
        return True
    except: return False
    finally: conn.close()

def update_employee(emp_id, name, desig, dept, nic, bank, acc_no, date):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('UPDATE employees SET name=?, designation=?, department=?, nic=?, bank_name=?, account_no=?, joined_date=? WHERE emp_id=?', (name, desig, dept, nic, bank, acc_no, date, emp_id))
    conn.commit()
    conn.close()
    logging.info(f"Employee Updated: {emp_id}")

def delete_employee(emp_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM employees WHERE emp_id=?", (emp_id,))
    conn.commit()
    conn.close()
    logging.warning(f"Employee Deleted: {emp_id}")

def get_all_employees():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM employees", conn)
    conn.close()
    return df

def get_employee_by_id(emp_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM employees WHERE emp_id=?", (emp_id,))
    data = c.fetchone()
    conn.close()
    return data

# --- HISTORY ---
def save_payroll_to_db(df, month, year):
    conn = sqlite3.connect(DB_NAME)
    db_data = df.copy()
    db_data['month'] = month
    db_data['year'] = year
    db_data['processed_date'] = datetime.now()
    
    subset = db_data[[
        'Employee ID', 'Name', 'month', 'year', 'Basic salary', 'Gross Salary', 
        'Nopay Amount', 'Total_Tax', 'EPF_Employee_Amt', 'Total Deduction', 
        'Net Salary', 'EPF_Company_Amt', 'ETF_Company_Amt', 'processed_date'
    ]]
    subset.columns = [
        'emp_id', 'emp_name', 'month', 'year', 'basic_salary', 'gross_salary', 
        'nopay_amount', 'total_tax', 'epf_employee', 'total_deduction', 
        'net_salary', 'epf_company', 'etf_company', 'processed_date'
    ]
    
    subset.to_sql('payroll_history', conn, if_exists='append', index=False)
    conn.close()
    logging.info(f"ARCHIVE: Saved payroll history for {month} {year} ({len(df)} records).")

def fetch_history(month, year):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM payroll_history WHERE month=? AND year=?", conn, params=(month, year))
    conn.close()
    return df