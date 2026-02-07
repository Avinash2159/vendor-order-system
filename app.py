import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os
import random
import time
import sqlite3
import io

st.set_page_config(page_title="Digital Order System", layout="centered")
st.title("📊 Digital Order System")

# ================= DATABASE SETUP =================
DATABASE_FILE = ":memory:"

def init_database_from_excel(uploaded_file=None):
    """Initialize database from uploaded Excel file"""
    conn = sqlite3.connect(DATABASE_FILE)
    
    if uploaded_file is not None:
        try:
            # Load all sheets
            cat_df = pd.read_excel(uploaded_file, sheet_name="Categories")
            ven_df = pd.read_excel(uploaded_file, sheet_name="VendorList")
            cam_df = pd.read_excel(uploaded_file, sheet_name="Campus")
            shiv_df = pd.read_excel(uploaded_file, sheet_name="Shiv")
            metro_df = pd.read_excel(uploaded_file, sheet_name="Metro")
            
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vendors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS campus (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS shiv_rates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT UNIQUE,
                    rate REAL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metro_rates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT UNIQUE,
                    rate REAL
                )
            ''')
            
            # Clear existing data
            cursor.execute("DELETE FROM categories")
            cursor.execute("DELETE FROM vendors")
            cursor.execute("DELETE FROM campus")
            cursor.execute("DELETE FROM shiv_rates")
            cursor.execute("DELETE FROM metro_rates")
            
            # Insert actual data
            # Categories
            categories = cat_df.iloc[:, 0].dropna().astype(str).tolist()
            for cat in categories:
                cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (cat,))
            
            # Vendors
            vendors = ven_df.iloc[:, 0].dropna().astype(str).tolist()
            for vendor in vendors:
                cursor.execute("INSERT OR IGNORE INTO vendors (name) VALUES (?)", (vendor,))
            
            # Campus
            campuses = cam_df.iloc[:, 0].dropna().astype(str).tolist()
            for campus in campuses:
                cursor.execute("INSERT OR IGNORE INTO campus (name) VALUES (?)", (campus,))
            
            # Shiv rates
            for _, row in shiv_df.iterrows():
                if len(row) >= 2 and pd.notna(row[0]) and pd.notna(row[1]):
                    cursor.execute("INSERT OR IGNORE INTO shiv_rates (category, rate) VALUES (?, ?)", 
                                  (str(row[0]), float(row[1])))
            
            # Metro rates
            for _, row in metro_df.iterrows():
                if len(row) >= 2 and pd.notna(row[0]) and pd.notna(row[1]):
                    cursor.execute("INSERT OR IGNORE INTO metro_rates (category, rate) VALUES (?, ?)", 
                                  (str(row[0]), float(row[1])))
            
            conn.commit()
            return conn, True, "Excel file data"
            
        except Exception as e:
            st.error(f"Error loading Excel: {str(e)}")
            conn.close()
            return init_database_with_sample()
    
    else:
        return init_database_with_sample()

def init_database_with_sample():
    """Initialize with sample data"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Create tables with consistent column names
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS campus (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shiv_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT UNIQUE,
            rate REAL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metro_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT UNIQUE,
            rate REAL
        )
    ''')
    
    # Clear any existing data
    cursor.execute("DELETE FROM categories")
    cursor.execute("DELETE FROM vendors")
    cursor.execute("DELETE FROM campus")
    cursor.execute("DELETE FROM shiv_rates")
    cursor.execute("DELETE FROM metro_rates")
    
    # Insert sample data
    categories = ["Banner", "Poster", "Standee", "Hoarding"]
    vendors = ["Shivnanda", "Metro"]
    campuses = ["Main Campus", "North Campus"]
    
    for cat in categories:
        cursor.execute("INSERT INTO categories (name) VALUES (?)", (cat,))
    
    for vendor in vendors:
        cursor.execute("INSERT INTO vendors (name) VALUES (?)", (vendor,))
    
    for campus in campuses:
        cursor.execute("INSERT INTO campus (name) VALUES (?)", (campus,))
    
    # Sample rates
    sample_rates = [
        ("Banner", 100.0, 120.0),
        ("Poster", 150.0, 180.0),
        ("Standee", 200.0, 220.0),
        ("Hoarding", 300.0, 350.0)
    ]
    
    for category, shiv_rate, metro_rate in sample_rates:
        cursor.execute("INSERT INTO shiv_rates (category, rate) VALUES (?, ?)", (category, shiv_rate))
        cursor.execute("INSERT INTO metro_rates (category, rate) VALUES (?, ?)", (category, metro_rate))
    
    conn.commit()
    return conn, False, "Sample data"

