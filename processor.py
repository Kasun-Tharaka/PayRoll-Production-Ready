import pandas as pd
import logging
from database import get_all_employees

# Configure Logging (Ensures it writes to the same file)
logging.basicConfig(filename='system.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def process_payroll_data(df_excel, config):
    try:
        logging.info("--- STARTED PAYROLL CALCULATION PROCESS ---")
        
        # 1. Fetch Employee Master Data from DB
        df_db = get_all_employees()
        logging.info(f"Fetched {len(df_db)} employee records from Master Database.")
        
        # 2. Standardize Employee ID columns for merging
        if 'Employee ID' in df_excel.columns:
            df_excel = df_excel.rename(columns={'Employee ID': 'emp_id'})
        
        df_excel['emp_id'] = df_excel['emp_id'].astype(str).str.strip()
        
        # --- STEP 1.5: REMOVE DUPLICATE COLUMNS FROM EXCEL ---
        conflicting_cols = ['Name', 'name', 'Designation', 'designation', 'Department', 'department', 
                            'NIC', 'nic', 'Bank', 'bank_name', 'Account', 'account_no', 'Joined Date', 'joined_date']
        df_excel = df_excel.drop(columns=[c for c in conflicting_cols if c in df_excel.columns], errors='ignore')

        # 3. MERGE Excel (Financials) with DB (Personal Details)
        if not df_db.empty:
            df_db['emp_id'] = df_db['emp_id'].astype(str).str.strip()
            df_merged = pd.merge(df_excel, df_db, on='emp_id', how='left')
        else:
            df_merged = df_excel
            for col in ['name', 'designation', 'department', 'nic', 'bank_name', 'account_no']:
                df_merged[col] = "N/A"

        # Fill Missing Personal Data
        fill_defaults = {
            'name': 'Unknown Employee', 'designation': '-', 'department': '-',
            'nic': '-', 'bank_name': '-', 'account_no': '-'
        }
        df_merged.fillna(fill_defaults, inplace=True)
        df_merged = df_merged.rename(columns={'name': 'Name', 'emp_id': 'Employee ID'})

        # 4. NUMERIC CLEANUP
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
            df_merged['Nopay Amount'] + df_merged['Salary adjustment'] + df_merged['Total_Tax'] + 
            df_merged['EPF_Employee_Amt'] + df_merged['Salary advances'] + df_merged['Loan installment'] + 
            df_merged['Loan interest'] + df_merged['Others'] + df_merged['Stamps_Final']
        )

        df_merged['Net Salary'] = df_merged['Gross Salary'] - df_merged['Total Deduction']

        df_merged['EPF_Company_Amt'] = df_merged['Basic salary'] * config.get('epf_co_rate', 0.12)
        df_merged['ETF_Company_Amt'] = df_merged['Basic salary'] * config.get('etf_co_rate', 0.03)

        # 5. FINAL CLEANUP
        df_merged = df_merged.loc[:, ~df_merged.columns.duplicated()]

        logging.info(f"SUCCESS: Calculated payroll for {len(df_merged)} employees.")
        logging.info(f"Total Net Payout: {df_merged['Net Salary'].sum()}")
        return df_merged

    except Exception as e:
        logging.error(f"CRITICAL ERROR in Payroll Calculation: {str(e)}")
        raise e