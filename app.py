import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os
import random
import time
import sqlite3

# DATABASE FILE PATH - FIX FOR STREAMLIT CLOUD
if os.path.exists("vendor_orders.db"):
    DATABASE_FILE = "vendor_orders.db"
else:
    # On Streamlit Cloud, create empty database
    DATABASE_FILE = "/tmp/vendor_orders.db"
    
    # Create database if doesn't exist
    if not os.path.exists(DATABASE_FILE):
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Create empty tables
        cursor.execute('''CREATE TABLE IF NOT EXISTS categories (category_name TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS vendors (vendor_name TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS campus (campus_name TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS shiv_rates (category_name TEXT, rate REAL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS metro_rates (category_name TEXT, rate REAL)''')
        
        # Add sample data
        cursor.execute("INSERT INTO categories (category_name) VALUES ('Banner')")
        cursor.execute("INSERT INTO categories (category_name) VALUES ('Poster')")
        cursor.execute("INSERT INTO vendors (vendor_name) VALUES ('Shivnanda')")
        cursor.execute("INSERT INTO vendors (vendor_name) VALUES ('Metro')")
        cursor.execute("INSERT INTO campus (campus_name) VALUES ('Main Campus')")
        cursor.execute("INSERT INTO shiv_rates (category_name, rate) VALUES ('Banner', 100.0)")
        cursor.execute("INSERT INTO shiv_rates (category_name, rate) VALUES ('Poster', 150.0)")
        cursor.execute("INSERT INTO metro_rates (category_name, rate) VALUES ('Banner', 120.0)")
        cursor.execute("INSERT INTO metro_rates (category_name, rate) VALUES ('Poster', 180.0)")
        
        conn.commit()
        conn.close()
        print("Created sample database on Streamlit Cloud")

st.set_page_config(page_title="Digital Order System", layout="centered")
st.title("📊 Digital Order System")

PDF_DIR = "generated_pdfs"
os.makedirs(PDF_DIR, exist_ok=True)

# Excel के बजाय SQLite डेटाबेस
DATABASE_FILE = "vendor_orders.db"
BACKUP_FILE = "Order_Backup.xlsx"  # अभी भी Excel में बैकअप
LOGO_PATH = "CMS LOGO.jpg"

# ================= PDF GENERATION WITH FPDF =================
class PDF(FPDF):
    def header(self):
        # Logo
        if os.path.exists(LOGO_PATH):
            self.image(LOGO_PATH, 10, 8, 30)
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Digital Order System', 0, 1, 'C')
        self.ln(10)

def generate_pdf(order_data, order_lines):
    """Generate PDF using FPDF"""
    pdf = PDF()
    pdf.add_page()
    
    # Order details
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f"Order ID: {order_data['order_id']}", 0, 1)
    pdf.cell(0, 10, f"Date & Time: {order_data['timestamp']}", 0, 1)
    pdf.cell(0, 10, f"Vendor: {order_data['vendor']}", 0, 1)
    pdf.cell(0, 10, f"Campus: {order_data['campus']}", 0, 1)
    pdf.cell(0, 10, f"Event: {order_data['event']}", 0, 1)
    pdf.cell(0, 10, f"Rate Type: {order_data['rate_type']}", 0, 1)
    
    pdf.ln(10)
    
    # Table header
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
            str(line["height"]),
            str(line["width"]),
            str(line["qty"]),
            str(line["area"]),
            f"₹{line['rate']}",
            f"₹{line['amount']}"
        ]
        
        for i, item in enumerate(row):
            pdf.cell(col_widths[i], 10, item, 1, 0, 'C' if i > 0 else 'L')
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
    
    # Save PDF
    pdf_path = os.path.join(PDF_DIR, f"{order_data['order_id']}.pdf")
    pdf.output(pdf_path)
    return pdf_path

# ================= SQLite HELPER FUNCTIONS =================
def get_db_connection():
    """SQLite डेटाबेस कनेक्शन बनाता है"""
    conn = sqlite3.connect(DATABASE_FILE)
    return conn

