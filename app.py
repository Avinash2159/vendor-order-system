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
# Use in-memory database
DATABASE_FILE = ":memory:"

def init_database_from_excel(uploaded_file=None):
    """Initialize database from uploaded Excel file or use sample data"""
    conn = sqlite3.connect(DATABASE_FILE)
    
    if uploaded_file is not None:
        # Load from uploaded Excel file
        try:
            # Load all sheets
            cat_df = pd.read_excel(uploaded_file, sheet_name="Categories")
            ven_df = pd.read_excel(uploaded_file, sheet_name="VendorList")
            cam_df = pd.read_excel(uploaded_file, sheet_name="Campus")
            shiv_df = pd.read_excel(uploaded_file, sheet_name="Shiv")
            metro_df = pd.read_excel(uploaded_file, sheet_name="Metro")
            
            # Create tables
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_name TEXT UNIQUE
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vendors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vendor_name TEXT UNIQUE
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS campus (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campus_name TEXT UNIQUE
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS shiv_rates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_name TEXT UNIQUE,
                    rate REAL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metro_rates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_name TEXT UNIQUE,
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
            categories = cat_df.iloc[:, 0].tolist()
            for cat in categories:
                if pd.notna(cat):
                    cursor.execute("INSERT OR IGNORE INTO categories (category_name) VALUES (?)", (str(cat),))
            
            # Vendors
            vendors = ven_df.iloc[:, 0].tolist()
            for vendor in vendors:
                if pd.notna(vendor):
                    cursor.execute("INSERT OR IGNORE INTO vendors (vendor_name) VALUES (?)", (str(vendor),))
            
            # Campus
            campuses = cam_df.iloc[:, 0].tolist()
            for campus in campuses:
                if pd.notna(campus):
                    cursor.execute("INSERT OR IGNORE INTO campus (campus_name) VALUES (?)", (str(campus),))
            
            # Shiv rates
            for _, row in shiv_df.iterrows():
                if len(row) >= 2 and pd.notna(row[0]) and pd.notna(row[1]):
                    cursor.execute("INSERT OR IGNORE INTO shiv_rates (category_name, rate) VALUES (?, ?)", 
                                  (str(row[0]), float(row[1])))
            
            # Metro rates
            for _, row in metro_df.iterrows():
                if len(row) >= 2 and pd.notna(row[0]) and pd.notna(row[1]):
                    cursor.execute("INSERT OR IGNORE INTO metro_rates (category_name, rate) VALUES (?, ?)", 
                                  (str(row[0]), float(row[1])))
            
            conn.commit()
            st.session_state.data_source = "uploaded"
            return conn, True
            
        except Exception as e:
            st.error(f"Error loading Excel file: {str(e)}")
            return init_database_with_sample(conn)
    
    else:
        # Use sample data
        return init_database_with_sample(conn)

def init_database_with_sample(conn):
    """Initialize with sample data"""
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT UNIQUE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_name TEXT UNIQUE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS campus (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campus_name TEXT UNIQUE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shiv_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT UNIQUE,
            rate REAL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metro_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT UNIQUE,
            rate REAL
        )
    ''')
    
    # Check if tables are empty
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        # Insert sample data
        sample_data = [
            ("categories", ["Banner", "Poster", "Standee"]),
            ("vendors", ["Shivnanda", "Metro"]),
            ("campus", ["Main Campus", "North Campus"]),
        ]
        
        for table_name, data_list in sample_data:
            for item in data_list:
                cursor.execute(f"INSERT OR IGNORE INTO {table_name} ({table_name[:-1]}_name) VALUES (?)", (item,))
        
        # Sample rates
        sample_rates = [
            ("shiv_rates", [("Banner", 100), ("Poster", 150), ("Standee", 200)]),
            ("metro_rates", [("Banner", 120), ("Poster", 180), ("Standee", 220)])
        ]
        
        for table_name, rates in sample_rates:
            for category, rate in rates:
                cursor.execute(f"INSERT OR IGNORE INTO {table_name} (category_name, rate) VALUES (?, ?)", 
                              (category, rate))
    
    conn.commit()
    st.session_state.data_source = "sample"
    return conn, False

# ================= SESSION STATE INIT =================
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False
if "db_conn" not in st.session_state:
    st.session_state.db_conn = None
if "data_source" not in st.session_state:
    st.session_state.data_source = "none"

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

# ================= FILE UPLOAD SECTION =================
st.header("📁 Step 1: Upload Your Excel File")

uploaded_file = st.file_uploader(
    "Upload your Digital_Orders.xlsx file",
    type=["xlsx"],
    help="Upload the same Excel file you use on your local machine"
)

if uploaded_file is not None:
    # Initialize database with uploaded file
    db_conn, success = init_database_from_excel(uploaded_file)
    st.session_state.db_conn = db_conn
    st.session_state.data_loaded = success
    
    if success:
        st.success("✅ Excel file uploaded and data loaded successfully!")
    else:
        st.warning("⚠️ Using sample data. Please check your Excel file format.")
else:
    # Initialize with sample data
    if not st.session_state.data_loaded:
        db_conn, _ = init_database_with_sample(sqlite3.connect(DATABASE_FILE))
        st.session_state.db_conn = db_conn
        st.session_state.data_loaded = True
        st.info("ℹ️ Using sample data. Upload your Excel file for actual data.")

# ================= DATA LOADING FUNCTIONS =================
def load_categories():
    """Load categories from database"""
    if st.session_state.db_conn:
        cursor = st.session_state.db_conn.cursor()
        cursor.execute("SELECT category_name FROM categories ORDER BY category_name")
        return [row[0] for row in cursor.fetchall()]
    return []

def load_vendors():
    """Load vendors from database"""
    if st.session_state.db_conn:
        cursor = st.session_state.db_conn.cursor()
        cursor.execute("SELECT vendor_name FROM vendors ORDER BY vendor_name")
        return [row[0] for row in cursor.fetchall()]
    return []

def load_campuses():
    """Load campuses from database"""
    if st.session_state.db_conn:
        cursor = st.session_state.db_conn.cursor()
        cursor.execute("SELECT campus_name FROM campus ORDER BY campus_name")
        return [row[0] for row in cursor.fetchall()]
    return []

def get_rate(category, rate_type):
    """Get rate for category based on rate type"""
    if st.session_state.db_conn:
        cursor = st.session_state.db_conn.cursor()
        table = "shiv_rates" if rate_type == "Shivnanda" else "metro_rates"
        cursor.execute(f"SELECT rate FROM {table} WHERE category_name = ?", (category,))
        result = cursor.fetchone()
        return result[0] if result else 0.0
    return 0.0

# ================= PDF GENERATION =================
def generate_pdf(order_data, order_lines):
    """Generate PDF using FPDF"""
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Digital Order System', 0, 1, 'C')
    pdf.set_font('Arial', '', 12)
    
    # Order details
    details = [
        f"Order ID: {order_data['order_id']}",
        f"Date & Time: {order_data['timestamp']}",
        f"Vendor: {order_data['vendor']}",
        f"Campus: {order_data['campus']}",
        f"Event: {order_data['event']}",
        f"Rate Type: {order_data['rate_type']}",
        f"Order Placed By: {order_data['order_by']}"
    ]
    
    for detail in details:
        pdf.cell(0, 10, detail, 0, 1)
    
    pdf.ln(5)
    
    # Table header
    pdf.set_font('Arial', 'B', 12)
    col_widths = [10, 40, 20, 20, 15, 25, 25, 30]
    headers = ["No", "Category", "H", "W", "Qty", "Area", "Rate", "Amount"]
    
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, header, 1, 0, 'C')
    pdf.ln()
    
    # Table rows
    pdf.set_font('Arial', '', 10)
    grand_total = 0
    
    for idx, line in enumerate(order_lines, 1):
        row = [
            str(idx),
            line["category"],
            f"{line['height']:.1f}",
            f"{line['width']:.1f}",
            str(line["qty"]),
            f"{line['area']:.2f}",
            f"₹{line['rate']:.2f}",
            f"₹{line['amount']:.2f}"
        ]
        
        for i, item in enumerate(row):
            pdf.cell(col_widths[i], 10, item, 1, 0, 'C')
        pdf.ln()
        grand_total += line["amount"]
    
    # Grand total
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(sum(col_widths[:-1]), 10, "Grand Total:", 1, 0, 'R')
    pdf.cell(col_widths[-1], 10, f"₹{grand_total:.2f}", 1, 1, 'C')
    
    pdf.ln(10)
    pdf.set_font('Arial', 'I', 10)
    pdf.cell(0, 10, "Programme Developed by Mr. Avinash Chandra Agarwal", 0, 0, 'C')
    
    # Return PDF as bytes
    return pdf.output(dest='S').encode('latin-1')

# ================= MAIN APP (only show if data loaded) =================
if st.session_state.data_loaded:
    # Load data
    categories = load_categories()
    vendors = load_vendors()
    campuses = load_campuses()
    
    if not categories:
        st.error("No categories found. Please upload a valid Excel file.")
        st.stop()
    
    st.markdown("---")
    st.header("📝 Order Form")
    
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
            st.session_state.order_lines = []
            st.session_state.current_order_id = None
            st.session_state.pdf_data = None
            st.session_state.form_version = str(time.time())
            st.session_state.event = ""
            st.session_state.orderby = ""
            st.rerun()
    
    with col2:
        if st.button("🔄 Reset Form"):
            st.session_state.order_lines = []
            st.session_state.pdf_data = None
            st.session_state.form_version = str(time.time())
            st.rerun()
    
    # Form fields
    vendor = st.selectbox("Select Vendor", vendors, 
                         key="vendor", index=vendors.index(st.session_state.vendor) if st.session_state.vendor in vendors else 0)
    
    campus = st.selectbox("Select Campus", campuses, 
                         key="campus", index=campuses.index(st.session_state.campus) if st.session_state.campus in campuses else 0)
    
    event = st.text_input("Event Name", value=st.session_state.event, key="event")
    order_by = st.text_input("Order Placed By", value=st.session_state.orderby, key="orderby")
    
    # Rate Type
    st.subheader("💲 Rate Configuration")
    rate_type = st.selectbox("Select Rate Type", ["Shivnanda", "Metro"], 
                            key="rate_type", index=0 if st.session_state.rate_type == "Shivnanda" else 1)
    
    st.info(f"Using **{rate_type}** rates")
    
    # Order Categories
    st.subheader("Order Categories")
    
    if not st.session_state.order_lines:
        st.session_state.order_lines = [{
            "category": categories[0] if categories else "",
            "height": 0.0,
            "width": 0.0,
            "qty": 1,
            "area": 0.0,
            "rate": 0.0,
            "amount": 0.0
        }]
    
    # Display order lines
    for i in range(len(st.session_state.order_lines)):
        with st.expander(f"Category #{i+1}", expanded=True):
            line = st.session_state.order_lines[i]
            
            # Safely get category index
            current_category = line.get("category", "")
            cat_idx = 0
            if current_category in categories:
                try:
                    cat_idx = categories.index(current_category)
                except:
                    cat_idx = 0
            
            # Category selection
            category = st.selectbox(
                "Category", 
                categories, 
                key=f"cat_{i}_{st.session_state.form_version}",
                index=cat_idx
            )
            
            # Dimensions and quantity
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
                    step=1, 
                    key=f"q_{i}_{st.session_state.form_version}"
                )
            
            # Calculate values
            area = round(height * width * qty, 2)
            rate = get_rate(category, rate_type)
            amount = round(area * rate, 2)
            
            st.markdown(f"**Area:** {area} sq.ft | **Rate:** ₹{rate:.2f} | **Amount:** ₹{amount:.2f}")
            
            # Update session state
            st.session_state.order_lines[i] = {
                "category": category,
                "height": height,
                "width": width,
                "qty": qty,
                "area": area,
                "rate": rate,
                "amount": amount
            }
            
            # Action buttons
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("➕ Add Another", key=f"add_{i}"):
                    st.session_state.order_lines.append({
                        "category": categories[0] if categories else "",
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
    
    # Save and PDF buttons
    st.markdown("---")
    col_save, col_pdf = st.columns(2)
    
    with col_save:
        if st.button("💾 Save Order", type="primary"):
            if not st.session_state.order_lines or st.session_state.order_lines[0]["amount"] == 0:
                st.error("Please add at least one category with valid dimensions")
            else:
                if not st.session_state.current_order_id:
                    st.session_state.current_order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(100,999)}"
                
                order_summary = {
                    "Order ID": st.session_state.current_order_id,
                    "Date": datetime.now().strftime("%d-%m-%Y %H:%M"),
                    "Vendor": vendor,
                    "Campus": campus,
                    "Event": event,
                    "Order By": order_by,
                    "Rate Type": rate_type,
                    "Total Amount": f"₹{sum(line['amount'] for line in st.session_state.order_lines):.2f}"
                }
                
                st.success(f"✅ Order saved successfully!")
                st.json(order_summary)
    
    with col_pdf:
        if st.button("📄 Generate PDF"):
            if not st.session_state.order_lines or st.session_state.order_lines[0]["amount"] == 0:
                st.error("Please add at least one category with valid dimensions")
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
                    st.error(f"Error generating PDF: {str(e)}")
    
    # Download PDF if available
    if st.session_state.pdf_data:
        st.download_button(
            label="⬇️ Download PDF",
            data=st.session_state.pdf_data,
            file_name=f"{st.session_state.current_order_id or 'order'}.pdf",
            mime="application/pdf"
        )
    
    # Display order summary
    if st.session_state.order_lines and st.session_state.order_lines[0]["amount"] > 0:
        st.markdown("---")
        st.subheader("📋 Order Summary")
        
        total_amount = sum(line["amount"] for line in st.session_state.order_lines)
        
        summary_data = []
        for line in st.session_state.order_lines:
            summary_data.append({
                "Category": line["category"],
                "Height": f"{line['height']:.1f} ft",
                "Width": f"{line['width']:.1f} ft",
                "Qty": line["qty"],
                "Area": f"{line['area']:.2f} sq.ft",
                "Rate": f"₹{line['rate']:.2f}",
                "Amount": f"₹{line['amount']:.2f}"
            })
        
        st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
        st.metric("Grand Total", f"₹{total_amount:.2f}")

# Cleanup on app end
import atexit
@atexit.register
def cleanup():
    if st.session_state.db_conn:
        st.session_state.db_conn.close()
