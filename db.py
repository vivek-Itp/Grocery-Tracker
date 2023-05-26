import sqlite3
from helpers import get_iso_from_slovak_dt_str
db_fp = 'receipts.db'
schema_fp = 'receipts_schema.sql'


def load_db_schema(conn, schema_fp):
    with open(schema_fp) as fp:
        conn.executescript(fp.read())


class Database:
    conn = sqlite3.connect(db_fp)
    load_db_schema(conn, schema_fp)

    def __init__(self):
        # Unique cursor for every Database instance
        self.cur = Database.conn.cursor()

    def get_person_id_name(self, phone: str):
        # Get person by phone number
        sql = ' SELECT person_id, name FROM person WHERE phone=? '
        person_result = self.cur.execute(sql, [phone]).fetchone()

        if person_result is None:
            # REGISTER NEW PERSON
            name = input("You're new! Please type in your name: ")
            insert_person_sql = " INSERT INTO person(phone, name) VALUES(?,?) "
            self.cur.execute(insert_person_sql, [phone, name])
            Database.conn.commit()

            person_id = self.cur.lastrowid
        else:
            person_id, name = person_result
            print(f'Welcome back, {name}!')

        return person_id, name

    def save_receipt(self, receipt, person):
        if not receipt.total or not receipt.grocery_list:
            raise ValueError('Receipt is empty')

        # Insert info into receipt table
        sql = ''' INSERT INTO receipt(person_id, shop_name, total, shopping_date) VALUES(?,?,?,?) '''
        receipt_task = (person.id, receipt.shop, receipt.total, get_iso_from_slovak_dt_str(receipt.shopping_date))
        self.cur.execute(sql, receipt_task)
        receipt_id = self.cur.lastrowid

        # DELETE orphan items
        self.cur.execute('DELETE FROM item WHERE receipt_id NOT IN (SELECT receipt_id FROM receipt)')

        sql = ''' INSERT INTO item(name, price, amount, receipt_id) VALUES(?,?,?,?) '''
        # Insert items into DB
        for item in receipt.grocery_list:
            print(item)
            item_task = (item['name'], item['final_price'], item['amount'], receipt_id)
            self.cur.execute(sql, item_task)

        Database.conn.commit()