def load_data_from_db():
    """SQLite डेटाबेस से सभी डेटा लोड करता है"""
    conn = get_db_connection()
    
    try:
        # Categories लोड करें - पहला कॉलम लें
        categories_df = pd.read_sql_query("SELECT * FROM categories", conn)
        categories = categories_df.iloc[:, 0].tolist() if not categories_df.empty else []
        
        # Vendors लोड करें - पहला कॉलम लें
        vendors_df = pd.read_sql_query("SELECT * FROM vendors", conn)
        vendors = vendors_df.iloc[:, 0].tolist() if not vendors_df.empty else []
        
        # Campus लोड करें - पहला कॉलम लें
        campus_df = pd.read_sql_query("SELECT * FROM campus", conn)
        campuses = campus_df.iloc[:, 0].tolist() if not campus_df.empty else []
        
        # Shiv rates लोड करें
        shiv_df = pd.read_sql_query("SELECT * FROM shiv_rates", conn)
        shiv_rates_dict = {}
        if not shiv_df.empty:
            # पहले कॉलम को key और दूसरे को value बनाएं
            for _, row in shiv_df.iterrows():
                key = str(row.iloc[0])  # पहला कॉलम
                value = float(row.iloc[1]) if len(row) > 1 else 0.0  # दूसरा कॉलम
                shiv_rates_dict[key] = value
        
        # Metro rates लोड करें
        metro_df = pd.read_sql_query("SELECT * FROM metro_rates", conn)
        metro_rates_dict = {}
        if not metro_df.empty:
            # पहले कॉलम को key और दूसरे को value बनाएं
            for _, row in metro_df.iterrows():
                key = str(row.iloc[0])  # पहला कॉलम
                value = float(row.iloc[1]) if len(row) > 1 else 0.0  # दूसरा कॉलम
                metro_rates_dict[key] = value
        
        return categories, vendors, campuses, shiv_rates_dict, metro_rates_dict
        
    except Exception as e:
        print(f"Database error in load_data_from_db: {e}")
        return [], [], [], {}, {}
    finally:
        conn.close()

def save_order_to_backup(rows):
    """ऑर्डर को Excel बैकअप फाइल में सेव करता है"""
    df_new = pd.DataFrame(rows)
    
    if os.path.exists(BACKUP_FILE):
        df_old = pd.read_excel(BACKUP_FILE)
        df_old["OrderID"] = df_old["OrderID"].astype(str)
        df_old = df_old[df_old["OrderID"] != rows[0]["OrderID"]]
        df_final = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df_final = df_new
    
    df_final.to_excel(BACKUP_FILE, index=False)
    return df_final

def search_order_in_backup(order_id):
    """बैकअप Excel से ऑर्डर खोजता है"""
    if os.path.exists(BACKUP_FILE):
        df = pd.read_excel(BACKUP_FILE)
        df["OrderID"] = df["OrderID"].astype(str)
        search_term = str(order_id).strip()
        res = df[df["OrderID"] == search_term]
        return res
    return pd.DataFrame()

# ================= SESSION HELPERS =================
def reset_form_only():
    # Clear widget states
    for k in list(st.session_state.keys()):
        if k.startswith(("cat","h","w","q","r","form_")):
            del st.session_state[k]
    
    # Load data from database to get defaults
    categories, vendors, campuses, _, _ = load_data_from_db()
    
    st.session_state["vendor"] = vendors[0] if vendors else ""
    st.session_state["campus"] = campuses[0] if campuses else ""
    st.session_state["event"] = ""
    st.session_state["orderby"] = ""
    st.session_state["rate_type"] = "Shivnanda"  # Default rate type
    
    # Reset order lines to one empty category
    st.session_state.order_lines = [{
        "category": categories[0] if categories else "",
        "height": 0.0,
        "width": 0.0,
        "qty": 1,
        "area": 0.0,
        "rate": 0.0,
        "amount": 0.0
    }]
    
    # Update form version to force new widgets
    st.session_state.form_version = str(time.time())

def create_new_order():
    st.session_state.current_order_id = None
    # Update form version
    st.session_state.form_version = str(time.time())

# Function to get rate based on category and vendor type
def get_rate_for_category(category_name, rate_type, shiv_rates_dict, metro_rates_dict):
    if rate_type == "Shivnanda" and category_name in shiv_rates_dict:
        return shiv_rates_dict[category_name]
    elif rate_type == "Metro" and category_name in metro_rates_dict:
        return metro_rates_dict[category_name]
    return 0.0

# Initialize session state
if "order_lines" not in st.session_state:
    st.session_state.order_lines = [{}]
if "current_order_id" not in st.session_state:
    st.session_state.current_order_id = None
if "pdf_path" not in st.session_state:
    st.session_state.pdf_path = None
if "form_version" not in st.session_state:
    st.session_state.form_version = "initial"
if "rate_type" not in st.session_state:
    st.session_state.rate_type = "Shivnanda"

# ================= MAIN APP =================
st.header("Step 1: Load Data from Database")

