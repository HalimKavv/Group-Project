from flask import Flask, render_template, request, redirect, url_for, session, flash
import hashlib
from database import get_db, init_db

app = Flask(__name__)
app.secret_key = 'luckynest_secret_key'

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['FirstName']
        last_name = request.form['LastName']
        email = request.form['Email']
        tel_no = request.form['TelNo']
        password = request.form['Password']
        confirm_password = request.form['confirmPassword']

        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('register.html')

        hashed_pw = hash_password(password)

        try:
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO User (FirstName, LastName, Email, TelNo, Role, Password)
                VALUES (?, ?, ?, ?, 'Guest', ?)
            ''', (first_name, last_name, email, tel_no, hashed_pw))

            user_id = cursor.lastrowid

            cursor.execute('''
                INSERT INTO Guest (UserID, FirstName, LastName, Email, TelNo)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, first_name, last_name, email, tel_no))

            conn.commit()
            conn.close()

            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            flash('Email or phone number already exists.', 'error')
            return render_template('register.html')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['Email']
        password = hash_password(request.form['Password'])

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM User WHERE Email = ? AND Password = ?', (email, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['user_id'] = user['UserID']
            session['user_name'] = user['FirstName']
            session['role'] = user['Role']
            flash(f"Welcome back, {user['FirstName']}!", 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if session['role'] == 'Owner':
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM Guest")
        total_guests = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM User")
        total_users = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(Amount) FROM Payment")
        total_revenue = cursor.fetchone()[0] or 0

        cursor.execute("SELECT SUM(Amount) FROM Payment WHERE Status = 'Pending'")
        pending_revenue = cursor.fetchone()[0] or 0

        cursor.execute("SELECT SUM(Amount) FROM Payment WHERE Status = 'Paid'")
        paid_revenue = cursor.fetchone()[0] or 0

        cursor.execute("SELECT SUM(Amount) FROM Payment WHERE Status = 'Overdue'")
        overdue_revenue = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM Room")
        total_rooms = cursor.fetchone()[0] or 50

        cursor.execute("SELECT COUNT(*) FROM Room WHERE IsAvailable = '0'")
        occupied_rooms = cursor.fetchone()[0] or 0

        occupancy_rate = round((occupied_rooms / total_rooms * 100)) if total_rooms > 0 else 0
        collection_rate = round((paid_revenue / total_revenue * 100)) if total_revenue > 0 else 0

        cursor.execute('''
            SELECT g.FirstName, g.LastName, g.Email, g.TelNo
            FROM Guest g
            ORDER BY g.GuestID DESC
            LIMIT 5
        ''')
        recent_guests = cursor.fetchall()

        conn.close()

        return render_template('owner_dashboard.html',
            total_guests=total_guests,
            total_users=total_users,
            total_revenue=total_revenue,
            pending_revenue=pending_revenue,
            paid_revenue=paid_revenue,
            overdue_revenue=overdue_revenue,
            total_rooms=total_rooms,
            occupied_rooms=occupied_rooms,
            occupancy_rate=occupancy_rate,
            collection_rate=collection_rate,
            recent_guests=recent_guests
        )
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('home'))
@app.route('/notifications')
def notifications():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('notifications.html')
if __name__ == '__main__':
    init_db()
    app.run(debug=True)