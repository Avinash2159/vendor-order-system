import pandas as pd
import sqlite3
import os

def excel_to_sqlite():
    print("Excel फाइलों को SQLite डेटाबेस में बदल रहा हूँ...")
    
    # डेटाबेस कनेक्शन बनाएं
    conn = sqlite3.connect('vendor_orders.db')
    
    try:
        # आपके मूल Excel फाइल का पथ
        excel_path = "Digital_Orders.xlsx"
        
        if not os.path.exists(excel_path):
            print(f"❌ {excel_path} फाइल नहीं मिली!")
            return
        
        print(f"✅ {excel_path} लोड हो रही है...")
        
        # 1. Categories शीट (पहला कॉलम लें)
        print("\n1. Categories लोड हो रही हैं...")
        try:
            categories_df = pd.read_excel(excel_path, sheet_name="Categories")
            # पहला कॉलम लें और टेबल बनाएं
            if not categories_df.empty:
                categories_df = categories_df.iloc[:, [0]]  # सिर्फ पहला कॉलम
                categories_df.columns = ['category_name']
                categories_df.to_sql('categories', conn, if_exists='replace', index=False)
                print(f"   ✓ Categories टेबल बन गई: {len(categories_df)} rows")
        except Exception as e:
            print(f"   ✗ Categories में error: {e}")
        
        # 2. VendorList शीट
        print("\n2. Vendors लोड हो रहे हैं...")
        try:
            vendors_df = pd.read_excel(excel_path, sheet_name="VendorList")
            if not vendors_df.empty:
                vendors_df = vendors_df.iloc[:, [0]]  # सिर्फ पहला कॉलम
                vendors_df.columns = ['vendor_name']
                vendors_df.to_sql('vendors', conn, if_exists='replace', index=False)
                print(f"   ✓ Vendors टेबल बन गई: {len(vendors_df)} rows")
        except Exception as e:
            print(f"   ✗ Vendors में error: {e}")
        
        # 3. Campus शीट
        print("\n3. Campus लोड हो रहा है...")
        try:
            campus_df = pd.read_excel(excel_path, sheet_name="Campus")
            if not campus_df.empty:
                campus_df = campus_df.iloc[:, [0]]  # सिर्फ पहला कॉलम
                campus_df.columns = ['campus_name']
                campus_df.to_sql('campus', conn, if_exists='replace', index=False)
                print(f"   ✓ Campus टेबल बन गई: {len(campus_df)} rows")
        except Exception as e:
            print(f"   ✗ Campus में error: {e}")
        
        # 4. Shiv rates शीट (2 कॉलम: Category और Rate)
        print("\n4. Shiv rates लोड हो रही हैं...")
        try:
            shiv_df = pd.read_excel(excel_path, sheet_name="Shiv")
            if not shiv_df.empty and len(shiv_df.columns) >= 2:
                shiv_df = shiv_df.iloc[:, [0, 1]]  # पहले दो कॉलम
                shiv_df.columns = ['category_name', 'rate']
                shiv_df.to_sql('shiv_rates', conn, if_exists='replace', index=False)
                print(f"   ✓ Shiv rates टेबल बन गई: {len(shiv_df)} rows")
        except Exception as e:
            print(f"   ✗ Shiv rates में error: {e}")
        
        # 5. Metro rates शीट (2 कॉलम: Category और Rate)
        print("\n5. Metro rates लोड हो रही हैं...")
        try:
            metro_df = pd.read_excel(excel_path, sheet_name="Metro")
            if not metro_df.empty and len(metro_df.columns) >= 2:
                metro_df = metro_df.iloc[:, [0, 1]]  # पहले दो कॉलम
                metro_df.columns = ['category_name', 'rate']
                metro_df.to_sql('metro_rates', conn, if_exists='replace', index=False)
                print(f"   ✓ Metro rates टेबल बन गई: {len(metro_df)} rows")
        except Exception as e:
            print(f"   ✗ Metro rates में error: {e}")
        
        print("\n" + "="*50)
        print("✅ सभी टेबल्स सफलतापूर्वक बन गईं!")
        
        # टेबल्स की जाँच करें
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"\nकुल टेबल्स: {len(tables)}")
        for table in tables:
            # हर टेबल में कितनी rows हैं
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"  • {table[0]}: {count} rows")
        
    except Exception as e:
        print(f"❌ मुख्य error: {e}")
    
    finally:
        # कनेक्शन बंद करें
        conn.close()
        print("\n✅ डेटाबेस बंद किया गया")

if __name__ == "__main__":
    excel_to_sqlite()
