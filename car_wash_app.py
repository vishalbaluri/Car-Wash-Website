import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from PIL import Image
import os

# -------------------- Ensure Excel File Exists --------------------
if not os.path.exists("car_wash.xlsx"):
    df = pd.DataFrame(columns=["ID", "Car_Number", "Car_Model", "Service_Type",
                               "Customer_Name", "Amount", "Date", "Wash_Count_On_Date"])
    df.to_excel("car_wash.xlsx", index=False)

# -------------------- Database Setup --------------------
conn = sqlite3.connect('car_wash.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS car_wash
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              car_number TEXT,
              car_model TEXT,
              service_type TEXT,
              customer_name TEXT,
              amount REAL,
              date TEXT)''')
conn.commit()

# -------------------- Functions --------------------
def view_records():
    c.execute("SELECT * FROM car_wash")
    return c.fetchall()

def count_by_date(selected_date):
    c.execute("SELECT COUNT(*) FROM car_wash WHERE date=?", (selected_date,))
    return c.fetchone()[0]

def total_amount_by_date(selected_date):
    """Return sum of amount for all washes on the given date."""
    c.execute("SELECT SUM(amount) FROM car_wash WHERE date=?", (selected_date,))
    result = c.fetchone()[0]
    return result if result is not None else 0.0

def get_cars_by_date(selected_date):
    c.execute("SELECT car_number, car_model, service_type, customer_name, amount FROM car_wash WHERE date=?", (selected_date,))
    return c.fetchall()

def export_to_excel():
    """Export DB data to Excel with wash count per date"""
    records = view_records()
    if records:
        df = pd.DataFrame(records, columns=["ID", "Car_Number", "Car_Model", "Service_Type", "Customer_Name", "Amount", "Date"])
        df["Wash_Count_On_Date"] = df["Date"].apply(lambda x: count_by_date(x))
    else:
        df = pd.DataFrame(columns=["ID", "Car_Number", "Car_Model", "Service_Type",
                                   "Customer_Name", "Amount", "Date", "Wash_Count_On_Date"])
    df.to_excel("car_wash.xlsx", index=False)

def add_record(car_number, car_model, service_type, customer_name, amount, date):
    c.execute("INSERT INTO car_wash (car_number, car_model, service_type, customer_name, amount, date) VALUES (?, ?, ?, ?, ?, ?)",
              (car_number, car_model, service_type, customer_name, amount, date))
    conn.commit()
    export_to_excel()

def delete_record(record_id):
    c.execute("DELETE FROM car_wash WHERE id=?", (record_id,))
    conn.commit()
    export_to_excel()

def update_record(record_id, car_number, car_model, service_type, customer_name, amount, date):
    c.execute("""UPDATE car_wash SET car_number=?, car_model=?, service_type=?, customer_name=?, amount=?, date=? WHERE id=?""",
              (car_number, car_model, service_type, customer_name, amount, date, record_id))
    conn.commit()
    export_to_excel()

# -------------------- Streamlit App --------------------
st.set_page_config(page_title="Ultra Shine Car Wash Services", page_icon="🚗", layout="wide")

# Load and display logo
logo = Image.open("car wash image.jpg")
st.image(logo, width=250)


# Display title
st.markdown("<h1 style='text-align: center;'>Ultra Shine Car Wash</h1>", unsafe_allow_html=True)

# -------------------- Login System --------------------
USER_CREDENTIALS = {
    "manager": "manager123",
    "purna": "purna@1619"  # Worker login
}

st.sidebar.subheader("Login")
username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")
login_btn = st.sidebar.button("Login")

if login_btn:
    if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
        st.session_state["logged_in"] = True
        st.session_state["role"] = username
    else:
        st.error("Invalid login credentials")

if "logged_in" in st.session_state and st.session_state["logged_in"]:
    role = st.session_state["role"]
    st.sidebar.success(f"Logged in as {role.capitalize()}")

    # Sidebar menu
    menu = st.sidebar.radio("Choose an action", ["Add New Record", "View All Records", "Search Car History"])

    # -------------------- Add New Record --------------------
    if menu == "Add New Record":
        if role == "purna":  # Only worker can add/edit
            st.subheader("Add Car Wash/Service Record")
            car_number = st.text_input("Car Number")
            car_model = st.text_input("Car Model")
            service_type = st.selectbox("Service Type", ["Exterior Wash", "Interior Cleaning", "Full Service"])
            customer_name = st.text_input("Owner Name")
            amount = st.number_input("Amount Paid (₹)", min_value=0.0, step=50.0)
            date = st.date_input("Date", datetime.today())

            if st.button("Add Record"):
                add_record(car_number, car_model, service_type, customer_name, amount, date.strftime("%Y-%m-%d"))
                st.success("✅ Record Added Successfully!")
        else:
            st.warning("Manager has read-only access.")

    # -------------------- View All Records --------------------
    elif menu == "View All Records":
        st.subheader("All Car Wash Records")
        records = view_records()
        if records:
            df = pd.DataFrame(records, columns=["ID", "Car_Number", "Car_Model", "Service_Type", "Customer_Name", "Amount", "Date"])
            df["Wash_Count_On_Date"] = df["Date"].apply(lambda x: count_by_date(x))
            st.dataframe(df)

            # Excel Download
            export_to_excel()
            with open("car_wash.xlsx", "rb") as file:
                st.download_button("📥 Download Excel File", file, "car_wash.xlsx")
        else:
            st.info("No records found.")

    # -------------------- Search Car History --------------------
    elif menu == "Search Car History":
        st.subheader("Search Car History by Date")
        selected_date = st.date_input("Select Date to Search")
        if selected_date:
            date_str = selected_date.strftime("%Y-%m-%d")

            # show wash count
            wash_count = count_by_date(date_str)
            st.info(f"Total washes on {date_str}: {wash_count}")

            # fetch rows (now includes amount)
            cars = get_cars_by_date(date_str)
            if cars:
                st.write("### Cars Washed on this Date:")
                car_df = pd.DataFrame(
                    cars,
                    columns=[
                        "Car Number",
                        "Car Model",
                        "Service Type",
                        "Customer Name",
                        "Amount (₹)"
                    ]
                )
                st.table(car_df)
    # -------------------- Edit/Delete (Only for Worker) --------------------
    if role == "purna":
        st.subheader("Edit or Delete Records`")
        record_id = st.number_input("Enter Record ID to Edit/Delete", min_value=1, step=1)
        if st.button("Delete Record"):
            delete_record(record_id)
            st.warning("Record Deleted Successfully")

        st.write("Update Record:")
        new_car_number = st.text_input("New Car Number")
        new_car_model = st.text_input("New Car Model")
        new_service_type = st.selectbox("New Service Type", ["Exterior Wash", "Interior Cleaning", "Full Service"])
        new_customer_name = st.text_input("New Customer Name")
        new_amount = st.number_input("New Amount (₹)", min_value=0.0, step=50.0)
        new_date = st.date_input("New Service Date")

        if st.button("Update Record"):
            update_record(record_id, new_car_number, new_car_model, new_service_type, new_customer_name, new_amount, new_date.strftime("%Y-%m-%d"))
            st.success("Record Updated Successfully")
else:
    st.warning("Please login from the sidebar to continue.")
