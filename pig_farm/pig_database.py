# pig_database.py
import sqlite3
from datetime import datetime

class PigDatabase:
    def __init__(self, db_path=None):
        if db_path is None:
            # Use the script directory to create the database file path
            script_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(script_dir, 'pigfarm_database.db')

        sqlite3.register_adapter(datetime.date, lambda x: x.strftime('%Y-%m-%d').encode('utf-8'))
        sqlite3.register_converter('DATE', lambda x: datetime.strptime(x.decode('utf-8'), '%Y-%m-%d').date())

        self.conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        self.c = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.c.execute('''
            CREATE TABLE IF NOT EXISTS pig_records (
                id INTEGER PRIMARY KEY,
                batch_number INTEGER,
                mother_id INTEGER,
                date_born DATE,
                male_pigs INTEGER,
                female_pigs INTEGER,
                age_in_days INTEGER
            )
        ''')
        self.conn.commit()

    def add_record(self, batch_number, mother_id, date_born, male_pigs, female_pigs, age_in_days=None):
        try:
            date_obj = datetime.strptime(date_born, '%Y-%m-%d').date()
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")
            return

        if age_in_days is None:
            age_in_days = (datetime.now().date() - date_obj).days

        try:
            self.c.execute('''
                INSERT INTO pig_records (batch_number, mother_id, date_born, male_pigs, female_pigs, age_in_days)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (batch_number, mother_id, date_obj, male_pigs, female_pigs, age_in_days))
            self.conn.commit()
        except Exception as e:
            print(f"Failed to add record. Error: {str(e)}")

    def delete_record(self, record_id):
        try:
            self.c.execute('DELETE FROM pig_records WHERE id = ?', (record_id,))
            self.conn.commit()
        except Exception as e:
            print(f"Failed to delete record. Error: {str(e)}")

    def get_all_records(self):
        try:
            self.c.execute('SELECT * FROM pig_records')
            return self.c.fetchall()
        except Exception as e:
            print(f"Failed to retrieve records. Error: {str(e)}")
            return []

    def update_age_in_days(self):
        try:
            records = self.get_all_records()
            for record in records:
                record_id, _, _, date_born, _, _, _ = record

                if date_born is not None:
                    date_of_birth = date_born
                    age_in_days = (datetime.now().date() - date_of_birth).days
                    self.c.execute('UPDATE pig_records SET age_in_days = ? WHERE id = ?', (age_in_days, record_id))

            self.conn.commit()
        except Exception as e:
            print(f"Failed to update age in days. Error: {str(e)}")

    def get_all_pig_batches(self):
        try:
            self.c.execute('SELECT DISTINCT batch_number FROM pig_records')
            return [batch[0] for batch in self.c.fetchall()]
        except Exception as e:
            print(f"Failed to retrieve pig batches. Error: {str(e)}")
            return []

    def close_connection(self):
        self.conn.close()

    def get_pig_data_by_batch_number(self, batch_number):
        try:
            self.c.execute('''
                SELECT * FROM pig_records
                WHERE batch_number = ?
            ''', (batch_number,))
            return self.c.fetchone()
        except Exception as e:
            print(f"Failed to retrieve pig data. Error: {str(e)}")
            return None
