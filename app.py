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
# Use in-memory database for Streamlit Cloud
DATABASE_FILE = ":memory:"

def init_database():
    """Initialize database with sample data"""
    conn = sqlite3.connect(DATABASE_FILE)
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
    
    # Insert sample data if tables are empty
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        # Sample data
        categories = ["Banner", "Poster", "Standee", "Hoarding", "Flex", "Vinyl", "Canvas"]
        vendors = ["Shivnanda", "Metro", "Local Printer", "Digital Press"]
        campuses = ["Main Campus", "North Campus", "South Campus", "East Campus"]
        
        for category in categories:
            cursor.execute("INSERT OR IGNORE INTO categories (category_name) VALUES (?)", (category,))
        
        for vendor in vendors:
            cursor.execute("INSERT OR IGNORE INTO vendors (vendor_name) VALUES (?)", (vendor,))
        
        for campus in campuses:
            cursor.execute("INSERT OR IGNORE INTO campus (campus_name) VALUES (?)", (campus,))
        
        # Sample rates
        shiv_rates = [
            ("Banner", 100.0), ("Poster", 150.0), ("Standee", 200.0),
            ("Hoarding", 300.0), ("Flex", 80.0), ("Vinyl", 120.0), ("Canvas", 250.0)
        ]
        
        metro_rates = [
            ("Banner", 120.0), ("Poster", 180.0), ("Standee", 220.0),
            ("Hoarding", 350.0), ("Flex", 90.0), ("Vinyl", 140.0), ("Canvas", 280.0)
        ]
        
        for category, rate in shiv_rates:
            cursor.execute("INSERT OR IGNORE INTO shiv_rates (category_name, rate) VALUES (?, ?)", 
                          (category, rate))
        
        for category, rate in metro_rates:
            cursor.execute("INSERT OR IGNORE INTO metro_rates (category_name, rate) VALUES (?, ?)", 
                          (category, rate))
    
    conn.commit()
    return conn

# Initialize database
db_conn = init_database()

# ================= PDF GENERATION =================
def generate_pdf(order_data, order_lines):
    """Generate PDF using FPDF"""
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Digital Order System', 0, 1, 'C')
    
    # Order details
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f"Order ID: {order_data['order_id']}", 0, 1)
    pdf.cell(0, 10, f"Date & Time: {order_data['timestamp']}", 0, 1)
    pdf.cell(0, 10, f"Vendor: {order_data['vendor']}", 0, 1)
    pdf.cell(0, 10, f"Campus: {order_data['campus']}", 0, 1)
    pdf.cell(0, 10, f"Event: {order_data['event']}", 0, 1)
    pdf.cell(0, 10, f"Rate Type: {order_data['rate_type']}", 0, 1)
    
    pdf.ln(10)
    
    # Table
    pdf.set_font('Arial', 'B', 12)
    col_widths = [15, 45, 25, 25, 20, 30, 30, 35]
    headers = ["No", "Category", "H (ft)", "W (ft)", "Qty", "Area", "Rate", "Amount"]
    
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
    
    pdf.ln(15)
    
    # Footer
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f"Order Placed By: {order_data['order_by']}", 0, 1)
    pdf.cell(0, 10, "Approved By: __________________", 0, 1)
    
    pdf.ln(10)
    pdf.set_font('Arial', 'I', 10)
    pdf.cell(0, 10, "Programme Developed by Mr. Avinash Chandra Agarwal", 0, 0, 'C')
    
    # Return PDF as bytes
    return pdf.output(dest='S').encode('latin-1')

# ================= DATA LOADING =================
def load_data():
    """Load data from in-memory database"""
    cursor = db_conn.cursor()
    
    # Load categories
    cursor.execute("SELECT category_name FROM categories ORDER BY category_name")
    categories = [row[0] for row in cursor.fetchall()]
    
    # Load vendors
    cursor.execute("SELECT vendor_name FROM vendors ORDER BY vendor_name")
    vendors = [row[0] for row in cursor.fetchall()]
    
    # Load campus
    cursor.execute("SELECT campus_name FROM campus ORDER BY campus_name")
    campuses = [row[0] for row in cursor.fetchall()]
    
    # Load shiv rates
    cursor.execute("SELECT category_name, rate FROM shiv_rates")
    shiv_rates_dict = {row[0]: row[1] for row in cursor.fetchall()}
    
    # Load metro rates
    cursor.execute("SELECT category_name, rate FROM metro_rates")
    metro_rates_dict = {row[0]: row[1] for row in cursor.fetchall()}
    
    return categories, vendors, campuses, shiv_rates_dict, metro_rates_dict

# ================= SESSION STATE =================
if "order_lines" not in st.session_state:
    st.session_state.order_lines = []
if "current_order_id" not in st.session_state:
    st.session_state.current_order_id = None
if "pdf_data" not in st.session_state:
    st.session_state.pdf_data = None
if "form_version" not in st.session_state:
    st.session_state.form_version = "initial"
