from fpdf import FPDF
import io
import zipfile
from datetime import date

class PDFPayslip(FPDF):
    def header(self):
        # We handle header manually in body to control positioning better
        pass
    
    def footer(self):
        pass

def create_single_pdf(row, month, year):
    data = row.to_dict()
    pdf = PDFPayslip()
    pdf.add_page()
    
    # --- 1. HEADER SECTION ---
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 5, 'EMPLOYEE PAY SLIP', ln=True, align='C')
    pdf.ln(2)
    
    pdf.set_font('helvetica', 'B', 14)
    pdf.cell(0, 5, 'Pitch Capital (Pvt) Ltd', ln=True, align='C') # You can change Company Name here
    
    pdf.set_font('helvetica', '', 9)
    pdf.ln(2)
    pdf.cell(0, 4, '540/18/2, Diyawanna Addara, Pitakotte Road, Thalawathugoda, 10116', ln=True, align='C')
    pdf.cell(0, 4, '0112091610', ln=True, align='C')
    
    pdf.ln(5)
    
    # Month / Issued Date
    pdf.set_font('helvetica', '', 10)
    pdf.cell(30, 5, f"Month / Year: {month} {year}", ln=True)
    pdf.cell(30, 5, f"Date Issued: {date.today().strftime('%Y-%m-%d')}", ln=True)
    
    pdf.ln(2)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y()) # Horizontal Line
    pdf.ln(5)
    
    # --- 2. EMPLOYEE DETAILS ---
    pdf.set_font('helvetica', 'B', 11)
    pdf.cell(0, 6, "Employee Details", ln=True)
    pdf.set_font('helvetica', '', 10)
    
    # Helper for key-value layout
    def add_detail(label, value):
        pdf.cell(45, 6, label, 0, 0)
        pdf.cell(5, 6, ":", 0, 0)
        pdf.cell(0, 6, str(value), 0, 1)

    add_detail("Employee Name", data.get('Name', ''))
    add_detail("Employee ID/EPF No", data.get('Employee ID', ''))
    add_detail("Designation", data.get('designation', ''))
    add_detail("Department", data.get('department', ''))
    add_detail("NIC No", data.get('nic', ''))
    add_detail("Bank & Account No", f"{data.get('bank_name', '')} - {data.get('account_no', '')}")
    
    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # --- 3. FINANCIALS TABLE (Earnings | Deductions) ---
    pdf.set_font('helvetica', 'B', 10)
    
    # Table Headers
    # We use explicit XY positioning to create two distinct columns
    start_y = pdf.get_y()
    left_col_x = 10
    right_col_x = 110
    
    pdf.text(left_col_x, start_y, "Earnings")
    pdf.text(right_col_x, start_y, "Deductions")
    
    pdf.ln(8)
    curr_y = pdf.get_y()
    
    # Prepare Data Lists
    earnings = [
        ("Basic Salary", data.get('Basic salary', 0)),
        ("Reimbursement Allowance", data.get('Reimburse allowances', 0)),
        ("Travelling Allowance", data.get('Travelling allowances', 0)),
        ("Overtime", 0.00), # Placeholder if not in excel
        ("Commission", 0.00), # Placeholder
        ("Bonus", 0.00), # Placeholder
        ("Other Earnings", data.get('Other Earnings', 0)),
    ]
    
    deductions = [
        ("No Pay", data.get('Nopay Amount', 0)),
        ("EPF - Employee (8%)", data.get('EPF_Employee_Amt', 0)),
        ("APIT", data.get('Total_Tax', 0)),
        ("Loan", data.get('Loan installment', 0)),
        ("Loan Interest", data.get('Loan interest', 0)),
        ("Salary Advance", data.get('Salary advances', 0)),
        ("Other Deductions", data.get('Others', 0)),
        ("Stamp Duty", data.get('Stamps_Final', 0)),
    ]
    
    pdf.set_font('helvetica', '', 10)
    
    # Calculate Max Rows
    max_rows = max(len(earnings), len(deductions))
    line_height = 6
    
    for i in range(max_rows):
        # LEFT COLUMN (Earnings)
        if i < len(earnings):
            lbl, val = earnings[i]
            pdf.set_xy(left_col_x, curr_y + (i * line_height))
            pdf.cell(60, line_height, lbl, 0, 0)
            pdf.cell(30, line_height, f"{val:,.2f}", 0, 0, 'R')
            
        # RIGHT COLUMN (Deductions)
        if i < len(deductions):
            lbl, val = deductions[i]
            pdf.set_xy(right_col_x, curr_y + (i * line_height))
            pdf.cell(60, line_height, lbl, 0, 0)
            pdf.cell(30, line_height, f"{val:,.2f}", 0, 0, 'R')
            
    # Move Cursor below table
    final_y = curr_y + (max_rows * line_height) + 2
    pdf.set_xy(10, final_y)
    
    # --- TOTALS ---
    pdf.set_font('helvetica', 'B', 10)
    
    # Total Earnings
    pdf.cell(60, 8, "Total Earnings (A)", 0, 0)
    pdf.cell(30, 8, f"{data.get('Gross Salary', 0):,.2f}", 0, 0, 'R')
    
    # Total Deductions (Align Right side)
    pdf.set_xy(right_col_x, final_y)
    pdf.cell(60, 8, "Total Deductions (B)", 0, 0)
    pdf.cell(30, 8, f"{data.get('Total Deduction', 0):,.2f}", 0, 1, 'R')
    
    pdf.ln(5)
    
    # --- NET PAY ---
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(60, 8, "Net Pay", 0, 0)
    pdf.cell(30, 8, f"{data.get('Net Salary', 0):,.2f}", 0, 1, 'R')
    
    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # --- 4. EMPLOYER CONTRIBUTIONS ---
    pdf.set_font('helvetica', 'B', 10)
    pdf.cell(0, 6, "Employer Contributions (For Information)", ln=True)
    pdf.set_font('helvetica', '', 10)
    
    pdf.cell(60, 6, "EPF - Employer (12%)", 0, 0)
    pdf.cell(30, 6, f"{data.get('EPF_Company_Amt', 0):,.2f}", 0, 1, 'R')
    
    pdf.cell(60, 6, "ETF - Employer (3%)", 0, 0)
    pdf.cell(30, 6, f"{data.get('ETF_Company_Amt', 0):,.2f}", 0, 1, 'R')
    
    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(10)
    
    # --- 5. FOOTER / DECLARATION ---
    pdf.set_font('helvetica', 'B', 10)
    pdf.cell(0, 6, "Declaration", ln=True)
    pdf.ln(15) # Space for signature
    
    pdf.cell(30, 6, "Authorized by:", 0, 0)
    pdf.cell(60, 6, "_" * 30, 0, 1)

    return bytes(pdf.output())

def generate_zip_payslips(df, month, year):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        for index, row in df.iterrows():
            pdf_content = create_single_pdf(row, month, year)
            filename = f"{row.get('Employee ID', index)}_{str(row.get('Name', 'Emp')).replace(' ', '_')}.pdf"
            zf.writestr(filename, pdf_content)
    zip_buffer.seek(0)
    return zip_buffer