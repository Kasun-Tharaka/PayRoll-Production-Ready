import pandas as pd
from database import get_all_employees

def process_payroll_data(df_excel, config):
    # 1. Fetch Employee Master Data from DB
    df_db = get_all_employees()
    
    # 2. Standardize Employee ID columns for merging
    # Rename excel column to match DB if needed
    if 'Employee ID' in df_excel.columns:
        df_excel = df_excel.rename(columns={'Employee ID': 'emp_id'})
    
    # Ensure emp_id is string type in both
    df_excel['emp_id'] = df_excel['emp_id'].astype(str).str.strip()
    
    # --- STEP 1.5: REMOVE DUPLICATE COLUMNS FROM EXCEL ---
    # We want personal details to come from the DB, not the Excel.
    # So we drop them from Excel to prevent "Name" vs "Name" conflicts.
    conflicting_cols = ['Name', 'name', 'Designation', 'designation', 'Department', 'department', 
                        'NIC', 'nic', 'Bank', 'bank_name', 'Account', 'account_no', 'Joined Date', 'joined_date']
    
    # Drop these columns from Excel if they exist
    df_excel = df_excel.drop(columns=[c for c in conflicting_cols if c in df_excel.columns], errors='ignore')

    # 3. MERGE Excel (Financials) with DB (Personal Details)
    if not df_db.empty:
        df_db['emp_id'] = df_db['emp_id'].astype(str).str.strip()
        df_merged = pd.merge(df_excel, df_db, on='emp_id', how='left')
    else:
        # If DB is empty, just use Excel
        df_merged = df_excel
        # Create empty columns to prevent crashes
        for col in ['name', 'designation', 'department', 'nic', 'bank_name', 'account_no']:
            df_merged[col] = "N/A"

    # Fill Missing Personal Data if Excel had no match in DB
    fill_defaults = {
        'name': 'Unknown Employee',
        'designation': '-',
        'department': '-',
        'nic': '-',
        'bank_name': '-',
        'account_no': '-'
    }
    df_merged.fillna(fill_defaults, inplace=True)
    
    # Rename 'name' from DB to 'Name' for the final report
    # Since we dropped 'Name' from Excel earlier, this is now safe!
    df_merged = df_merged.rename(columns={'name': 'Name', 'emp_id': 'Employee ID'})

    # 4. NUMERIC CLEANUP
    # Ensure all calculation columns exist and are numbers
    numeric_cols = [
        'Basic salary', 'Reimburse allowances', 'Travelling allowances', 
        'Nopay days', 'Salary adjustment', 'Tax rate', 'APIT', 
        'Salary advances', 'Loan installment', 'Loan interest', 'Others', 'Stamps fee'
    ]
    
    for col in numeric_cols:
        if col not in df_merged.columns:
            df_merged[col] = 0.0
    
    df_merged[numeric_cols] = df_merged[numeric_cols].fillna(0.0)

    # --- CALCULATION LOGIC ---
    df_merged['Gross Salary'] = df_merged['Basic salary'] + df_merged['Reimburse allowances'] + df_merged['Travelling allowances']
    
    working_days = config.get('working_days', 30)
    # Avoid division by zero
    if working_days == 0: working_days = 30
    
    df_merged['Nopay Amount'] = (df_merged['Basic salary'] / working_days) * df_merged['Nopay days']

    df_merged['Liable Salary'] = df_merged['Gross Salary'] - df_merged['Nopay Amount'] - df_merged['Salary adjustment']

    df_merged['Tax_Calculated'] = df_merged['Liable Salary'] * df_merged['Tax rate']
    df_merged['Total_Tax'] = df_merged['Tax_Calculated'] + df_merged['APIT']

    epf_emp_rate = config.get('epf_emp_rate', 0.08)
    df_merged['EPF_Employee_Amt'] = df_merged['Basic salary'] * epf_emp_rate

    global_stamp = config.get('stamps_fee', 25.0)
    if 'Stamps fee' in df_merged.columns:
        df_merged['Stamps_Final'] = df_merged['Stamps fee'].apply(lambda x: x if x > 0 else global_stamp)
    else:
        df_merged['Stamps_Final'] = global_stamp

    df_merged['Total Deduction'] = (
        df_merged['Nopay Amount'] + 
        df_merged['Salary adjustment'] + 
        df_merged['Total_Tax'] + 
        df_merged['EPF_Employee_Amt'] + 
        df_merged['Salary advances'] + 
        df_merged['Loan installment'] + 
        df_merged['Loan interest'] + 
        df_merged['Others'] + 
        df_merged['Stamps_Final']
    )

    df_merged['Net Salary'] = df_merged['Gross Salary'] - df_merged['Total Deduction']

    df_merged['EPF_Company_Amt'] = df_merged['Basic salary'] * config.get('epf_co_rate', 0.12)
    df_merged['ETF_Company_Amt'] = df_merged['Basic salary'] * config.get('etf_co_rate', 0.03)

    # 5. FINAL CLEANUP: REMOVE DUPLICATES (Safety Net)
    # This removes any duplicate columns that might have slipped through
    df_merged = df_merged.loc[:, ~df_merged.columns.duplicated()]

    return df_merged