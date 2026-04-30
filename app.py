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

@app.route('/bookings')
def bookings():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    all_bookings = conn.execute('''
        SELECT b.BookingID, g.FirstName, g.LastName, r.RoomNo, 
               b.CheckInDate, b.CheckOutDate, b.Status
        FROM Booking b
        JOIN Guest g ON b.GuestID = g.GuestID
        JOIN Room r ON b.RoomID = r.RoomID
        ORDER BY b.BookingID DESC
    ''').fetchall()
    conn.close()
    return render_template('bookings.html', bookings=all_bookings)

@app.route('/book_room', methods=['GET', 'POST'])
def book_room():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()

    if request.method == 'POST':
        room_id = request.form['room_id']
        check_in = request.form['check_in']
        check_out = request.form['check_out']
        status = 'Pending'

        try:
            guest = conn.execute('SELECT GuestID FROM Guest WHERE UserID = ?', 
                                 (session['user_id'],)).fetchone()
            if not guest:
                flash('Guest profile not found.', 'error')
                return redirect(url_for('dashboard'))

            conn.execute('''
                INSERT INTO Booking (GuestID, RoomID, CheckInDate, CheckOutDate, Status)
                VALUES (?, ?, ?, ?, ?)
            ''', (guest['GuestID'], room_id, check_in, check_out, status))
            conn.execute("UPDATE Room SET IsAvailable = '0' WHERE RoomID = ?", (room_id,))
            conn.commit()
            flash('Booking confirmed!', 'success')
        except Exception as e:
            flash('Booking failed. Please try again.', 'error')
            print(f"Booking Error: {e}")
        finally:
            conn.close()

        return redirect(url_for('dashboard'))

    selected_room = request.args.get('room_id')
    rooms = conn.execute("SELECT * FROM Room WHERE IsAvailable = '1'").fetchall()
    conn.close()
    return render_template('book_rooms.html', rooms=rooms, selected_room=selected_room)

@app.route('/rooms')
def rooms():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    all_rooms = conn.execute('SELECT * FROM Room ORDER BY RoomNo').fetchall()
    conn.close()
    return render_template('rooms.html', rooms=all_rooms)

@app.route('/add_room', methods=['GET', 'POST'])
def add_room():
    if 'user_id' not in session or session['role'] != 'Owner':
        return redirect(url_for('login'))
    if request.method == 'POST':
        room_no = request.form['RoomNo']
        floor = request.form['FloorLevel']
        room_type = request.form['RoomType']
        weekly_rate = request.form['WeeklyRate']
        monthly_rate = request.form['MonthlyRate']
        security_deposit = request.form['SecurityDeposit']
        conn = get_db()
        try:
            conn.execute('''
                INSERT INTO Room (RoomNo, FloorLevel, RoomType, WeeklyRate, MonthlyRate, SecurityDeposit, IsAvailable)
                VALUES (?, ?, ?, ?, ?, ?, '1')
            ''', (room_no, floor, room_type, weekly_rate, monthly_rate, security_deposit))
            conn.commit()
            flash('Room added successfully!', 'success')
        except Exception as e:
            flash('Error adding room.', 'error')
        finally:
            conn.close()
        return redirect(url_for('rooms'))
    return render_template('add_room.html')

@app.route('/delete_room/<int:room_id>')
def delete_room(room_id):
    if 'user_id' not in session or session['role'] != 'Owner':
        return redirect(url_for('login'))
    conn = get_db()
    conn.execute('DELETE FROM Room WHERE RoomID = ?', (room_id,))
    conn.commit()
    conn.close()
    flash('Room deleted.', 'success')
    return redirect(url_for('rooms'))

@app.route('/guests')
def guests():
    if 'user_id' not in session or session['role'] != 'Owner':
        return redirect(url_for('login'))
    conn = get_db()
    all_guests = conn.execute('''
        SELECT g.GuestID, g.FirstName, g.LastName, g.Email, g.TelNo,
               u.Role, r.RoomNo
        FROM Guest g
        JOIN User u ON g.UserID = u.UserID
        LEFT JOIN Booking b ON g.GuestID = b.GuestID AND b.Status = 'Pending'
        LEFT JOIN Room r ON b.RoomID = r.RoomID
        ORDER BY g.GuestID DESC
    ''').fetchall()
    conn.close()
    return render_template('guests.html', guests=all_guests)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)