if "rate_type" not in st.session_state:
    st.session_state.rate_type = "Shivnanda"

# ================= MAIN APP =================
st.header("Step 1: Load Application Data")

# Load data
categories, vendors, campuses, shiv_rates_dict, metro_rates_dict = load_data()

if not categories:
    st.error("Failed to load data. Please refresh the page.")
    st.stop()

st.success(f"✅ Application loaded successfully!")
st.info(f"Loaded: {len(categories)} categories, {len(vendors)} vendors, {len(campuses)} campuses")

# Initialize form values
if "vendor" not in st.session_state:
    st.session_state.vendor = vendors[0] if vendors else ""
if "campus" not in st.session_state:
    st.session_state.campus = campuses[0] if campuses else ""
if "event" not in st.session_state:
    st.session_state.event = ""
if "orderby" not in st.session_state:
    st.session_state.orderby = ""

# Reset and New Order buttons
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

# ================= ORDER FORM =================
st.header("📝 Order Form")

vendor = st.selectbox("Select Vendor", vendors, key="vendor")
campus = st.selectbox("Select Campus", campuses, key="campus")
event = st.text_input("Event Name", key="event")
order_by = st.text_input("Order Placed By", key="orderby")

# Rate Type
st.subheader("💲 Rate Configuration")
rate_type = st.selectbox("Select Rate Type", ["Shivnanda", "Metro"], key="rate_type")
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

for i in range(len(st.session_state.order_lines)):
    with st.expander(f"Category #{i+1}", expanded=True):
        line = st.session_state.order_lines[i]
        
        # Category selection
        cat_idx = categories.index(line["category"]) if line["category"] in categories else 0
        category = st.selectbox("Category", categories, key=f"cat_{i}_{st.session_state.form_version}", index=cat_idx)
        
        # Dimensions and quantity
        col1, col2, col3 = st.columns(3)
        with col1:
            height = st.number_input("Height (ft)", value=line["height"], min_value=0.0, step=0.1, 
                                    key=f"h_{i}_{st.session_state.form_version}")
        with col2:
            width = st.number_input("Width (ft)", value=line["width"], min_value=0.0, step=0.1, 
                                   key=f"w_{i}_{st.session_state.form_version}")
        with col3:
            qty = st.number_input("Quantity", value=line["qty"], min_value=1, step=1, 
                                 key=f"q_{i}_{st.session_state.form_version}")
        
        # Calculate area
        area = round(height * width * qty, 2)
        
        # Get rate
        if rate_type == "Shivnanda":
            rate = shiv_rates_dict.get(category, 0.0)
        else:
            rate = metro_rates_dict.get(category, 0.0)
        
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

# ================= SAVE AND PDF =================
st.markdown("---")
col_save, col_pdf = st.columns(2)

with col_save:
    if st.button("💾 Save Order", type="primary"):
        if not st.session_state.current_order_id:
            st.session_state.current_order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(100,999)}"
        
        # Create order summary
        order_summary = {
            "Order ID": st.session_state.current_order_id,
            "Date": datetime.now().strftime("%d-%m-%Y %H:%M"),
            "Vendor": vendor,
            "Campus": campus,
            "Event": event,
            "Order By": order_by,
            "Rate Type": rate_type
        }
        
        st.success(f"Order saved successfully! Order ID: {st.session_state.current_order_id}")
        st.json(order_summary)

with col_pdf:
    if st.button("📄 Generate PDF"):
        if not st.session_state.order_lines or st.session_state.order_lines[0]["amount"] == 0:
            st.error("Please add at least one category with valid dimensions")
        else:
            # Generate PDF
            order_data = {
                "order_id": st.session_state.current_order_id or f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(100,999)}",
                "timestamp": datetime.now().strftime("%d-%m-%Y %H:%M"),
                "vendor": vendor,
                "campus": campus,
                "event": event,
                "rate_type": rate_type,
                "order_by": order_by
            }
            
            pdf_bytes = generate_pdf(order_data, st.session_state.order_lines)
            st.session_state.pdf_data = pdf_bytes
            
            st.success("PDF generated successfully!")

# Download PDF if available
if st.session_state.pdf_data:
    st.download_button(
        label="⬇️ Download PDF",
        data=st.session_state.pdf_data,
        file_name=f"{order_data['order_id']}.pdf",
        mime="application/pdf"
    )

# Display order summary
if st.session_state.order_lines and st.session_state.order_lines[0]["amount"] > 0:
    st.markdown("---")
    st.subheader("📋 Order Summary")
    
    total_amount = sum(line["amount"] for line in st.session_state.order_lines)
    
    summary_df = pd.DataFrame(st.session_state.order_lines)
    st.dataframe(summary_df, use_container_width=True)
    
    st.metric("Grand Total", f"₹{total_amount:.2f}")

# Close database connection on app end
import atexit
@atexit.register
def close_db():
    db_conn.close()
