import streamlit as st
import pandas as pd
import os
import logging
from processor import process_payroll_data
from database import (init_db, save_payroll_to_db, fetch_history, add_employee, 
                      update_employee, delete_employee, get_all_employees, 
                      get_employee_by_id, login_user, add_user, get_all_users, delete_user)
from pdf_gen import generate_zip_payslips, create_single_pdf

# 1. Initialize Logging & DB
logging.basicConfig(filename='system.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
init_db()

# 2. Page Configuration
st.set_page_config(page_title="Pitch Capital Payroll", layout="wide", page_icon="🏢")

# --- LOGIN LOGIC ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user_role'] = None

def login_page():
    st.title("🔐 Payroll System Login")
    with st.container():
        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        if st.button("Login"):
            role = login_user(user, pw)
            if role:
                st.session_state['logged_in'] = True
                st.session_state['user_role'] = role
                st.rerun()
            else:
                st.error("Invalid Username or Password")

if not st.session_state['logged_in']:
    login_page()
    st.stop()

# ==========================================
# SIDEBAR SETUP
# ==========================================
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)
else:
    st.sidebar.header("🏢 Pitch Capital")

st.sidebar.title(f"Welcome, {st.session_state['user_role']}")
if st.sidebar.button("Logout"):
    logging.info(f"User {st.session_state['user_role']} Logged Out")
    st.session_state['logged_in'] = False
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Global Settings")
sel_month = st.sidebar.selectbox("Processing Month", 
    ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
sel_year = st.sidebar.number_input("Processing Year", value=2026, step=1)

st.sidebar.subheader("Calculation Constants")
working_days = st.sidebar.number_input("Working Days", value=30)
stamps_fee = st.sidebar.number_input("Stamps Fee (LKR)", value=25.0)

st.sidebar.subheader("Statutory Rates (%)")
epf_emp = st.sidebar.slider("EPF Employee Contribution (%)", 0, 15, 8) / 100
epf_co = st.sidebar.slider("EPF Employer Contribution (%)", 0, 20, 12) / 100
etf_co = st.sidebar.slider("ETF Employer Contribution (%)", 0, 10, 3) / 100

config = {'working_days': working_days, 'stamps_fee': stamps_fee, 'epf_emp_rate': epf_emp, 'epf_co_rate': epf_co, 'etf_co_rate': etf_co}

# --- NAVIGATION TABS ---
tabs_list = ["🚀 Payroll Processing", "👥 Employee Management", "📜 History"]
if st.session_state['user_role'] == 'Admin':
    tabs_list.append("🔑 User Administration")

selected_tabs = st.tabs(tabs_list)

# TAB 1: PAYROLL PROCESSING
with selected_tabs[0]:
    st.subheader(f"Step 1: Upload Data for {sel_month} {sel_year}")
    uploaded_file = st.file_uploader("Upload Finance Excel Sheet", type=['xlsx'])
    if uploaded_file:
        df_input = pd.read_excel(uploaded_file)
        st.write("### 📄 Data Preview (First 5 Rows)")
        st.dataframe(df_input.head())
        if st.button("Calculate Payroll for All Employees"):
            try:
                df_result = process_payroll_data(df_input, config)
                st.session_state['result'] = df_result
                st.success("Calculations complete!")
            except Exception as e:
                st.error(f"Error in calculation: {e}")

        if 'result' in st.session_state:
            df_final = st.session_state['result']
            st.markdown("---")
            st.subheader("📊 Payroll Summary Metrics")
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Net Payout", f"LKR {df_final['Net Salary'].sum():,.2f}")
            m2.metric("Total Company EPF (12%)", f"LKR {df_final['EPF_Company_Amt'].sum():,.2f}")
            m3.metric("Total Company ETF (3%)", f"LKR {df_final['ETF_Company_Amt'].sum():,.2f}")

            st.write("### Detailed Result Table")
            st.dataframe(df_final)

            col_zip, col_db = st.columns(2)
            with st.spinner("Preparing ZIP..."):
                zip_data = generate_zip_payslips(df_final, sel_month, sel_year)
                col_zip.download_button(label="📦 Download All Payslips (ZIP)", data=zip_data, file_name=f"Payslips_{sel_month}_{sel_year}.zip", mime="application/zip")
            if col_db.button("💾 Save to History Database"):
                save_payroll_to_db(df_final, sel_month, sel_year)
                st.success("Archived successfully!")

            st.markdown("---")
            st.subheader("👤 Individual Employee Quick-View & PDF")
            for i, row in df_final.iterrows():
                with st.expander(f"{row['Employee ID']} - {row['Name']}"):
                    c_left, c_right = st.columns([3, 1])
                    c_left.write(f"**Gross:** {row['Gross Salary']:,.2f} | **Deductions:** {row['Total Deduction']:,.2f} | **Net:** {row['Net Salary']:,.2f}")
                    pdf_bytes = create_single_pdf(row, sel_month, sel_year)
                    c_right.download_button("Download PDF", data=pdf_bytes, file_name=f"{row['Employee ID']}_{row['Name']}.pdf", mime="application/pdf", key=f"btn_{row['Employee ID']}_{i}")

# TAB 2: EMPLOYEE MANAGEMENT
with selected_tabs[1]:
    st.header("Manage Employee Database")
    df_emps = get_all_employees()
    st.dataframe(df_emps, use_container_width=True)
    st.divider()
    col_add, col_edit = st.columns(2)
    with col_add:
        st.subheader("➕ Add New Employee")
        with st.form("add_emp_form"):
            new_id = st.text_input("Employee ID"); new_name = st.text_input("Full Name"); new_desig = st.text_input("Designation")
            new_dept = st.text_input("Department"); new_nic = st.text_input("NIC No"); new_bank = st.text_input("Bank Name")
            new_acc = st.text_input("Account No"); new_date = st.text_input("Joined Date (YYYY-MM-DD)")
            if st.form_submit_button("Add to Database"):
                if new_id and new_name:
                    if add_employee(new_id, new_name, new_desig, new_dept, new_nic, new_bank, new_acc, new_date): st.success("Added!"); st.rerun()
                    else: st.error("ID already exists.")
    with col_edit:
        st.subheader("✏️ Update or Remove")
        if not df_emps.empty:
            emp_to_edit = st.selectbox("Select ID to Edit", df_emps['emp_id'].tolist())
            curr_data = get_employee_by_id(emp_to_edit)
            if curr_data:
                c_id, c_name, c_desig, c_dept, c_nic, c_bank, c_acc, c_date = curr_data
                with st.form("edit_emp_form"):
                    e_name = st.text_input("Name", value=c_name); e_desig = st.text_input("Designation", value=c_desig)
                    e_dept = st.text_input("Department", value=c_dept); e_nic = st.text_input("NIC", value=c_nic)
                    e_bank = st.text_input("Bank", value=c_bank); e_acc = st.text_input("Account No", value=c_acc)
                    e_date = st.text_input("Joined Date", value=c_date)
                    cb1, cb2 = st.columns(2)
                    if cb1.form_submit_button("Update"): update_employee(c_id, e_name, e_desig, e_dept, e_nic, e_bank, e_acc, e_date); st.rerun()
                    if cb2.form_submit_button("Delete", type="primary"): delete_employee(c_id); st.rerun()

# TAB 3: HISTORY
with selected_tabs[2]:
    st.header("Search Past Records")
    h_col1, h_col2 = st.columns(2)
    h_m = h_col1.selectbox("Month", ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], key='hist_m')
    h_y = h_col2.number_input("Year", value=2026, key='hist_y')
    if st.button("Retrieve Records"):
        hist_df = fetch_history(h_m, h_y)
        if not hist_df.empty: st.dataframe(hist_df); st.metric("Total Payout", f"LKR {hist_df['net_salary'].sum():,.2f}")
        else: st.warning("No records found.")

