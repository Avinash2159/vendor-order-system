# Digital Order System

A Streamlit web application for managing vendor orders.

## Features
- Create new vendor orders
- Auto-calculate rates based on category
- Generate PDF invoices
- Search existing orders
- Multiple vendor rate types

## Setup Instructions

### 1. Local Setup
```bash
# Clone the repository
git clone <repository-url>

# Install dependencies
pip install -r requirements.txt

# Convert Excel to SQLite
python convert_excel_to_db.py

# Run the app
streamlit run app.py