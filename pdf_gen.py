# from fpdf import FPDF
# import io
# import zipfile

# class PDFPayslip(FPDF):
#     def header(self):
#         # Header setup
#         self.set_font('helvetica', 'B', 15)
#         self.cell(0, 10, 'SRI LANKA TOURISM PROPERTY CO.', ln=True, align='C')
#         self.set_font('helvetica', 'I', 10)
#         self.cell(0, 10, 'Monthly Salary Statement', ln=True, align='C')
#         self.ln(5)
#         self.line(10, self.get_y(), 200, self.get_y())
#         self.ln(10)

# def create_single_pdf(row, month, year):
#     # Convert row to dict for easier .get() access
#     data = row.to_dict()
    
#     pdf = PDFPayslip()
#     pdf.add_page()
    
#     # Employee Info
#     pdf.set_font('helvetica', 'B', 11)
#     pdf.cell(100, 8, f"Employee Name: {data.get('Name', 'N/A')}")
#     pdf.cell(0, 8, f"ID: {data.get('Employee ID', 'N/A')}", ln=True, align='R')
#     pdf.cell(100, 8, f"Period: {month} {year}")
#     pdf.ln(12)

#     # Table Setup
#     pdf.set_fill_color(240, 240, 240)
#     pdf.set_font('helvetica', 'B', 10)
#     pdf.cell(95, 8, "Earnings", 1, 0, 'C', True)
#     pdf.cell(95, 8, "Deductions", 1, 1, 'C', True)
    
#     pdf.set_font('helvetica', '', 9)
    
#     # Prepare Table Data
#     earnings = [
#         ("Basic Salary", data.get('Basic salary', 0)),
#         ("Reimburse Allowances", data.get('Reimburse allowances', 0)),
#         ("Travelling Allowances", data.get('Travelling allowances', 0)),
#         ("Gross Salary", data.get('Gross Salary', 0)),
#     ]
    
#     deductions = [
#         ("Nopay Amount", data.get('Nopay Amount', 0)),
#         ("Salary Adjustment", data.get('Salary adjustment', 0)),
#         ("EPF (Employee 8%)", data.get('EPF_Employee_Amt', 0)),
#         ("Govt Tax (Rate+APIT)", data.get('Total_Tax', 0)),
#         ("Salary Advances", data.get('Salary advances', 0)),
#         ("Loan (Inst + Int)", data.get('Loan installment', 0) + data.get('Loan interest', 0)),
#         ("Stamps Fee", data.get('Stamps_Final', 0)),
#         ("Others", data.get('Others', 0)),
#     ]

#     max_rows = max(len(earnings), len(deductions))
#     for i in range(max_rows):
#         # Left side
#         if i < len(earnings):
#             pdf.cell(60, 7, earnings[i][0], 'L')
#             pdf.cell(35, 7, f"{earnings[i][1]:,.2f}", 'R')
#         else:
#             pdf.cell(95, 7, "", 'LR')
            
#         # Right side
#         if i < len(deductions):
#             pdf.cell(60, 7, deductions[i][0], 'L')
#             pdf.cell(35, 7, f"{deductions[i][1]:,.2f}", 'R', 1)
#         else:
#             pdf.cell(95, 7, "", 'R', 1)

#     # Summary Section
#     pdf.ln(5)
#     pdf.set_font('helvetica', 'B', 10)
#     pdf.cell(95, 10, f"TOTAL EARNINGS:  {data.get('Gross Salary', 0):,.2f}", 1, 0, 'R')
#     pdf.cell(95, 10, f"TOTAL DEDUCTIONS:  {data.get('Total Deduction', 0):,.2f}", 1, 1, 'R')
    
#     pdf.ln(2)
#     pdf.set_fill_color(220, 255, 220)
#     pdf.cell(0, 12, f"NET SALARY PAYABLE: LKR {data.get('Net Salary', 0):,.2f}", 1, 1, 'C', True)
    
#     pdf.ln(10)
#     pdf.set_font('helvetica', 'I', 8)
#     pdf.cell(0, 5, f"EPF Company (12%): {data.get('EPF_Company_Amt', 0):,.2f}", ln=True)
#     pdf.cell(0, 5, f"ETF Company (3%): {data.get('ETF_Company_Amt', 0):,.2f}", ln=True)
    
#     return pdf.output()

