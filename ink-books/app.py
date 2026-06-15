from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
import pandas as pd

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
        name TEXT,
        shop TEXT,
        mobile TEXT,
        designs TEXT,
        quantity TEXT,
        message TEXT
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

@app.route("/submit", methods=["POST"])
def submit():

    name = request.form["name"]
    shop = request.form["shop"]
    mobile = request.form["mobile"]

    # NAME VALIDATION
    if not name.replace(" ", "").isalpha():

        return render_template(
            "error.html",
            title="Invalid Name",
            message="Name should contain only letters."
        )

    # SHOP VALIDATION
    if len(shop.strip()) < 3:

        return render_template(
            "error.html",
            title="Invalid Shop Name",
            message="Please enter a valid shop name."
        )

    # MOBILE VALIDATION
    if len(mobile) != 10 or not mobile.isdigit():

        return render_template(
            "error.html",
            title="Invalid Mobile Number",
            message="Please enter a valid 10-digit mobile number."
        )

    # INDIAN MOBILE VALIDATION
    if mobile[0] not in "6789":

        return render_template(
            "error.html",
            title="Invalid Mobile Number",
            message="Indian mobile numbers must start with 6, 7, 8 or 9."
        )
    message = request.form["message"]

    selected_designs = []

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
    for design, qty in products.items():
        if qty and qty.strip() != "" and int(qty) > 0:
            selected_designs.append(f"{design} - {qty}")

    designs = ", ".join(selected_designs)

    quantity = str(
        sum(
            int(qty)
            for qty in products.values()
            if qty and qty.strip() != ""
        )
    )

    conn = sqlite3.connect("leads.db")

    conn.execute(
        """
        INSERT INTO inquiries
        (name, shop, mobile, designs, quantity, message)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            name,
            shop,
            mobile,
            designs,
            quantity,
            message
        )
    )

    conn.commit()
    conn.close()

    return render_template("thankyou.html")
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