# Check if database exists
if os.path.exists(DATABASE_FILE):
    try:
        # Load all data from SQLite database
        categories, vendors, campuses, shiv_rates_dict, metro_rates_dict = load_data_from_db()
        
        if not categories:
            st.error("Database is empty or no categories found.")
            st.info("Please make sure Digital_Orders.xlsx file exists and run convert_excel_to_db.py")
            st.stop()
        
        st.success(f"✅ Data loaded successfully!")
        st.info(f"Loaded: {len(categories)} categories, {len(vendors)} vendors, {len(campuses)} campuses")
        
        # Initialize session state
        if "vendor" not in st.session_state:
            st.session_state["vendor"] = vendors[0] if vendors else ""
        if "campus" not in st.session_state:
            st.session_state["campus"] = campuses[0] if campuses else ""
        if "event" not in st.session_state:
            st.session_state["event"] = ""
        if "orderby" not in st.session_state:
            st.session_state["orderby"] = ""

        # ================= SEARCH =================
        st.header("🔍 Search Order")

        search_id = st.text_input("Enter Order ID", key="search")
        
        if st.button("Search Order"):
            res = search_order_in_backup(search_id)
            
            if not res.empty:
                # Clear widget states for category fields
                for k in list(st.session_state.keys()):
                    if k.startswith(("cat","h","w","q","r","form_")):
                        del st.session_state[k]
                
                st.session_state.current_order_id = search_id
                first_row = res.iloc[0]
                
                # Update form values
                st.session_state["vendor"] = first_row["Vendor"]
                st.session_state["campus"] = first_row["Campus"]
                st.session_state["event"] = first_row["Event"] if pd.notna(first_row["Event"]) else ""
                st.session_state["orderby"] = first_row["OrderPlacedBy"] if pd.notna(first_row["OrderPlacedBy"]) else ""
                
                # Rebuild order lines
                st.session_state.order_lines = []
                for idx, r in res.iterrows():
                    st.session_state.order_lines.append({
                        "category": r["Category"],
                        "height": float(r["Height"]),
                        "width": float(r["Width"]),
                        "qty": int(r["Qty"]),
                        "area": float(r["Area"]),
                        "rate": float(r["Rate"]),
                        "amount": float(r["Amount"])
                    })
                
                # Update form version to force new widgets
                st.session_state.form_version = str(time.time())
                
                st.success(f"Order {search_id} found and loaded!")
                st.rerun()
            else:
                st.error(f"Order ID '{search_id}' not found.")

        # ================= BUTTONS =================
        col_a, col_b = st.columns(2)
        if col_a.button("🆕 Create New Order"):
            create_new_order()
            st.rerun()

        if col_b.button("🔄 Reset Form"):
            reset_form_only()
            st.session_state.current_order_id = None
            st.session_state.pdf_path = None
            st.rerun()

        # ================= FORM =================
        st.header("📝 Order Form")

        vendor = st.selectbox("Select Vendor", vendors, key="vendor")
        campus = st.selectbox("Select Campus", campuses, key="campus")
        event = st.text_input("Event Name", key="event")
        order_by = st.text_input("Order Placed By", key="orderby")
        
        # ================= RATE TYPE SELECTION =================
        st.markdown("---")
        st.subheader("💲 Rate Configuration")
        
        rate_type = st.selectbox(
            "Select Rate Type",
            ["Shivnanda", "Metro"],
            key="rate_type",
            help="Select vendor rate type to auto-fill rates based on category"
        )
        
        st.info(f"Using **{rate_type}** rates. Rate field will auto-fill based on selected category.")

        st.markdown("---")
        st.subheader("Order Categories")

        # Create order categories with versioned keys
        for i in range(len(st.session_state.order_lines)):
            line = st.session_state.order_lines[i] if i < len(st.session_state.order_lines) else {}
            
            with st.expander(f"Category #{i+1}", expanded=True):
                # Get category index
                cat_index = 0
                if line.get("category") and line.get("category") in categories:
                    try:
                        cat_index = categories.index(line.get("category"))
                    except:
                        cat_index = 0
                
                # Create widgets with versioned keys
                form_key = f"v{st.session_state.form_version.replace('.', '')}"
                
                cat = st.selectbox(
                    "Category", 
                    categories,
                    index=cat_index,
                    key=f"cat{i}_{form_key}",
                    on_change=None
                )
                
                # Get current values
                current_height = float(line.get("height", 0.0))
                current_width = float(line.get("width", 0.0))
                current_qty = int(line.get("qty", 1))
                
                # Get rate based on selected category and rate type
                actual_rate = get_rate_for_category(cat, rate_type, shiv_rates_dict, metro_rates_dict)
                
                col1, col2, col3 = st.columns(3)
                
                h = col1.number_input(
                    "Height", 
                    value=current_height,
                    step=0.1,
                    key=f"h{i}_{form_key}"
                )
                
                w = col2.number_input(
                    "Width", 
                    value=current_width,
                    step=0.1,
                    key=f"w{i}_{form_key}"
                )
                
                q = col3.number_input(
                    "Qty", 
                    value=current_qty,
                    min_value=1,
                    step=1,
                    key=f"q{i}_{form_key}"
                )
                
                area = round(h * w * q, 2)
                st.markdown(f"**Total Area:** `{area}`")
                
                # FIXED: Create unique key for rate field based on category and rate type
                rate_field_key = f"rate{i}_{form_key}_{cat}_{rate_type}"
                
                # Display rate field with the actual rate
                r_display = st.text_input(
                    "Rate", 
                    value=f"{actual_rate:.2f}",
                    key=rate_field_key,
                    disabled=True,
                    help=f"Rate auto-filled from {rate_type} rates based on selected category"
                )
                
                # Use actual_rate for calculation
                r = actual_rate
                
                amt = round(area * r, 2)
                st.markdown(f"**Amount:** ₹ {amt}")
                
                # Update session state
                if i < len(st.session_state.order_lines):
                    st.session_state.order_lines[i] = {
                        "category": cat,
                        "height": h,
                        "width": w,
                        "qty": q,
                        "area": area,
                        "rate": r,
                        "amount": amt
                    }
                
                # Add button to update rate if category changes
                if st.button("🔄 Update Rate", key=f"update_rate{i}_{form_key}"):
                    # Get the new rate for current category
                    new_rate = get_rate_for_category(cat, rate_type, shiv_rates_dict, metro_rates_dict)
                    # Update session state
                    st.session_state.order_lines[i]["rate"] = new_rate
                    st.session_state.order_lines[i]["amount"] = round(area * new_rate, 2)
                    st.rerun()
                
                # Add category button
                if st.button("➕ Add Category", key=f"add{i}_{form_key}"):
                    new_category = categories[0] if categories else ""
                    new_rate = get_rate_for_category(new_category, rate_type, shiv_rates_dict, metro_rates_dict)
                    st.session_state.order_lines.append({
                        "category": new_category,
                        "height": 0.0,
                        "width": 0.0,
                        "qty": 1,
                        "area": 0.0,
                        "rate": new_rate,
                        "amount": 0.0
                    })
                    st.rerun()
                
                # Delete button
                if len(st.session_state.order_lines) > 1:
                    if st.button("🗑 Delete", key=f"del{i}_{form_key}"):
                        st.session_state.order_lines.pop(i)
                        st.rerun()

        # ================= SAVE / PDF =================
        col1, col2 = st.columns(2)
        save_btn = col1.button("💾 Save Order Info")
        pdf_btn = col2.button("📄 Generate Order PDF")

        if save_btn or pdf_btn:
            if not st.session_state.current_order_id:
                st.session_state.current_order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(100,999)}"

            oid = st.session_state.current_order_id
            ts = datetime.now().strftime("%d-%m-%Y %H:%M")

            rows=[]
            for l in st.session_state.order_lines:
                rows.append({
                    "OrderID": oid,
                    "DateTime": ts,
                    "Vendor": vendor,
                    "Campus": campus,
                    "Event": event,
                    "Category": l["category"],
                    "Height": l["height"],
                    "Width": l["width"],
                    "Qty": l["qty"],
                    "Area": l["area"],
                    "Rate": l["rate"],
                    "Amount": l["amount"],
                    "OrderPlacedBy": order_by,
                    "RateType": rate_type
                })

            # Save to Excel backup
            save_order_to_backup(rows)
            st.success(f"Order Saved | {oid}")

            # ================= PDF =================
            if pdf_btn:
                try:
                    order_data = {
                        "order_id": oid,
                        "timestamp": ts,
                        "vendor": vendor,
                        "campus": campus,
                        "event": event,
                        "rate_type": rate_type,
                        "order_by": order_by
                    }
                    
                    pdf_path = generate_pdf(order_data, st.session_state.order_lines)
                    st.session_state.pdf_path = pdf_path
                    st.success(f"PDF generated successfully!")
                    
                except Exception as e:
                    st.error(f"Error generating PDF: {str(e)}")

        if st.session_state.pdf_path and os.path.exists(st.session_state.pdf_path):
            with open(st.session_state.pdf_path, "rb") as f:
                st.download_button(
                    "⬇️ Download PDF",
                    f,
                    file_name=os.path.basename(st.session_state.pdf_path),
                    mime="application/pdf"
                )

    except Exception as e:
        st.error(f"Error loading from database: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        st.info("Please make sure you have run convert_excel_to_db.py to create the database.")
else:
    st.error(f"Database file '{DATABASE_FILE}' not found!")
    st.info("Please run convert_excel_to_db.py first to create the database from Excel files.")
