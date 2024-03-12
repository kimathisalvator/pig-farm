import logging
from tkinter import Tk, Label, Entry, Button, Text, messagebox, ttk, Toplevel
from tkcalendar import DateEntry
from datetime import datetime, timedelta
import sqlite3

# Constants
DEFAULT_GESTATION_PERIOD = 144  # Default gestation period in days

# Setup logging
logging.basicConfig(filename='pig_database.log', level=logging.ERROR)

class PigRegistrationApp:
    def __init__(self, window):
        self.window = window
        self.window.title("Pig Registration Form")

        # Initialize database connection
        self.conn, self.cursor = self.initialize_database()

        # Create and place labels, entry fields, and buttons
        Label(window, text="Date of Birth:").grid(row=0, column=0)
        self.dob_entry = DateEntry(window, width=12, background='darkblue', foreground='white', borderwidth=2,
                                   date_pattern='yyyy-mm-dd')
        self.dob_entry.grid(row=0, column=1)

        Label(window, text="Number of Males:").grid(row=1, column=0)
        self.males_entry = Entry(window)
        self.males_entry.grid(row=1, column=1)

        Label(window, text="Number of Females:").grid(row=2, column=0)
        self.females_entry = Entry(window)
        self.females_entry.grid(row=2, column=1)

        Label(window, text="Mother ID:").grid(row=3, column=0)
        self.mother_id_entry = Entry(window)
        self.mother_id_entry.grid(row=3, column=1)

        # Create and place buttons using ttk.Button for styling
        register_button = ttk.Button(window, text="Register", command=self.register_pig)
        register_button.grid(row=4, column=0, columnspan=2)

        view_batches_button = ttk.Button(window, text="View Registered Batches", command=self.view_registered_batches)
        view_batches_button.grid(row=5, column=0, columnspan=2)

        # Configure row and column weights to allow resizing
        window.grid_rowconfigure(4, weight=1)
        window.grid_columnconfigure(0, weight=1)
        window.grid_columnconfigure(1, weight=1)

    def initialize_database(self):
        try:
            # Create a SQLite database connection
            conn = sqlite3.connect('farm_database.db')
            cursor = conn.cursor()

            # Create a table to store pig registration data if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pig_registration (
                    id INTEGER PRIMARY KEY,
                    batch_number TEXT,
                    dob DATE,
                    males INTEGER,
                    females INTEGER,
                    mother_id TEXT
                )
            ''')

            conn.commit()

            return conn, cursor

        except sqlite3.Error as e:
            logging.error(f"Error initializing database: {e}")
            messagebox.showerror("Database Error", "Failed to initialize the database.")
            return None, None

    def register_pig(self):
        try:
            batch_number = self.generate_batch_number()
            dob = self.dob_entry.get()
            males = self.males_entry.get()
            females = self.females_entry.get()
            mother_id = self.mother_id_entry.get()

            # Insert data into the database
            if self.insert_data_into_database(batch_number, dob, males, females, mother_id):
                messagebox.showinfo("Success", "Pig registered successfully!")
            else:
                messagebox.showerror("Error", "Failed to register pig.")

            # Clear input fields
            self.dob_entry.set_date(datetime.now())
            self.males_entry.delete(0, 'end')
            self.females_entry.delete(0, 'end')
            self.mother_id_entry.delete(0, 'end')

        except Exception as e:
            logging.error(f"An error occurred while registering pig: {e}")
            messagebox.showerror("Error", "An unexpected error occurred. Please check the logs.")

    def insert_data_into_database(self, batch_number, dob, males, females, mother_id):
        try:
            self.cursor.execute("INSERT INTO pig_registration (batch_number, dob, males, females, mother_id) VALUES (?, ?, ?, ?, ?)",
                            (batch_number, dob, males, females, mother_id))
            self.conn.commit()
            return True

        except Exception as e:
            logging.error(f"Error inserting data into the database: {e}")
            messagebox.showerror("Database Error", f"Failed to insert data into the database. {e}")
            return False

    def generate_batch_number(self):
        # Example: A001, A002, ..., Z999
        last_batch_number = self.get_last_batch_number()
        if last_batch_number:
            prefix = chr(((ord(last_batch_number[0]) - ord('A') + 1) % 26) + ord('A'))
            number = str(int(last_batch_number[1:]) + 1).zfill(3)
        else:
            # If no batches are registered yet
            prefix = 'A'
            number = '001'

        return f"{prefix}{number}"

    def get_last_batch_number(self):
        try:
            self.cursor.execute("SELECT batch_number FROM pig_registration ORDER BY id DESC LIMIT 1")
            last_batch = self.cursor.fetchone()
            return last_batch[0] if last_batch else None

        except Exception as e:
            logging.error(f"Error fetching last batch number from the database: {e}")
            messagebox.showerror("Database Error", "Failed to fetch data from the database.")
            return None

    def view_registered_batches(self):
        try:
            # Create a new window for viewing registered batches
            view_batches_window = Toplevel(self.window)
            view_batches_window.title("Registered Batches")

            # Create a text widget to display registered batches
            batches_text_widget = Text(view_batches_window, wrap="none")
            batches_text_widget.grid(row=0, column=0, sticky="nsew")

            # Configure the Text widget to expand with the window
            batches_text_widget.config(wrap="none")  # Disable automatic line wrapping

            # Fetch registered batches and their information from the database
            batches_data = self.get_batch_information()

            # Display titles
            titles = ["Batch Number", "Date of Birth", "Males", "Females", "Mother ID", "Age (Days)"]
            for col, title in enumerate(titles):
                batches_text_widget.insert("end", f"{title}\t\t")
                batches_text_widget.tag_add("title", f"1.{col*12}", f"1.{(col+1)*12}")
                batches_text_widget.tag_config("title", font=('bold', 10), underline=True)
            batches_text_widget.insert("end", "\n\n")

            # Display registered batches and their information in the text widget
            if batches_data:
                for row, batch in enumerate(batches_data, start=2):
                    for col, value in enumerate(batch):
                        if col != 5:  # Skip the last column (Age)
                            batches_text_widget.insert("end", f"{value}\t\t")
                    # Calculate and display age (current date - date of birth)
                    dob = datetime.strptime(batch[1], '%Y-%m-%d').date()
                    age = (datetime.now().date() - dob).days
                    batches_text_widget.insert("end", f"{age}\t\t")
                    batches_text_widget.insert("end", "\n")
            else:
                batches_text_widget.insert("end", "No registered batches.")

            # Add a close button to the window
            close_button = ttk.Button(view_batches_window, text="Close", command=view_batches_window.destroy)
            close_button.grid(row=1, column=0)

            # Add a scrollbar for better navigation
            scrollbar = ttk.Scrollbar(view_batches_window, command=batches_text_widget.yview)
            batches_text_widget.config(yscrollcommand=scrollbar.set)
            scrollbar.grid(row=0, column=1, sticky="ns")

            # Update the window to handle resizing
            view_batches_window.update_idletasks()

            # Configure weight for resizing
            view_batches_window.grid_rowconfigure(0, weight=1)
            view_batches_window.grid_columnconfigure(0, weight=1)

        except Exception as e:
            logging.error(f"An error occurred while viewing registered batches: {e}")
            messagebox.showerror("Error", "An unexpected error occurred. Please check the logs.")


    def get_batch_information(self):
        try:
            self.cursor.execute("SELECT batch_number, dob, males, females, mother_id FROM pig_registration")
            batches_data = self.cursor.fetchall()

            # Check if there are any registered batches
            if not batches_data:
                return None

            # Calculate the age of each batch based on the date of birth
            today = datetime.now().date()
            for index, batch in enumerate(batches_data):
                dob = datetime.strptime(batch[1], '%Y-%m-%d').date()
                age = (today - dob).days
                batches_data[index] = (*batch, age)

            return batches_data

        except Exception as e:
            logging.error(f"Error fetching batch information from the database: {e}")
            messagebox.showerror("Database Error", "Failed to fetch data from the database.")
            return None

if __name__ == "__main__":
    pig_registration_app = PigRegistrationApp(Tk())
    pig_registration_app.window.mainloop()
