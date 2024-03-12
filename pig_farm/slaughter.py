import logging
from tkinter import Tk, Label, Text, ttk, Toplevel, Entry, Button, messagebox
from datetime import datetime
import sqlite3

# Constants
SLAUGHTER_AGE_THRESHOLD = 168  # Age threshold for slaughter

# Setup logging
logging.basicConfig(filename='slaughter_log.log', level=logging.ERROR)

class DatabaseHandler:
    @staticmethod
    def initialize_database():
        try:
            # Create a SQLite database connection
            conn = sqlite3.connect('farm_database.db')
            cursor = conn.cursor()

            # Create a table to store additional slaughter information if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS slaughter_information (
                    id INTEGER PRIMARY KEY,
                    batch_number TEXT,
                    user_id TEXT,
                    males_slaughtered INTEGER,
                    females_slaughtered INTEGER,
                    avg_weight REAL,
                    date_slaughtered DATE
                )
            ''')

            conn.commit()

            return conn, cursor

        except sqlite3.Error as e:
            logging.error(f"Error initializing database: {e}")
            return None, None

class SlaughterViewApp:
    def __init__(self, window):
        self.window = window
        self.window.title("Slaughter View")

        # Initialize database connection
        self.conn, self.cursor = DatabaseHandler.initialize_database()

        # Create and place labels, text widget, and buttons
        Label(window, text="Batches Ready for Slaughter:").grid(row=0, column=0)

        # Add a button to view slaughtered batches information
        view_slaughtered_button = ttk.Button(window, text="View Slaughtered Batches", command=self.view_slaughtered_batches)
        view_slaughtered_button.grid(row=0, column=1)

        self.slaughter_text_widget = Text(window, wrap="none")
        self.slaughter_text_widget.grid(row=1, column=0, columnspan=2, sticky="nsew")

        self.slaughter_text_widget.config(wrap="none")  # Disable automatic line wrapping

        # Fetch batches ready for slaughter and display in the text widget
        self.display_batches_for_slaughter()

        # Add a close button to the window
        close_button = ttk.Button(window, text="Close", command=self.window.destroy)
        close_button.grid(row=2, column=0, columnspan=2)

        # Add a scrollbar for better navigation
        scrollbar = ttk.Scrollbar(window, command=self.slaughter_text_widget.yview)
        self.slaughter_text_widget.config(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=1, column=2, sticky="ns")

        # Update the window to handle resizing
        self.window.update_idletasks()

        # Configure weight for resizing
        self.window.grid_rowconfigure(1, weight=1)
        self.window.grid_columnconfigure(0, weight=1)

    def display_batches_for_slaughter(self):
        try:
            # Fetch batches ready for slaughter and their information from the database
            slaughter_data = self.get_batches_for_slaughter()

            # Display titles
            titles = ["Batch Number", "Males", "Females", "Age (Days)"]
            for col, title in enumerate(titles):
                self.slaughter_text_widget.insert("end", f"{title}\t\t")
                self.slaughter_text_widget.tag_add("title", f"1.{col*12}", f"1.{(col+1)*12}")
                self.slaughter_text_widget.tag_config("title", font=('bold', 10), underline=True)
            self.slaughter_text_widget.insert("end", "\n\n")

            # Display batches ready for slaughter and their information in the text widget
            if slaughter_data:
                for row, batch in enumerate(slaughter_data, start=2):
                    for col, value in enumerate(batch):
                        self.slaughter_text_widget.insert("end", f"{value}\t\t")
                    self.slaughter_text_widget.insert("end", "\n")

                    # Add a button for each batch to trigger the reduction window
                    slaughter_button = ttk.Button(self.slaughter_text_widget, text="Reduce", command=lambda b=batch[0]: self.reduce_pig_numbers(b))
                    self.slaughter_text_widget.window_create("end", window=slaughter_button)
                    self.slaughter_text_widget.insert("end", "\n")

            else:
                self.slaughter_text_widget.insert("end", "No batches ready for slaughter.")

        except Exception as e:
            logging.error(f"An error occurred while displaying batches for slaughter: {e}")

    def get_batches_for_slaughter(self):
        try:
            # Fetch batches with age above the threshold
            self.cursor.execute("SELECT batch_number, males, females, dob FROM pig_registration")
            batches_data = self.cursor.fetchall()

            today = datetime.now().date()

            # Filter batches based on age threshold
            batches_for_slaughter = []
            for batch in batches_data:
                dob = datetime.strptime(batch[3], '%Y-%m-%d').date()
                age = (today - dob).days
                if age >= SLAUGHTER_AGE_THRESHOLD:
                    batches_for_slaughter.append((batch[0], batch[1], batch[2], age))

            return batches_for_slaughter

        except Exception as e:
            logging.error(f"Error fetching batches for slaughter from the database: {e}")
            return None

    def reduce_pig_numbers(self, batch_number):
        try:
            # Create a new window for reducing pig numbers
            reduce_window = Toplevel(self.window)
            reduce_window.title("Reduce Pig Numbers")

            # Fetch current pig numbers for the selected batch
            self.cursor.execute("SELECT males, females FROM pig_registration WHERE batch_number=?", (batch_number,))
            current_numbers = self.cursor.fetchone()

            # Create and place labels, entry fields, and buttons
            Label(reduce_window, text=f"Batch Number: {batch_number}").grid(row=0, column=0, columnspan=2)

            Label(reduce_window, text="Current Male Pigs:").grid(row=1, column=0)
            males_label = Label(reduce_window, text=current_numbers[0])
            males_label.grid(row=1, column=1)

            Label(reduce_window, text="Current Female Pigs:").grid(row=2, column=0)
            females_label = Label(reduce_window, text=current_numbers[1])
            females_label.grid(row=2, column=1)

            Label(reduce_window, text="Number Slaughtered (Male):").grid(row=3, column=0)
            slaughtered_male_entry = Entry(reduce_window)
            slaughtered_male_entry.grid(row=3, column=1)

            Label(reduce_window, text="Number Slaughtered (Female):").grid(row=4, column=0)
            slaughtered_female_entry = Entry(reduce_window)
            slaughtered_female_entry.grid(row=4, column=1)

            # Add a button to perform the reduction
            reduce_button = ttk.Button(reduce_window, text="Reduce", command=lambda: self.perform_reduction(
                batch_number,
                int(slaughtered_male_entry.get()),
                int(slaughtered_female_entry.get()),
                males_label,
                females_label,
                reduce_window
            ))
            reduce_button.grid(row=5, column=0, columnspan=2)

        except Exception as e:
            logging.error(f"An error occurred while reducing pig numbers: {e}")
            messagebox.showerror("Error", "An unexpected error occurred. Please check the logs.")

    def perform_reduction(self, batch_number, slaughtered_male_count, slaughtered_female_count, males_label, females_label, window):
        try:
            # Fetch current pig numbers for the selected batch
            self.cursor.execute("SELECT males, females FROM pig_registration WHERE batch_number=?", (batch_number,))
            current_numbers = self.cursor.fetchone()

            # Calculate new counts after slaughter
            new_males_count = max(current_numbers[0] - slaughtered_male_count, 0)
            new_females_count = max(current_numbers[1] - slaughtered_female_count, 0)

            # Update the labels
            males_label.config(text=str(new_males_count))
            females_label.config(text=str(new_females_count))

            # Update the database with new counts
            self.cursor.execute("UPDATE pig_registration SET males=?, females=? WHERE batch_number=?", (new_males_count, new_females_count, batch_number))
            self.cursor.execute("INSERT INTO slaughter_information (batch_number, user_id, males_slaughtered, females_slaughtered, avg_weight, date_slaughtered) VALUES (?, ?, ?, ?, ?, ?)",
                                (batch_number, "user123", slaughtered_male_count, slaughtered_female_count, 75.5, datetime.now().date()))
            self.conn.commit()

            # Close the reduce window
            window.destroy()

            # Display a success message
            messagebox.showinfo("Success", "Pig numbers updated successfully!")

            # Refresh the batches for slaughter display
            self.slaughter_text_widget.delete(1.0, "end")
            self.display_batches_for_slaughter()

        except Exception as e:
            logging.error(f"Error updating pig numbers: {e}")
            messagebox.showerror("Error", "Failed to update pig numbers. Please check the logs.")

    def decrease_count(self, label):
        try:
            current_count = int(label.cget("text"))
            if current_count > 0:
                current_count -= 1
                label.config(text=str(current_count))
        except ValueError:
            logging.error("Error while decreasing count: Invalid count value.")
            messagebox.showerror("Error", "Invalid count value. Please check the logs.")

    def update_pig_numbers(self, batch_number, new_males, new_females, user_id, avg_weight, date_slaughtered, window):
        try:
            # Update pig numbers and additional information in the database
            self.cursor.execute("UPDATE pig_registration SET males=?, females=? WHERE batch_number=?", (new_males, new_females, batch_number))
            self.cursor.execute("INSERT INTO slaughter_information (batch_number, user_id, males_slaughtered, females_slaughtered, avg_weight, date_slaughtered) VALUES (?, ?, ?, ?, ?, ?)",
                                (batch_number, user_id, 0, 0, avg_weight, date_slaughtered))
            self.conn.commit()

            # Close the reduce window
            window.destroy()

            # Display a success message
            messagebox.showinfo("Success", "Pig numbers and information updated successfully!")

            # Refresh the batches for slaughter display
            self.slaughter_text_widget.delete(1.0, "end")
            self.display_batches_for_slaughter()

        except Exception as e:
            logging.error(f"Error updating pig numbers and information: {e}")
            messagebox.showerror("Error", "Failed to update pig numbers and information. Please check the logs.")

    def view_slaughtered_batches(self):
        slaughtered_batches_view_app = SlaughteredBatchesViewApp(Toplevel(), self.conn)
        slaughtered_batches_view_app.display_slaughtered_batches()

class SlaughteredBatchesViewApp:
    def __init__(self, window, conn):
        self.window = window
        self.window.title("Slaughtered Batches View")
        self.conn = conn
        self.cursor = conn.cursor()

        # Create and place labels, text widget, and buttons
        Label(window, text="Slaughtered Batches Information:").grid(row=0, column=0)

        self.slaughtered_text_widget = Text(window, wrap="none")
        self.slaughtered_text_widget.grid(row=1, column=0, columnspan=2, sticky="nsew")

        self.slaughtered_text_widget.config(wrap="none")  # Disable automatic line wrapping

        # Add a close button to the window
        close_button = ttk.Button(window, text="Close", command=self.window.destroy)
        close_button.grid(row=2, column=0, columnspan=2)

        # Add a scrollbar for better navigation
        scrollbar = ttk.Scrollbar(window, command=self.slaughtered_text_widget.yview)
        self.slaughtered_text_widget.config(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=1, column=2, sticky="ns")

        # Update the window to handle resizing
        self.window.update_idletasks()

        # Configure weight for resizing
        self.window.grid_rowconfigure(1, weight=1)
        self.window.grid_columnconfigure(0, weight=1)

    def display_slaughtered_batches(self):
        try:
            # Fetch slaughtered batches information from the database
            self.cursor.execute("SELECT batch_number, user_id, males_slaughtered, females_slaughtered, avg_weight, date_slaughtered FROM slaughter_information")
            slaughtered_data = self.cursor.fetchall()

            # Display titles including the new column
            titles = ["Batch Number", "User ID", "Males Slaughtered", "Females Slaughtered", "Average Weight", "Date Slaughtered", "Number Slaughtered"]
            for col, title in enumerate(titles):
                self.slaughtered_text_widget.insert("end", f"{title}\t\t")
                self.slaughtered_text_widget.tag_add("title", f"1.{col*18}", f"1.{(col+1)*18}")
                self.slaughtered_text_widget.tag_config("title", font=('bold', 10), underline=True)
            self.slaughtered_text_widget.insert("end", "\n\n")

            # Display slaughtered batches information in the text widget
            if slaughtered_data:
                for row, batch in enumerate(slaughtered_data, start=2):
                    # Fetch the number slaughtered from the corresponding batch ready for slaughter
                    self.cursor.execute("SELECT COUNT(*) FROM slaughter_information WHERE batch_number=?", (batch[0],))
                    number_slaughtered = self.cursor.fetchone()[0]

                    for col, value in enumerate(batch):
                        self.slaughtered_text_widget.insert("end", f"{value}\t\t")
                    # Display the number slaughtered in the new column
                    self.slaughtered_text_widget.insert("end", f"{number_slaughtered}\t\t")
                    self.slaughtered_text_widget.insert("end", "\n")
            else:
                self.slaughtered_text_widget.insert("end", "No slaughtered batches.")

        except Exception as e:
            logging.error(f"An error occurred while displaying slaughtered batches: {e}")

if __name__ == "__main__":
    slaughter_view_app = SlaughterViewApp(Tk())
    slaughter_view_app.window.mainloop()
