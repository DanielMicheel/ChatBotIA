# database.py
import sqlite3

def get_connection():
    return sqlite3.connect("cars.db")

def get_all_cars():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM cars WHERE available = 1;")
    cars = cur.fetchall()
    conn.close()
    return cars

def get_cars_by_seats(required_seats):
    conn = get_connection()
    cur = conn.cursor()
    query = "SELECT * FROM cars WHERE available = 1 AND seats >= ?;"
    cur.execute(query, (required_seats,))
    cars = cur.fetchall()
    conn.close()
    return cars

def get_cars_by_budget(max_rate):
    conn = get_connection()
    cur = conn.cursor()
    query = "SELECT * FROM cars WHERE available = 1 AND daily_rate <= ?;"
    cur.execute(query, (max_rate,))
    cars = cur.fetchall()
    conn.close()
    return cars

def get_business_info():
    """Retorna uma tupla (company_name, info_text) com as informações da empresa."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT company_name, info_text FROM business_info LIMIT 1;")
    business = cur.fetchone()
    conn.close()
    return business