# ================= SESSION STATE =================
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False
if "db_conn" not in st.session_state:
    st.session_state.db_conn = None
if "data_source" not in st.session_state:
    st.session_state.data_source = ""

if "order_lines" not in st.session_state:
    st.session_state.order_lines = []
if "current_order_id" not in st.session_state:
    st.session_state.current_order_id = None
if "pdf_data" not in st.session_state:
    st.session_state.pdf_data = None
if "form_version" not in st.session_state:
    st.session_state.form_version = str(time.time())
if "rate_type" not in st.session_state:
    st.session_state.rate_type = "Shivnanda"

# ================= FILE UPLOAD =================
st.header("📁 Step 1: Upload Excel File (Optional)")

uploaded_file = st.file_uploader(
    "Upload Digital_Orders.xlsx (same as local file)",
    type=["xlsx"],
    help="Upload to use your actual data. Otherwise, sample data will be used."
)

if uploaded_file is not None:
    # Initialize with uploaded file
    db_conn, success, source = init_database_from_excel(uploaded_file)
    st.session_state.db_conn = db_conn
    st.session_state.data_loaded = True
    st.session_state.data_source = source
    
    if success:
        st.success(f"✅ {source} loaded successfully!")
    else:
        st.warning("⚠️ Using sample data instead.")
else:
    # Initialize with sample data
    if not st.session_state.data_loaded:
        db_conn, _, source = init_database_with_sample()
        st.session_state.db_conn = db_conn
        st.session_state.data_loaded = True
        st.session_state.data_source = source
        st.info(f"ℹ️ Using {source}. Upload your Excel file for actual data.")

# ================= DATA LOADING =================
def load_categories():
    """Load categories from database"""
    if st.session_state.db_conn:
        cursor = st.session_state.db_conn.cursor()
        cursor.execute("SELECT name FROM categories ORDER BY name")
        return [row[0] for row in cursor.fetchall()]
    return []

def load_vendors():
    """Load vendors from database"""
    if st.session_state.db_conn:
        cursor = st.session_state.db_conn.cursor()
        cursor.execute("SELECT name FROM vendors ORDER BY name")
        return [row[0] for row in cursor.fetchall()]
    return []

def load_campuses():
    """Load campuses from database"""
    if st.session_state.db_conn:
        cursor = st.session_state.db_conn.cursor()
        cursor.execute("SELECT name FROM campus ORDER BY name")
        return [row[0] for row in cursor.fetchall()]
    return []

def get_rate(category, rate_type):
    """Get rate for category"""
    if st.session_state.db_conn:
        cursor = st.session_state.db_conn.cursor()
        table = "shiv_rates" if rate_type == "Shivnanda" else "metro_rates"
        cursor.execute(f"SELECT rate FROM {table} WHERE category = ?", (category,))
        result = cursor.fetchone()
        return float(result[0]) if result else 0.0
    return 0.0

# ================= PDF GENERATION (FIXED ENCODING) =================
class UnicodePDF(FPDF):
    """PDF class that supports Unicode characters"""
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Digital Order System', 0, 1, 'C')
        self.ln(5)

