# connection and queries - SQLite

import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "property_payroll.db"

def init_db():
    """Create the database tables if they don't exist."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Table to store monthly payroll history
    # We store the most important columns for reporting
    c.execute('''
        CREATE TABLE IF NOT EXISTS payroll_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id TEXT,
            emp_name TEXT,
            month TEXT,
            year INTEGER,
            basic_salary REAL,
            gross_salary REAL,
            total_deduction REAL,
            net_salary REAL,
            epf_company REAL,
            etf_company REAL,
            processed_date TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_payroll_to_db(df, month, year):
    """
    Saves the processed dataframe to SQLite.
    Assumes df has columns: 'Employee ID', 'Name' (You must ensure Excel has these)
    """
    conn = sqlite3.connect(DB_NAME)
    
    # Add metadata columns
    df['month'] = month
    df['year'] = year
    df['processed_date'] = datetime.now()
    
    # We map the DataFrame columns to the Database columns
    # This requires renaming columns temporarily to match DB schema or just dumping raw
    # For simplicity, let's dump specific columns we care about:
    
    # Check if Employee ID and Name exist in Excel, if not, handle gracefully
    if 'Employee ID' not in df.columns:
        df['Employee ID'] = 'Unknown'
    if 'Name' not in df.columns:
        df['Name'] = 'Unknown'

    subset = df[[
        'Employee ID', 'Name', 'month', 'year', 
        'Basic salary', 'Gross Salary', 'Total Deduction', 'Net Salary', 
        'EPF_Company_Amt', 'ETF_Company_Amt', 'processed_date'
    ]].copy()
    
    # Rename for DB matching
    subset.columns = [
        'emp_id', 'emp_name', 'month', 'year',
        'basic_salary', 'gross_salary', 'total_deduction', 'net_salary',
        'epf_company', 'etf_company', 'processed_date'
    ]
    
    # Append to database
    subset.to_sql('payroll_history', conn, if_exists='append', index=False)
    conn.close()

def fetch_history(month, year):
    """Retrieve history for a specific month."""
    conn = sqlite3.connect(DB_NAME)
    query = "SELECT * FROM payroll_history WHERE month=? AND year=?"
    df = pd.read_sql(query, conn, params=(month, year))
    conn.close()
    return df