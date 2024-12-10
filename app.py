import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

def create_expenses_table():
    connection = sqlite3.connect("expenses.db")
    cursor = connection.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        amount REAL NOT NULL,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        category TEXT NOT NULL,
        note TEXT DEFAULT 'None',
        payment_method TEXT DEFAULT 'Cash'
    )''')

    connection.commit()
    connection.close()

def add_expense(amount, date, time, category, note, payment_method):
    connection = sqlite3.connect("expenses.db")
    cursor = connection.cursor()

    cursor.execute("INSERT INTO expenses (amount, date, time, category, note, payment_method) VALUES (?, ?, ?, ?, ?, ?)",
                   (amount, date, time, category, note, payment_method))
    
    connection.commit()
    connection.close()

def edit_expense(id, amount = None, date = None, time = None, category = None, note = None, payment_method = None):
    try:
        connection = sqlite3.connect("expenses.db")
        cursor = connection.cursor()

        cursor.execute("UPDATE expenses SET amount=?, date=?, time=?, category=?, note=?, payment_method=? WHERE id=?",
                   (amount, date, time, category, note, payment_method, id))
    
        connection.commit()

        if cursor.rowcount == 0:
            print(f"No expense found with ID {id}.")
        else:
            print(f"Expense with ID {id} updated successfully.")

    except sqlite3.Error as e:
        print(f"An error occurred while updating the expense: {e}")

    finally :
        connection.close()  

def delete_expense(id):
    try:
        connection = sqlite3.connect("expenses.db")
        cursor = connection.cursor()

        cursor.execute("DELETE FROM expenses WHERE ID = ?", (id,))
        connection.commit()

        if cursor.rowcount == 0:
            print(f"No expense found with ID {id}.")
        else:
            print(f"Expense with ID {id} deleted successfully.")

    except sqlite3.Error as e:
        print(f"An error occurred while deleting the expense: {e}")

    finally:
        connection.close()

def get_expenses_data():
    connection = sqlite3.connect("expenses.db")
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM expenses")
    data = cursor.fetchall()
    connection.close()
    return data

def dataframe():
    connection = sqlite3.connect("expenses.db")
    df = pd.read_sql_query("SELECT * FROM expenses", connection)
    connection.close()
    return df

def pie_chart():
    if dataframe().empty:
        st.warning("No expenses found.")
    else:
        grouped_data = dataframe().groupby("category")["amount"].sum()
        labels = grouped_data.index
        colors = ["#FFC0CB", "#FF69B4", "#FF0000", "#FFA500", "#FFFF00", "#008000", "#0000FF"]
        amounts = grouped_data.values
        plt.pie(amounts, labels=labels, colors=colors, autopct="%1.1f%%", shadow=True, startangle=140)
        plt.axis("equal")
        st.pyplot(plt)

def main():    
    st.title("Expense Tracker")

    # Sidebar Menu
    menu = ["Add Expense", "View Expenses", "Edit Expense", "Delete Expense", "Analysis", "Visualize Data"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Add Expense":
        st.subheader("Add a New Expense")
        
        amount = st.number_input("Amount",  min_value=0.0)
        date = st.date_input("Date")
        time = str(st.time_input("Time"))
        category = st.selectbox("Category", ["Food", "Travelling", "Shopping", "Entertainment", "Bills", "Rents", "Other"])
        note = st.text_area("Note", placeholder="Enter a note")
        payment_method = st.selectbox("Payment Method", ["Cash", "Credit Card", "Debit Card", "Online Payment"])

        if st.button("Submit", icon="✔️"):
            if amount and date and time and category:
                add_expense(amount, date, time, category, note, payment_method)
                st.success("Expense added successfully!")
            else:
                st.warning("Please fill in all the required fields.")

    elif choice == "View Expenses":
        st.subheader("All Expenses")

        df = dataframe()
        #Table for expenses
        if dataframe().empty:
            st.warning("No expenses found, start adding expenses!")
        else:
             # Search/Filter Options
            with st.expander("Filter Options"):
                category_filter = st.selectbox("Filter by Category", options=["All"] + df["category"].unique().tolist(), index=0)
                payment_filter = st.selectbox("Filter by Payment Method", options=["All"] + df["payment_method"].unique().tolist(), index=0)
                if category_filter != "All":
                    df = df[df["category"] == category_filter]
                if payment_filter != "All":
                    df = df[df["payment_method"] == payment_filter]
            
            # Display Data
            st.dataframe(df)
            
            # Summary Stats
            st.write("### Summary")
            st.write(f"**Total Expenses:** ₹{df['amount'].sum():,.2f}")
            st.write(f"**Average Expense Amount:** ₹{df['amount'].mean():,.2f}")
            st.write(f"**Number of Expenses:** {df.shape[0]}")

            # Export Option
            csv = df.to_csv(index=False)
            st.download_button(label="Download Data as CSV", data=csv, file_name="expenses.csv", mime="text/csv")

    elif choice == "Edit Expense":
        st.subheader("Edit an Expense")

        expenses = get_expenses_data()
        if not expenses:
            st.warning("No expenses found.")
        else:
            expense_df = pd.DataFrame(expenses, columns=["ID", "Amount", "Date", "Time", "Category", "Note", "Payment Method"])
            selected_id = st.selectbox("Select an expense to edit (ID)", expense_df["ID"])

            # Prefill fields with the selected expense's data
            selected_expense = expense_df[expense_df["ID"] == selected_id]
            amount = st.number_input("Amount", value=selected_expense["Amount"].iloc[0], min_value=0.0)
            date = st.date_input("Date", value=pd.to_datetime(selected_expense["Date"].iloc[0]).date())
            time = st.time_input("Time", value=pd.to_datetime(selected_expense["Time"].iloc[0]).time())
            category = st.selectbox("Category", ["Food", "Travelling", "Shopping", "Entertainment", "Bills", "Rents", "Other"],
                                    index=["Food", "Travelling", "Shopping", "Entertainment", "Bills", "Rents", "Other"].index(selected_expense["Category"].iloc[0]))
            note = st.text_area("Note", value=selected_expense["Note"].iloc[0])
            payment_method = st.selectbox("Payment Method", ["Cash", "Credit Card", "Debit Card", "Online Payment"],
                                        index=["Cash", "Credit Card", "Debit Card", "Online Payment"].index(selected_expense["Payment Method"].iloc[0]))

            # Save updated expense
            if st.button("Update Expense"):
                edit_expense(selected_id, amount, str(date), str(time), category, note, payment_method)
                st.success(f"Expense with ID {selected_id} updated successfully!")

    elif choice == "Delete Expense":
        st.subheader("Delete an Expense")
        # Select and delete expense
        selected_expense = st.selectbox("Select an expense", get_expenses_data())
        id = selected_expense[0]
        if st.button("Delete"):
            delete_expense(id)
            st.success("Expense deleted successfully!")
        else:
            st.warning("Please select an expense to delete.")

    elif choice == "Analysis":
        st.subheader("Expense Analysis")

    elif choice == "Visualize Data":
        st.subheader("Charts and Visualizations")
        pie_chart()
        

if __name__ == "__main__":
    create_expenses_table()
    main()