# TAB 4: USER ADMIN (ADMIN ONLY + NEW LOG VIEWER)
if st.session_state['user_role'] == 'Admin':
    with selected_tabs[3]:
        st.header("🔑 User Administration")
        u_col1, u_col2 = st.columns(2)
        with u_col1:
            st.subheader("Add User")
            with st.form("new_user"):
                nu = st.text_input("Username"); np = st.text_input("Password", type="password"); nr = st.selectbox("Role", ["Staff", "Admin"])
                if st.form_submit_button("Create"):
                    if add_user(nu, np, nr): st.success("Created"); st.rerun()
                    else: st.error("Error creating user.")
        with u_col2:
            st.subheader("Existing Users")
            ulist = get_all_users()
            st.dataframe(ulist)
            du = st.selectbox("Delete", ulist['username'].tolist())
            if st.button("Delete User"):
                if delete_user(du): st.rerun()

        # --- NEW: SYSTEM LOG VIEWER ---
        st.divider()
        st.subheader("🛡️ System Integrity Logs")
        if os.path.exists("system.log"):
            with open("system.log", "r") as log_file:
                log_content = log_file.read()
            
            # Download Button
            st.download_button(
                label="📥 Download Full Log File",
                data=log_content,
                file_name="system.log",
                mime="text/plain"
            )
            
            # Preview Window
            with st.expander("View Recent Log Activity"):
                # Show last 2000 characters
                st.text_area("Log Output", log_content[-2000:], height=300)
        else:
            st.info("No logs generated yet.")