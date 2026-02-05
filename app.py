import streamlit as st
import pandas as pd
import io
from processor import process_payroll_data
from database import init_db, save_payroll_to_db, fetch_history
from pdf_gen import generate_zip_payslips, create_single_pdf

# 1. Initialize Database
init_db()

# 2. Page Configuration
st.set_page_config(page_title="SL Property Payroll Engine", layout="wide", page_icon="🏢")

# Custom CSS to make the UI look professional
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    .stDownloadButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #28a745; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏢 Property Company Payroll System")
st.markdown("---")

# --- SIDEBAR: GLOBAL VARIABLES ---
st.sidebar.header("⚙️ Global Settings")

# Date Selection
sel_month = st.sidebar.selectbox("Processing Month", 
    ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
sel_year = st.sidebar.number_input("Processing Year", value=2026, step=1)

# Calculation Variables
st.sidebar.subheader("Logic Constants")
working_days = st.sidebar.number_input("Standard Working Days", value=30)
stamps_fee = st.sidebar.number_input("Standard Stamp Fee (LKR)", value=25.0)

st.sidebar.subheader("Statutory Rates (%)")
epf_emp = st.sidebar.slider("EPF Employee Contribution", 0, 15, 8) / 100
epf_co = st.sidebar.slider("EPF Employer Contribution", 0, 20, 12) / 100
etf_co = st.sidebar.slider("ETF Employer Contribution", 0, 10, 3) / 100

config = {
    'working_days': working_days,
    'stamps_fee': stamps_fee,
    'epf_emp_rate': epf_emp,
    'epf_co_rate': epf_co,
    'etf_co_rate': etf_co
}

# --- MAIN INTERFACE TABS ---
tab1, tab2 = st.tabs(["🚀 Payroll Processing", "📜 Salary History"])

with tab1:
    st.subheader(f"Step 1: Upload Data for {sel_month} {sel_year}")
    uploaded_file = st.file_uploader("Upload Finance/HR Excel Sheet", type=['xlsx'])
    
    if uploaded_file:
        df_input = pd.read_excel(uploaded_file)
        st.write("### Data Preview (First 5 Rows)")
        st.dataframe(df_input.head())

        # PROCESS BUTTON
        if st.button("Calculate Payroll for All Employees"):
            try:
                # Run the logic from processor.py
                df_result = process_payroll_data(df_input, config)
                # Save result to session state so it persists during downloads
                st.session_state['result'] = df_result
                st.success(f"Calculations complete for {len(df_result)} employees!")
            except Exception as e:
                st.error(f"Error in calculation: {e}")

        # ACTIONS SECTION (Shown only after calculation)
        if 'result' in st.session_state:
            df_final = st.session_state['result']
            
            st.markdown("---")
            st.subheader("Step 2: Review & Download")
            
            # Key Summary Metrics
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Net Payout", f"LKR {df_final['Net Salary'].sum():,.2f}")
            m2.metric("Company EPF (12%)", f"LKR {df_final['EPF_Company_Amt'].sum():,.2f}")
            m3.metric("Company ETF (3%)", f"LKR {df_final['ETF_Company_Amt'].sum():,.2f}")

            st.dataframe(df_final)

            # Download Buttons
            st.write("### 📥 Bulk Exports")
            col_excel, col_zip, col_db = st.columns(3)

            # 1. Download Processed Excel
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                df_final.to_excel(writer, index=False)
            col_excel.download_button(
                "📊 Download Result Excel", 
                excel_buffer.getvalue(), 
                f"Payroll_Summary_{sel_month}_{sel_year}.xlsx"
            )

            # 2. Download ZIP of Individual PDFs
            # This uses the new zip function in pdf_gen.py
            with st.spinner("Generating individual PDFs..."):
                zip_file = generate_zip_payslips(df_final, sel_month, sel_year)
                col_zip.download_button(
                    label="📦 Download All Payslips (ZIP)",
                    data=zip_file,
                    file_name=f"Payslips_{sel_month}_{sel_year}.zip",
                    mime="application/zip"
                )

            # 3. Save to Database History
            if col_db.button("💾 Save to History DB"):
                save_payroll_to_db(df_final, sel_month, sel_year)
                st.success("Successfully archived to Database!")

            # Individual Employee Section
            st.markdown("---")
            st.subheader("👤 Individual Employee Quick-View")
            for i, row in df_final.iterrows():
                with st.expander(f"{row['Employee ID']} - {row['Name']}"):
                    c_left, c_right = st.columns([3, 1])
                    c_left.write(f"**Gross:** {row['Gross Salary']:,.2f} | **Deductions:** {row['Total Deduction']:,.2f} | **Net:** {row['Net Salary']:,.2f}")
                    
                    # Generate single PDF for this specific row
                    single_pdf = create_single_pdf(row, sel_month, sel_year)
                    c_right.download_button(
                        "Download PDF",
                        data=single_pdf,
                        file_name=f"{row['Employee ID']}_{row['Name']}.pdf",
                        mime="application/pdf",
                        key=f"btn_{row['Employee ID']}_{i}"
                    )

with tab2:
    st.header("Search Past Records")
    h_col1, h_col2 = st.columns(2)
    h_month = h_col1.selectbox("Month", ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], key='hist_m')
    h_year = h_col2.number_input("Year", value=2026, key='hist_y')
    
    if st.button("Retrieve Historical Data"):
        hist_df = fetch_history(h_month, h_year)
        if not hist_df.empty:
            st.write(f"### Historical Records for {h_month} {h_year}")
            st.dataframe(hist_df)
            st.metric("Month Total Payout", f"LKR {hist_df['net_salary'].sum():,.2f}")
        else:
            st.warning("No records found in the database for the selected period.")