# 🏢 Pitch Capital Payroll System

A robust, secure, and automated payroll management system built with Python and Streamlit. This application handles the end-to-end payroll process: from Excel data ingestion and tax calculation to PDF payslip generation and historical archiving.

![Status](https://img.shields.io/badge/Status-Production%20Ready-success)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Database](https://img.shields.io/badge/Database-SQLite-lightgrey)

## 🌟 Key Features

### 🚀 Payroll Processing
- **Excel Integration:** Upload raw financial data (Excel) and automatically merge it with the stored Employee Database.
- **Smart Calculation:** Auto-calculates EPF (8%/12%), ETF (3%), APIT Tax, and Stamp Fees based on configurable logic.
- **Bulk & Individual Exports:** Generate a ZIP file of all payslips or download specific PDFs individually.

### 👥 Employee Management
- **CRUD Operations:** Add, Edit, and Delete employee records via a GUI.
- **Master Data:** Stores static details (NIC, Bank Account, Joined Date) so you don't need to re-type them every month.

### 🔒 Security & Admin
- **Role-Based Access Control (RBAC):** Distinct `Admin` and `Staff` roles.
- **Secure Authentication:** SHA-256 password hashing.
- **Audit History:** Archives every processed month into a searchable database.

---

## 🛠️ Installation & Setup

### 1. Prerequisites
Ensure you have [Python](https://www.python.org/) installed.

### 2. Clone/Download
Download the project files to your local machine.

### 3. Install Dependencies
Open your terminal in the project folder and run:
```bash
pip install streamlit pandas reportlab xlsxwriter


4. Run Application

streamlit run app.py


├── app.py              # Main Application Entry Point (UI & Routing)
├── processor.py        # Logic: Math, Tax Formulas, Data Merging
├── database.py         # Data Layer: SQLite connection, CRUD functions
├── pdf_gen.py          # Reporting: Generates PDF Payslips
├── logo.png            # Company Branding (Sidebar Image)
├── property_payroll.db # (Auto-generated) Local Database file
└── README.md           # Documentation



⚙️ How to Use
Login: Use the credentials above.

Configuration: Use the Sidebar to set the Month, Year, and Statutory Rates (EPF/ETF).

Upload: Go to "Payroll Processing" and upload your monthly finance Excel sheet.

Calculate: Click "Calculate Payroll". Review the "Data Preview" and "Metrics".

Distribute: Download the ZIP of payslips.

Archive: Click "Save to History Database" to store the records permanently.

📐 Architecture Overview
The system utilizes a Modular Monolithic design:

Frontend: Streamlit handles the session state and UI rendering.

Backend Logic: processor.py standardizes column names and executes financial math.

Database: SQLite acts as the persistent storage, featuring auto-migration scripts to prevent schema errors during updates.