import random
from tkinter import Tk, Label, OptionMenu, StringVar, simpledialog, messagebox
import sqlite3
from datetime import datetime

class PigDatabase:
    def __init__(self):
        self.conn, self.cursor = self.initialize_database()

    def initialize_database(self):
        try:
            conn = sqlite3.connect('farm_database.db')
            cursor = conn.cursor()

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
            messagebox.showerror("Database Error", f"Failed to initialize the database: {e}")
            return None, None

    def close_database(self):
        if self.conn:
            self.conn.close()

    def get_pig_batches(self):
        try:
            self.cursor.execute("SELECT batch_number FROM pig_registration")
            batches = self.cursor.fetchall()
            return [batch[0] for batch in batches]

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to fetch batches from the database: {e}")
            return []

    def get_pig_data(self, batch_name):
        try:
            self.cursor.execute("SELECT dob FROM pig_registration WHERE batch_number=?", (batch_name,))
            dob = self.cursor.fetchone()

            if dob is not None:
                dob = datetime.strptime(dob[0], '%Y-%m-%d').date()
                today = datetime.now().date()
                age = (today - dob).days
                return {"batch_number": batch_name, "dob": dob, "age": age}
            else:
                return {"batch_number": "", "dob": None, "age": 0}

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to fetch data from the database: {e}")
            return {"batch_number": "", "dob": None, "age": 0}

class PigCalculatorApp:
    def __init__(self):
        self.pig_db = PigDatabase()
        self.root = Tk()
        self.root.title("Pig Breeding Calculator")
        self.feed_data = [
            (1, 28, "breastfeeding", 0.21),
            (29, 42, "0.00075kg of feed 2", 0.4),
            (43, 56, "1kg of feed 2", 1.0),
            (57, 70, "0.255kg of feed 2", 0.655),
            (71, 85, "1.4kg of feed 3", 0.71),
            (86, 99, "0.805kg of feed 3", 0.805),
            (100, 114, "0.970kg of feed 3", 0.97),
            (115, 128, "1.020kg of feed 3", 1.02),
            (129, 143, "1.120kg of feed 4", 1.12),
            (144, 157, "1.100kg of feed 4", 1.1),
            (158, 240, "2.5kg of feed 4", "")
        ]
        self.selected_batch = StringVar(self.root)  # Make it an instance variable
        self.selected_batch.set(self.pig_db.get_pig_batches()[0])
        self.create_widgets()

    def create_widgets(self):
        pig_batches = self.pig_db.get_pig_batches()

        batch_menu = OptionMenu(self.root, self.selected_batch, *pig_batches)
        batch_menu.pack()

        calculate_button = Label(self.root, text="Calculate Feed", padx=10, pady=5, bg="blue", fg="white")
        calculate_button.pack()
        calculate_button.bind("<Button-1>", self.on_calculate_button_click)

    def on_calculate_button_click(self, event):
        selected_batch_name = self.selected_batch.get()
        selected_batch_data = self.pig_db.get_pig_data(selected_batch_name)
        pig_age = selected_batch_data['age']

        result = self.calculate_expected_weight_and_food(pig_age)

        self.display_result_in_window(result)

    def calculate_expected_weight_and_food(self, age_in_days):
        expected_weight = 0

        for start_day, end_day, _, weight_gain_per_day in self.feed_data:
            if start_day <= age_in_days:
                period_start = max(start_day, 1)
                period_end = min(age_in_days, end_day)
                period_days = max(0, period_end - period_start + 1)

                if isinstance(weight_gain_per_day, float):
                    expected_weight += weight_gain_per_day * period_days
                else:
                    expected_weight += round(random.uniform(1.5, 2.5) * period_days, 3)

        current_feed = self.determine_feed_for_age(age_in_days)

        actual_weight = simpledialog.askfloat("Input", "Enter the actual weight of the pig:")

        health_status = "Excellent" if actual_weight >= expected_weight else "Critical" if actual_weight < (expected_weight - 10) else "Average"

        return {
            "expected_weight": round(expected_weight, 3),
            "actual_weight": actual_weight,
            "health_status": health_status,
            "recommended_feed": current_feed
        }

    def determine_feed_for_age(self, age_in_days):
        for start_day, end_day, feed_description, _ in self.feed_data:
            if start_day <= age_in_days <= end_day:
                if isinstance(_, float):
                    return feed_description
                else:
                    return round(random.uniform(1.5, 2.5), 3)
        return None

    def display_result_in_window(self, result):
        result_window = Tk()
        result_window.title("Calculation Result")

        result_label = Label(result_window, text=f"Expected Weight: {result['expected_weight']}\nActual Weight: {result['actual_weight']}\nRecommended Feed: {result['recommended_feed']}\nHealth Status: {result['health_status']}")
        result_label.pack()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    try:
        pig_app = PigCalculatorApp()
        pig_app.run()
    finally:
        pig_app.pig_db.close_database()
