from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
import pandas as pd
import random
from datetime import datetime
import requests
import os


app = Flask(__name__)
app.secret_key = "inkbooks_secret_2026"


# ==========================
# DATABASE SETUP
# ==========================

def init_db():
    conn = sqlite3.connect("leads.db")

    conn.execute("""
CREATE TABLE IF NOT EXISTS inquiries(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT,
    name TEXT,
    shop TEXT,
    mobile TEXT,
    designs TEXT,
    quantity TEXT,
    message TEXT,
    created_at TEXT,
    status TEXT DEFAULT 'Pending'
)
""")

    conn.commit()
    conn.close()

init_db()


# ==========================
# HOME PAGE
# ==========================

@app.route("/")
def home():
    return render_template("index.html")


# ==========================
# LOGIN PAGE
# ==========================

@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/login_submit", methods=["POST"])
def login_submit():

    username = request.form["username"]
    password = request.form["password"]

    if username == "Ganesh" and password == "Gani@2026":
        session["admin"] = True
        return redirect("/admin")

    return """
    <h2>Invalid Username or Password</h2>
    <a href="/login">Try Again</a>
    """

# ==========================
# LOGOUT
# ==========================

@app.route("/logout")
def logout():

    session.pop("admin", None)

    return redirect("/login")


# ==========================
# FORM SUBMISSION
# ==========================

    order_id = "INK-" + str(random.randint(1000, 9999))

    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    CHAT_ID = os.environ.get("CHAT_ID")

    telegram_message = f"""
📦 NEW INK BOOKS ORDER

🆔 Order ID: {order_id}

👤 Customer: {name}
🏪 Shop: {shop}
📱 Mobile: {mobile}

📚 Designs:
{designs}

📦 Quantity: {quantity}

📝 Message:
{message}

🕒 Date:
{created_at}
"""

    requests.get(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        params={
            "chat_id": CHAT_ID,
            "text": telegram_message
        }
    )

    conn = sqlite3.connect("leads.db")

    conn.execute(
        """
        INSERT INTO inquiries
        (order_id,name,shop,mobile,designs,quantity,message,created_at,status)
        VALUES(?,?,?,?,?,?,?,?,?)
        """,
        (
            order_id,
            name,
            shop,
            mobile,
            designs,
            quantity,
            message,
            created_at,
            "Pending"
        )
    )

    conn.commit()
    conn.close()

    return render_template(
        "thankyou.html",
        order_id=order_id
    )# ==========================
# ADMIN DASHBOARD
# ==========================

@app.route("/admin")
def admin():

    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("leads.db")

    data = conn.execute(
        "SELECT * FROM inquiries ORDER BY id DESC"
    ).fetchall()

    conn.close()

    total_qty = sum(
        int(row[6]) for row in data
        if str(row[6]).isdigit()
    )

    return render_template(
        "admin.html",
        data=data,
        total_qty=total_qty
    )


@app.route("/track")
def track():
    return render_template("track.html")


@app.route("/track_order", methods=["POST"])
def track_order():

    order_id = request.form["order_id"]

    conn = sqlite3.connect("leads.db")

    order = conn.execute(
        "SELECT * FROM inquiries WHERE order_id=?",
        (order_id,)
    ).fetchone()

    conn.close()

    return render_template(
        "track_result.html",
        order=order
    )

# ==========================
# DELETE INQUIRY
# ==========================

@app.route("/delete/<int:id>")
def delete(id):

    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("leads.db")

    conn.execute(
        "DELETE FROM inquiries WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")

@app.route("/status/<int:id>/<new_status>")
def update_status(id, new_status):

    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("leads.db")

    conn.execute(
        "UPDATE inquiries SET status=? WHERE id=?",
        (new_status, id)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")


# ==========================
# EXPORT TO EXCEL
# ==========================

@app.route("/export")
def export():

    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("leads.db")

    df = pd.read_sql_query(
        "SELECT * FROM inquiries",
        conn
    )

    conn.close()

    file_name = "customer_leads.xlsx"

    df.to_excel(
        file_name,
        index=False
    )

    return send_file(
        file_name,
        as_attachment=True
    )


# ==========================
# RUN APPLICATION
# ==========================

if __name__ == "__main__":
    app.run(debug=True)