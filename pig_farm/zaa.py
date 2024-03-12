import logging
from tkinter import Tk, Label, Entry, Button, Text, messagebox, ttk
from tkcalendar import DateEntry
from datetime import datetime, timedelta
from plyer import notification
import sqlite3
import threading
from ttkthemes import ThemedStyle

# Constants
DEFAULT_GESTATION_PERIOD = 144  # Default gestation period in days

# Setup logging
logging.basicConfig(filename='pig_breeding.log', level=logging.ERROR)

class PigBreedingApp:
    def __init__(self, window):
        self.window = window
        self.window.title("Pig Breeding Calculator")

        # Initialize database connection
        self.conn, self.cursor = self.initialize_database()

        # Set the theme
        style = ThemedStyle(self.window)
        style.set_theme("equilux")

        # Create and place labels, entry fields, and buttons
        Label(window, text="Pig ID:", foreground='blue').grid(row=0, column=0, sticky='e')
        self.pig_id_entry = Entry(window)
        self.pig_id_entry.grid(row=0, column=1, sticky='w')

        Label(window, text="Served Date:", foreground='blue').grid(row=1, column=0, sticky='e')
        self.served_date_entry = DateEntry(window, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.served_date_entry.grid(row=1, column=1, sticky='w')

        # Create and place a text widget to display breeding results
        self.result_text_widget = Text(window, width=70, height=10, wrap="none", font=('Arial', 10), foreground='orange')
        self.result_text_widget.grid(row=2, column=0, columnspan=2, sticky="nsew")

        # Create and place buttons using ttk.Button for styling
        calculate_button = ttk.Button(window, text="Calculate", command=self.calculate_and_display, style='TButton')
        calculate_button.grid(row=4, column=0, columnspan=2)

        view_database_button = ttk.Button(window, text="View Database Entries", command=self.view_database_entries, state="disabled", style='TButton')
        view_database_button.grid(row=5, column=0, columnspan=2)

        delete_born_pigs_button = ttk.Button(window, text="Delete Born Pigs", command=self.delete_born_pigs, style='TButton')
        delete_born_pigs_button.grid(row=6, column=0, columnspan=2)

        # Configure the Text widget to expand with the window
        self.result_text_widget.config(wrap="none")  # Disable automatic line wrapping

        # Configure row and column weights to allow resizing
        window.grid_rowconfigure(2, weight=1)
        window.grid_columnconfigure(0, weight=1)
        window.grid_columnconfigure(1, weight=1)

        # Enable view database button after successful database initialization
        view_database_button["state"] = "normal"

    def initialize_database(self):
        try:
            # Create a SQLite database connection
            conn = sqlite3.connect('pig_breeding.db')
            cursor = conn.cursor()

            # Create a table to store pig breeding data if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pig_breeding (
                    id INTEGER PRIMARY KEY,
                    pig_id TEXT,
                    served_date DATE,
                    expected_birth_date DATE
                )
            ''')
            conn.commit()

            return conn, cursor

        except sqlite3.Error as e:
            logging.error(f"Error initializing database: {e}")
            messagebox.showerror("Database Error", "Failed to initialize the database.")
            return None, None

    def close_database_connection(self):
        try:
            self.conn.close()
        except Exception as e:
            logging.error(f"Error closing database connection: {e}")

    def calculate_expected_birth_date(self, served_date):
        return served_date + timedelta(days=DEFAULT_GESTATION_PERIOD)

    def insert_data_into_database(self, pig_id, served_date, expected_birth_date):
        try:
            self.cursor.execute("INSERT INTO pig_breeding (pig_id, served_date, expected_birth_date) VALUES (?, ?, ?)",
                               (pig_id, served_date, expected_birth_date))
            self.conn.commit()
            return True

        except Exception as e:
            logging.error(f"Error inserting data into the database: {e}")
            messagebox.showerror("Database Error", "Failed to insert data into the database.")
            return False

    def get_data_from_database(self):
        try:
            self.cursor.execute("SELECT pig_id, served_date, expected_birth_date FROM pig_breeding ORDER BY id DESC LIMIT 1")
            data = self.cursor.fetchone()
            return data

        except Exception as e:
            logging.error(f"Error fetching data from the database: {e}")
            messagebox.showerror("Database Error", "Failed to fetch data from the database.")
            return None

    def delete_pig_from_database(self, pig_id):
        try:
            self.cursor.execute("DELETE FROM pig_breeding WHERE pig_id=?", (pig_id,))
            self.conn.commit()

            # Refresh the displayed entries after successful deletion
            self.view_database_entries()

            return True

        except Exception as e:
            logging.error(f"Error deleting data from the database: {e}")
            messagebox.showerror("Database Error", "Failed to delete data from the database.")
            return False

    def view_database_entries(self):
        try:
            self.cursor.execute("SELECT * FROM pig_breeding")
            entries = self.cursor.fetchall()

            # Sort entries based on days left
            entries.sort(key=lambda entry: (datetime.strptime(entry[3], '%Y-%m-%d').date() - datetime.now().date()).days)

            # Clear existing text in the widget
            self.result_text_widget.delete(1.0, "end")

            # Display column headers
            header_text = "ID\tPig ID\tServed Date\tExpected Birth Date\tDays Left\n"
            self.result_text_widget.insert("end", header_text)

            if entries:
                for entry in entries:
                    # Extracting relevant information
                    if len(entry) >= 4:
                        pig_id, served_date, expected_birth_date = entry[1:4]

                        # Calculate and print the number of days left
                        days_left = (datetime.strptime(expected_birth_date, '%Y-%m-%d').date() - datetime.now().date()).days

                        # Format the entry text
                        entry_text = f"{entry[0]}\t{pig_id}\t{served_date}\t{expected_birth_date}\t{days_left}\n"
                        self.result_text_widget.insert("end", entry_text)
                    else:
                        logging.warning("Invalid entry format in the database.")
            else:
                # Display a message if there are no entries
                self.result_text_widget.insert("end", "No entries in the database.")

        except Exception as e:
            logging.error(f"An error occurred while fetching database entries: {e}")
            messagebox.showerror("Error", "An unexpected error occurred. Please check the logs.")

    def calculate_and_display(self):
        try:
            pig_id = self.pig_id_entry.get().strip()
            served_date = self.served_date_entry.get_date()

            if not pig_id or not served_date:
                messagebox.showerror("Error", "Please fill in all fields.")
                return

            expected_birth_date = self.calculate_expected_birth_date(served_date)
            self.display_results_in_window(pig_id, expected_birth_date)

            # Insert data into the database
            if self.insert_data_into_database(pig_id, served_date, expected_birth_date):
                # Check if data was successfully saved in the database
                messagebox.showinfo("Success", "Data saved successfully in the database.")
            else:
                messagebox.showerror("Error", "Failed to save data in the database.")

            # Clear input fields
            self.pig_id_entry.delete(0, 'end')
            self.served_date_entry.set_date(datetime.now())

        except Exception as e:
            logging.error(f"An error occurred in calculate_and_display: {e}")
            messagebox.showerror("Error", "An unexpected error occurred. Please check the logs.")

    def display_results_in_window(self, pig_id, expected_birth_date):
        # Calculate the number of days until the expected birth date
        current_date = datetime.now().date()
        days_until_birth = (expected_birth_date - current_date).days

        result_text = f"Pig ID {pig_id} is expected to give birth on: {expected_birth_date.strftime('%Y-%m-%d')}"

        if days_until_birth == 0:
            result_text += "\nToday is the expected birth date! Prepare for piglets."
            notification_message = "Today is the expected birth date! Prepare for piglets."

            # Prompt user for confirmation to delete pig from the database
            user_response = messagebox.askyesno("Confirmation", "The pig has farrowed! Do you want to delete this pig from the database?")
            if user_response:
                if self.delete_pig_from_database(pig_id):
                    messagebox.showinfo("Deleted", f"Pig ID {pig_id} has been deleted from the database.")
                else:
                    messagebox.showinfo("Not Deleted", f"Pig ID {pig_id} was not deleted from the database.")
        else:
            result_text += f"\n{days_until_birth} days until the expected birth date."
            notification_message = f"{days_until_birth} days left until the expected birth date."

            # Check if days_until_birth is less than 5 to show a notification
            if days_until_birth < 5:
                threading.Timer(86400, self.show_notification, args=[notification_message]).start()  # Schedule notification after 24 hours

        # Clear existing text in the widget and insert new results
        self.result_text_widget.delete(1.0, "end")
        self.result_text_widget.insert("end", result_text)

        # Send a notification using plyer
        notification.notify(
            title="Pig Breeding Calculator",
            message=notification_message,
            timeout=10  # Notification will disappear after 10 seconds
        )

    def show_notification(self, message):
        notification.notify(
            title="Pig Breeding Calculator",
            message=message,
            timeout=10  # Notification will disappear after 10 seconds
        )

    def delete_born_pigs(self):
        try:
            # Get a list of pigs that have given birth
            born_pigs = [(pig_id, expected_birth_date) for pig_id, _, expected_birth_date in self.get_data_from_database()
                        if datetime.strptime(expected_birth_date, '%Y-%m-%d').date() < datetime.now().date()]

            # Delete each pig in the list
            for pig_id, _ in born_pigs:
                self.delete_pig_from_database(pig_id)

            # Inform the user about the deletion
            messagebox.showinfo("Deleted", f"Deleted {len(born_pigs)} pigs that have given birth.")

        except Exception as e:
            logging.error(f"Error deleting born pigs from the database: {e}")
            messagebox.showerror("Database Error", "Failed to delete born pigs from the database.")


    def main(self):
        # Start the GUI main loop
        self.window.mainloop()

        # Close database connection when the GUI is closed
        self.close_database_connection()

# Instantiate and run the PigBreedingApp
if __name__ == "__main__":
    pig_breeding_app = PigBreedingApp(Tk())
    pig_breeding_app.main()