# def generate_zip_payslips(df, month, year):
#     zip_buffer = io.BytesIO()
#     with zipfile.ZipFile(zip_buffer, "w") as zf:
#         for index, row in df.iterrows():
#             pdf_content = create_single_pdf(row, month, year)
#             filename = f"{row.get('Employee ID', index)}_{str(row.get('Name', 'Emp')).replace(' ', '_')}.pdf"
#             zf.writestr(filename, pdf_content)
#     zip_buffer.seek(0)
#     return zip_buffer

from fpdf import FPDF
import io
import zipfile

class PDFPayslip(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 15)
        self.cell(0, 10, 'SRI LANKA TOURISM PROPERTY CO.', ln=True, align='C')
        self.set_font('helvetica', 'I', 10)
        self.cell(0, 10, 'Monthly Salary Statement', ln=True, align='C')
        self.ln(5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(10)

def create_single_pdf(row, month, year):

    data = row.to_dict()

    pdf = PDFPayslip()
    pdf.add_page()

    pdf.set_font('helvetica', 'B', 11)
    pdf.cell(100, 8, f"Employee Name: {data.get('Name', 'N/A')}")
    pdf.cell(0, 8, f"ID: {data.get('Employee ID', 'N/A')}", ln=True, align='R')
    pdf.cell(100, 8, f"Period: {month} {year}")
    pdf.ln(12)

    pdf.set_fill_color(240, 240, 240)
    pdf.set_font('helvetica', 'B', 10)
    pdf.cell(95, 8, "Earnings", 1, 0, 'C', True)
    pdf.cell(95, 8, "Deductions", 1, 1, 'C', True)

    pdf.set_font('helvetica', '', 9)

    earnings = [
        ("Basic Salary", data.get('Basic salary', 0)),
        ("Reimburse Allowances", data.get('Reimburse allowances', 0)),
        ("Travelling Allowances", data.get('Travelling allowances', 0)),
        ("Gross Salary", data.get('Gross Salary', 0)),
    ]

    deductions = [
        ("Nopay Amount", data.get('Nopay Amount', 0)),
        ("Salary Adjustment", data.get('Salary adjustment', 0)),
        ("EPF (Employee 8%)", data.get('EPF_Employee_Amt', 0)),
        ("Govt Tax (Rate+APIT)", data.get('Total_Tax', 0)),
        ("Salary Advances", data.get('Salary advances', 0)),
        ("Loan (Inst + Int)", data.get('Loan installment', 0) + data.get('Loan interest', 0)),
        ("Stamps Fee", data.get('Stamps_Final', 0)),
        ("Others", data.get('Others', 0)),
    ]

    max_rows = max(len(earnings), len(deductions))

    for i in range(max_rows):
        if i < len(earnings):
            pdf.cell(60, 7, earnings[i][0], 'L')
            pdf.cell(35, 7, f"{earnings[i][1]:,.2f}", 'R')
        else:
            pdf.cell(95, 7, "", 'LR')

        if i < len(deductions):
            pdf.cell(60, 7, deductions[i][0], 'L')
            pdf.cell(35, 7, f"{deductions[i][1]:,.2f}", 'R', 1)
        else:
            pdf.cell(95, 7, "", 'R', 1)

    pdf.ln(5)
    pdf.set_font('helvetica', 'B', 10)
    pdf.cell(95, 10, f"TOTAL EARNINGS: {data.get('Gross Salary', 0):,.2f}", 1, 0, 'R')
    pdf.cell(95, 10, f"TOTAL DEDUCTIONS: {data.get('Total Deduction', 0):,.2f}", 1, 1, 'R')

    pdf.ln(2)
    pdf.set_fill_color(220, 255, 220)
    pdf.cell(0, 12, f"NET SALARY PAYABLE: LKR {data.get('Net Salary', 0):,.2f}", 1, 1, 'C', True)

    pdf.ln(10)
    pdf.set_font('helvetica', 'I', 8)
    pdf.cell(0, 5, f"EPF Company (12%): {data.get('EPF_Company_Amt', 0):,.2f}", ln=True)
    pdf.cell(0, 5, f"ETF Company (3%): {data.get('ETF_Company_Amt', 0):,.2f}", ln=True)

    # ✅ CRITICAL FIX — convert bytearray → bytes
    return bytes(pdf.output(dest="S"))


def generate_zip_payslips(df, month, year):

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for index, row in df.iterrows():
            pdf_bytes = create_single_pdf(row, month, year)

            filename = f"{row.get('Employee ID', index)}_{str(row.get('Name', 'Emp')).replace(' ', '_')}.pdf"

            zf.writestr(filename, pdf_bytes)

    zip_buffer.seek(0)
    return zip_buffer
