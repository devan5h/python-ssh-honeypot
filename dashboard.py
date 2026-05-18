from flask import Flask, render_template
import sqlite3
from database import init_db

init_db()
app = Flask(__name__)

def get_logs():
    conn = sqlite3.connect("honeypot.db")
    c = conn.cursor()
    c.execute("SELECT * FROM attacks ORDER BY timestamp DESC")
    data = c.fetchall()
    conn.close()
    return data

# 🔥 NEW: Stats functions
def get_stats():
    conn = sqlite3.connect("honeypot.db")
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM attacks")
    total = c.fetchone()[0]

    c.execute("SELECT ip, COUNT(*) as count FROM attacks GROUP BY ip ORDER BY count DESC LIMIT 5")
    top_ips = c.fetchall()

    c.execute("SELECT username, COUNT(*) FROM attacks GROUP BY username ORDER BY COUNT(*) DESC LIMIT 5")
    top_users = c.fetchall()

    c.execute("SELECT password, COUNT(*) FROM attacks GROUP BY password ORDER BY COUNT(*) DESC LIMIT 5")
    top_passwords = c.fetchall()

    c.execute("""
    SELECT username, COUNT(*) 
    FROM attacks 
    WHERE password = 'COMMAND'
    GROUP BY username 
    ORDER BY COUNT(*) DESC LIMIT 5
    """)
    top_commands = c.fetchall()

    conn.close()
    return total, top_ips, top_users, top_passwords,top_commands

def get_chart_data():
    conn = sqlite3.connect("honeypot.db")
    c = conn.cursor()

    # Top IPs
    c.execute("SELECT ip, COUNT(*) FROM attacks GROUP BY ip ORDER BY COUNT(*) DESC LIMIT 5")
    ip_data = c.fetchall()

    # Top commands
    c.execute("""
        SELECT username, COUNT(*) 
        FROM attacks 
        WHERE password='COMMAND'
        GROUP BY username 
        ORDER BY COUNT(*) DESC LIMIT 5
    """)
    cmd_data = c.fetchall()

    conn.close()

    return ip_data, cmd_data

@app.route("/")
def index():
    logs = get_logs()
    total, top_ips, top_users, top_passwords, _ = get_stats()
    ip_chart, cmd_chart = get_chart_data()

    return render_template(
        "index.html",
        logs=logs,
        total=total,
        top_ips=top_ips,
        top_users=top_users,
        top_passwords=top_passwords,
        top_commands=cmd_chart,
        ip_chart=ip_chart,
        cmd_chart=cmd_chart
    )
if __name__ == "__main__":
    app.run(debug=True)