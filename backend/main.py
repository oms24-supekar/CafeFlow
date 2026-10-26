from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import os
import sqlite3
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

BASE = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get('CAFEFLOW_DB', str(BASE / 'cafeflow.sqlite3')))

MENU = [
    {'id': 1, 'name': 'Masala Chai', 'price': 20, 'category': 'Drinks', 'emoji': '☕', 'description': 'Freshly brewed Indian chai'},
    {'id': 2, 'name': 'Cold Coffee', 'price': 80, 'category': 'Drinks', 'emoji': '🥤', 'description': 'Chilled café-style coffee'},
    {'id': 3, 'name': 'Veg Sandwich', 'price': 60, 'category': 'Snacks', 'emoji': '🥪', 'description': 'Toasted with fresh vegetables'},
    {'id': 4, 'name': 'Cheese Maggi', 'price': 70, 'category': 'Snacks', 'emoji': '🍜', 'description': 'Classic noodles with cheese'},
    {'id': 5, 'name': 'Veg Burger', 'price': 90, 'category': 'Meals', 'emoji': '🍔', 'description': 'Crispy veggie patty'},
    {'id': 6, 'name': 'French Fries', 'price': 75, 'category': 'Snacks', 'emoji': '🍟', 'description': 'Golden, seasoned fries'},
    {'id': 7, 'name': 'Paneer Wrap', 'price': 120, 'category': 'Meals', 'emoji': '🌯', 'description': 'Spicy paneer and vegetables'},
    {'id': 8, 'name': 'Chocolate Brownie', 'price': 85, 'category': 'Desserts', 'emoji': '🍫', 'description': 'Rich chocolate treat'},
]
MENU_BY_ID = {item['id']: item for item in MENU}

@contextmanager
def db():
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with db() as conn:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'new',
                payment_method TEXT NOT NULL,
                payment_status TEXT NOT NULL DEFAULT 'unverified',
                total INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                unit_price INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id)
            );
        ''')
        conn.commit()

init_db()
app = FastAPI(title='CafeFlow MVP API', version='0.1.0')
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173', 'http://127.0.0.1:5173'],
    allow_methods=['GET', 'POST', 'PATCH'],
    allow_headers=['Content-Type'],
)

class LineItem(BaseModel):
    product_id: int
    quantity: int = Field(ge=1, le=20)

class CreateOrder(BaseModel):
    items: list[LineItem] = Field(min_length=1, max_length=30)
    payment_method: Literal['cash', 'upi'] = 'cash'

class UpdateStatus(BaseModel):
    status: Literal['new', 'preparing', 'ready', 'completed', 'cancelled']

def load_order(conn, order_id: int):
    order = conn.execute('SELECT * FROM orders WHERE id=?', (order_id,)).fetchone()
    if not order:
        raise HTTPException(status_code=404, detail='Order not found')
    items = conn.execute('SELECT product_id,name,unit_price,quantity FROM order_items WHERE order_id=? ORDER BY id', (order_id,)).fetchall()
    return {**dict(order), 'items': [dict(i) for i in items], 'token': f'CF-{order_id:04d}'}

@app.get('/health')
def health():
    return {'status': 'ok'}

@app.get('/menu')
def menu():
    return MENU

@app.post('/orders', status_code=201)
def create_order(payload: CreateOrder):
    if any(line.product_id not in MENU_BY_ID for line in payload.items):
        raise HTTPException(status_code=422, detail='Unknown menu item')
    subtotal = sum(MENU_BY_ID[line.product_id]['price'] * line.quantity for line in payload.items)
    # The server calculates prices. Client-supplied totals must never be trusted.
    with db() as conn:
        try:
            conn.execute('BEGIN IMMEDIATE')
            cursor = conn.execute(
                'INSERT INTO orders(created_at,payment_method,total) VALUES(?,?,?)',
                (datetime.now(timezone.utc).isoformat(), payload.payment_method, subtotal),
            )
            order_id = cursor.lastrowid
            for line in payload.items:
                product = MENU_BY_ID[line.product_id]
                conn.execute(
                    'INSERT INTO order_items(order_id,product_id,name,unit_price,quantity) VALUES(?,?,?,?,?)',
                    (order_id, product['id'], product['name'], product['price'], line.quantity),
                )
            conn.commit()
            return load_order(conn, order_id)
        except Exception:
            conn.rollback()
            raise

@app.get('/orders')
def list_orders():
    with db() as conn:
        rows = conn.execute('SELECT id FROM orders ORDER BY id DESC LIMIT 100').fetchall()
        return [load_order(conn, row['id']) for row in rows]

@app.get('/orders/{order_id}')
def get_order(order_id: int):
    with db() as conn:
        return load_order(conn, order_id)

@app.patch('/orders/{order_id}/status')
def update_status(order_id: int, payload: UpdateStatus):
    # Demo-only: add staff authentication/authorization before production use.
    with db() as conn:
        existing = conn.execute('SELECT id FROM orders WHERE id=?', (order_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail='Order not found')
        conn.execute('UPDATE orders SET status=? WHERE id=?', (payload.status, order_id))
        conn.commit()
        return load_order(conn, order_id)
