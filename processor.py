import pandas as pd

def process_payroll_data(df, config):
    # 1. Clean & Standardize Identification
    if 'Employee ID' not in df.columns: 
        df['Employee ID'] = [f"EMP{i+1:03d}" for i in range(len(df))]
    if 'Name' not in df.columns: 
        df['Name'] = "Employee " + (df.index + 1).astype(str)

    # 2. List of mandatory numeric columns to prevent calculation crashes
    numeric_cols = [
        'Basic salary', 'Reimburse allowances', 'Travelling allowances', 
        'Nopay days', 'Salary adjustment', 'Tax rate', 'APIT', 
        'Salary advances', 'Loan installment', 'Loan interest', 'Others', 'Stamps fee'
    ]
    
    for col in numeric_cols:
        if col not in df.columns:
            df[col] = 0.0
    
    df[numeric_cols] = df[numeric_cols].fillna(0.0)

    # --- CALCULATION LOGIC ---

    # Gross Salary
    df['Gross Salary'] = df['Basic salary'] + df['Reimburse allowances'] + df['Travelling allowances']

    # Nopay Amount
    working_days = config.get('working_days', 30)
    df['Nopay Amount'] = (df['Basic salary'] / working_days) * df['Nopay days']

    # Liable Salary
    df['Liable Salary'] = df['Gross Salary'] - df['Nopay Amount'] - df['Salary adjustment']

    # Government Tax
    df['Tax_Calculated'] = df['Liable Salary'] * df['Tax rate']
    df['Total_Tax'] = df['Tax_Calculated'] + df['APIT']

    # EPF (Employee 8%)
    epf_emp_rate = config.get('epf_emp_rate', 0.08)
    df['EPF_Employee_Amt'] = df['Basic salary'] * epf_emp_rate

    # Stamp Fee (Explicitly creating Stamps_Final to avoid KeyErrors)
    global_stamp = config.get('stamps_fee', 25.0)
    df['Stamps_Final'] = df['Stamps fee'].apply(lambda x: x if x > 0 else global_stamp)

    # Total Deduction
    df['Total Deduction'] = (
        df['Nopay Amount'] + 
        df['Salary adjustment'] + 
        df['Total_Tax'] + 
        df['EPF_Employee_Amt'] + 
        df['Salary advances'] + 
        df['Loan installment'] + 
        df['Loan interest'] + 
        df['Others'] + 
        df['Stamps_Final']
    )

    # Net Salary
    df['Net Salary'] = df['Gross Salary'] - df['Total Deduction']

    # Company Contributions
    df['EPF_Company_Amt'] = df['Basic salary'] * config.get('epf_co_rate', 0.12)
    df['ETF_Company_Amt'] = df['Basic salary'] * config.get('etf_co_rate', 0.03)

    return df