def generate_pdf(order_data, order_lines):
    """Generate PDF with proper encoding"""
    pdf = UnicodePDF()
    pdf.add_page()
    
    # Set font
    pdf.set_font('Arial', '', 12)
    
    # Order details (without ₹ symbol to avoid encoding issues)
    details = [
        f"Order ID: {order_data['order_id']}",
        f"Date & Time: {order_data['timestamp']}",
        f"Vendor: {order_data['vendor']}",
        f"Campus: {order_data['campus']}",
        f"Event: {order_data['event']}",
        f"Rate Type: {order_data['rate_type']}",
        f"Order By: {order_data['order_by']}"
    ]
    
    for detail in details:
        pdf.cell(0, 10, detail, 0, 1)
    
    pdf.ln(5)
    
    # Table header
    pdf.set_font('Arial', 'B', 12)
    col_widths = [10, 40, 20, 20, 15, 25, 25, 30]
    headers = ["No", "Category", "H(ft)", "W(ft)", "Qty", "Area", "Rate", "Amount"]
    
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, header, 1, 0, 'C')
    pdf.ln()
    
    # Table rows
    pdf.set_font('Arial', '', 10)
    grand_total = 0
    
    for idx, line in enumerate(order_lines, 1):
        # Format numbers without ₹ symbol
        row = [
            str(idx),
            str(line["category"]),
            f"{line['height']:.1f}",
            f"{line['width']:.1f}",
            str(line["qty"]),
            f"{line['area']:.2f}",
            f"{line['rate']:.2f}",
            f"{line['amount']:.2f}"
        ]
        
        for i, item in enumerate(row):
            pdf.cell(col_widths[i], 10, item, 1, 0, 'C')
        pdf.ln()
        grand_total += line["amount"]
    
    # Grand total
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(sum(col_widths[:-1]), 10, "Grand Total: Rs.", 1, 0, 'R')
    pdf.cell(col_widths[-1], 10, f"{grand_total:.2f}", 1, 1, 'C')
    
    pdf.ln(10)
    pdf.set_font('Arial', 'I', 10)
    pdf.cell(0, 10, "Programme Developed by Mr. Avinash Chandra Agarwal", 0, 0, 'C')
    
    # Return PDF bytes
    return pdf.output(dest='S').encode('latin-1')

