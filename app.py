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
# LOGIN
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
    <a href='/login'>Try Again</a>
    """


# ==========================
# LOGOUT
# ==========================

@app.route("/logout")
def logout():

    session.pop("admin", None)

    return redirect("/login")


# ==========================
# SUBMIT ORDER
# ==========================

@app.route("/submit", methods=["POST"])
def submit():

    name = request.form.get("name", "").strip()
    shop = request.form.get("shop", "").strip()
    mobile = request.form.get("mobile", "").strip()
    message = request.form.get("message", "").strip()

    created_at = datetime.now().strftime("%d-%m-%Y %I:%M %p")

    products = {
        "Breaking Bad Edition": request.form.get("breaking-bad_qty"),
        "BTS Edition": request.form.get("bts_qty"),
        "Minions Edition": request.form.get("minions_qty"),
        "Virat Kohli Edition": request.form.get("virat_kohli_qty"),
        "Free Fire Edition": request.form.get("free_fire_qty"),
        "Squid Game Edition": request.form.get("squid_game_qty"),
        "Jack Sparrow Edition": request.form.get("jack_sparrow_qty"),
        "Krishna Edition": request.form.get("krishna_qty"),
        "Viro Edition": request.form.get("viro_qty"),
        "Money Heist Edition": request.form.get("money_heist_qty"),
        "Shiva Edition": request.form.get("shiva_qty"),
        "Unicorn Edition": request.form.get("unicorn_qty")
    }

    selected_designs = []
    total_quantity = 0

    for design, qty in products.items():

        if qty and qty.strip():

            try:
                qty_num = int(qty)

                if qty_num > 0:
                    selected_designs.append(
                        f"{design} - {qty_num}"
                    )
                    total_quantity += qty_num

            except:
                pass

    if total_quantity == 0:
        return """
        <h2>Please select at least one notebook quantity.</h2>
        <a href="/">Go Back</a>
        """

    designs = ", ".join(selected_designs)

    order_id = "INK-" + str(
        random.randint(1000, 9999)
    )

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

📦 Quantity: {total_quantity}

📝 Message:
{message}

🕒 Date:
{created_at}
"""

    try:
        if BOT_TOKEN and CHAT_ID:

            requests.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                params={
                    "chat_id": CHAT_ID,
                    "text": telegram_message
                }
            )

    except:
        pass

    conn = sqlite3.connect("leads.db")

    conn.execute(
        """
        INSERT INTO inquiries
        (
            order_id,
            name,
            shop,
            mobile,
            designs,
            quantity,
            message,
            created_at,
            status
        )
        VALUES(?,?,?,?,?,?,?,?,?)
        """,
        (
            order_id,
            name,
            shop,
            mobile,
            designs,
            str(total_quantity),
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
    )


# ==========================
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

    return render_template(
        "admin.html",
        data=data
    )


# ==========================
# UPDATE STATUS
# ==========================

@app.route("/update_status/<int:id>", methods=["POST"])
def update_status(id):

    if not session.get("admin"):
        return redirect("/login")

    status = request.form["status"]

    conn = sqlite3.connect("leads.db")

    conn.execute(
        "UPDATE inquiries SET status=? WHERE id=?",
        (status, id)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")


# ==========================
# TRACK ORDER
# ==========================

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
# DELETE
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


# ==========================
# EXPORT EXCEL
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
# RUN
# ==========================

if __name__ == "__main__":
    app.run(debug=True)