# ================= MAIN APP =================
if st.session_state.data_loaded:
    # Load data
    categories = load_categories()
    vendors = load_vendors()
    campuses = load_campuses()
    
    if not categories:
        st.error("No data loaded. Please refresh and upload Excel file.")
        st.stop()
    
    st.markdown("---")
    st.header("📝 Order Form")
    st.info(f"Data Source: {st.session_state.data_source}")
    
    # Initialize form values
    if "vendor" not in st.session_state:
        st.session_state.vendor = vendors[0] if vendors else ""
    if "campus" not in st.session_state:
        st.session_state.campus = campuses[0] if campuses else ""
    if "event" not in st.session_state:
        st.session_state.event = ""
    if "orderby" not in st.session_state:
        st.session_state.orderby = ""
    
    # Control buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🆕 New Order"):
            st.session_state.order_lines = [{
                "category": categories[0],
                "height": 0.0,
                "width": 0.0,
                "qty": 1,
                "area": 0.0,
                "rate": 0.0,
                "amount": 0.0
            }]
            st.session_state.current_order_id = None
            st.session_state.pdf_data = None
            st.session_state.form_version = str(time.time())
            st.session_state.event = ""
            st.session_state.orderby = ""
            st.rerun()
    
    with col2:
        if st.button("🔄 Reset Current"):
            if st.session_state.order_lines:
                st.session_state.order_lines = [{
                    "category": categories[0],
                    "height": 0.0,
                    "width": 0.0,
                    "qty": 1,
                    "area": 0.0,
                    "rate": 0.0,
                    "amount": 0.0
                }]
                st.session_state.form_version = str(time.time())
                st.rerun()
    
    # Form fields
    vendor = st.selectbox("Select Vendor", vendors, 
                         key="vendor", index=0)
    campus = st.selectbox("Select Campus", campuses, 
                         key="campus", index=0)
    event = st.text_input("Event Name", key="event")
    order_by = st.text_input("Order Placed By", key="orderby")
    
    # Rate Type
    st.subheader("💲 Rate Configuration")
    rate_type = st.selectbox("Select Rate Type", ["Shivnanda", "Metro"], 
                            key="rate_type")
    
    # Order Categories
    st.subheader("Order Categories")
    
    if not st.session_state.order_lines:
        st.session_state.order_lines = [{
            "category": categories[0],
            "height": 0.0,
            "width": 0.0,
            "qty": 1,
            "area": 0.0,
            "rate": 0.0,
            "amount": 0.0
        }]
    
    # Display each category line
    for i in range(len(st.session_state.order_lines)):
        with st.expander(f"Category #{i+1}", expanded=i==0):
            line = st.session_state.order_lines[i]
            
            # Get current category index safely
            current_cat = line.get("category", categories[0])
            cat_index = categories.index(current_cat) if current_cat in categories else 0
            
            # Category selection
            category = st.selectbox(
                "Category", 
                categories, 
                key=f"cat_{i}_{st.session_state.form_version}",
                index=cat_index
            )
            
            # Dimensions
            col1, col2, col3 = st.columns(3)
            with col1:
                height = st.number_input(
                    "Height (ft)", 
                    value=float(line.get("height", 0.0)), 
                    min_value=0.0, 
                    step=0.1,
                    key=f"h_{i}_{st.session_state.form_version}"
                )
            with col2:
                width = st.number_input(
                    "Width (ft)", 
                    value=float(line.get("width", 0.0)), 
                    min_value=0.0, 
                    step=0.1,
                    key=f"w_{i}_{st.session_state.form_version}"
                )
            with col3:
                qty = st.number_input(
                    "Quantity", 
                    value=int(line.get("qty", 1)), 
                    min_value=1,
                    key=f"q_{i}_{st.session_state.form_version}"
                )
            
            # Calculate
            area = round(height * width * qty, 2)
            rate = get_rate(category, rate_type)
            amount = round(area * rate, 2)
            
            st.markdown(f"**Area:** {area} sq.ft | **Rate:** Rs.{rate:.2f} | **Amount:** Rs.{amount:.2f}")
            
            # Update session
            st.session_state.order_lines[i] = {
                "category": category,
                "height": height,
                "width": width,
                "qty": qty,
                "area": area,
                "rate": rate,
                "amount": amount
            }
            
            # Buttons
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("➕ Add Category", key=f"add_{i}"):
                    st.session_state.order_lines.append({
                        "category": categories[0],
                        "height": 0.0,
                        "width": 0.0,
                        "qty": 1,
                        "area": 0.0,
                        "rate": 0.0,
                        "amount": 0.0
                    })
                    st.rerun()
            
            with col_btn2:
                if len(st.session_state.order_lines) > 1 and st.button("🗑 Remove", key=f"del_{i}"):
                    st.session_state.order_lines.pop(i)
                    st.rerun()
    
    # Action buttons
    st.markdown("---")
    col_save, col_pdf = st.columns(2)
    
    with col_save:
        if st.button("💾 Save Order", type="primary", use_container_width=True):
            valid_order = any(line["amount"] > 0 for line in st.session_state.order_lines)
            
            if not valid_order:
                st.error("Please enter valid dimensions for at least one category")
            else:
                if not st.session_state.current_order_id:
                    st.session_state.current_order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(100,999)}"
                
                total = sum(line["amount"] for line in st.session_state.order_lines)
                st.success(f"Order {st.session_state.current_order_id} saved!")
                st.info(f"Total Amount: Rs.{total:.2f}")
    
    with col_pdf:
        if st.button("📄 Generate PDF", type="primary", use_container_width=True):
            valid_order = any(line["amount"] > 0 for line in st.session_state.order_lines)
            
            if not valid_order:
                st.error("Please enter valid dimensions first")
            else:
                order_id = st.session_state.current_order_id or f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(100,999)}"
                
                order_data = {
                    "order_id": order_id,
                    "timestamp": datetime.now().strftime("%d-%m-%Y %H:%M"),
                    "vendor": vendor,
                    "campus": campus,
                    "event": event,
                    "rate_type": rate_type,
                    "order_by": order_by
                }
                
                try:
                    pdf_bytes = generate_pdf(order_data, st.session_state.order_lines)
                    st.session_state.pdf_data = pdf_bytes
                    st.session_state.current_order_id = order_id
                    st.success("✅ PDF generated successfully!")
                except Exception as e:
                    st.error(f"PDF Error: {str(e)[:100]}...")
    
    # Download PDF
    if st.session_state.pdf_data:
        st.download_button(
            label="⬇️ Download PDF",
            data=st.session_state.pdf_data,
            file_name=f"{st.session_state.current_order_id}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    
    # Order Summary
    if st.session_state.order_lines:
        total = sum(line["amount"] for line in st.session_state.order_lines)
        if total > 0:
            st.markdown("---")
            st.subheader("📋 Order Summary")
            
            summary_data = []
            for line in st.session_state.order_lines:
                if line["amount"] > 0:
                    summary_data.append({
                        "Category": line["category"],
                        "Size": f"{line['height']:.1f}x{line['width']:.1f} ft",
                        "Qty": line["qty"],
                        "Area": f"{line['area']:.2f} sq.ft",
                        "Rate": f"Rs.{line['rate']:.2f}",
                        "Amount": f"Rs.{line['amount']:.2f}"
                    })
            
            if summary_data:
                st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
                st.metric("Grand Total", f"Rs.{total:.2f}")

# Cleanup
import atexit
@atexit.register
def cleanup():
    if 'db_conn' in st.session_state and st.session_state.db_conn:
        try:
            st.session_state.db_conn.close()
        except:
            pass
