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

    # Guest dashboard
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT b.BookingID, b.CheckInDate, b.CheckOutDate, b.Status,
               r.RoomNo, r.RoomType, r.MonthlyRate, r.WeeklyRate
        FROM Booking b
        JOIN Room r ON b.RoomID = r.RoomID
        JOIN Guest g ON b.GuestID = g.GuestID
        WHERE g.UserID = ?
        ORDER BY b.BookingID DESC LIMIT 1
    ''', (session['user_id'],))
    booking = cursor.fetchone()

    cursor.execute('''
        SELECT p.PaymentDate, p.Amount, p.PayMethod, p.Status
        FROM Payment p
        JOIN Guest g ON p.GuestID = g.GuestID
        WHERE g.UserID = ?
        ORDER BY p.PaymentDate DESC LIMIT 5
    ''', (session['user_id'],))
    recent_payments = cursor.fetchall()

    cursor.execute('''
        SELECT COUNT(*) FROM ServiceRequest sr
        JOIN Guest g ON sr.GuestID = g.GuestID
        WHERE g.UserID = ? AND sr.Status = 'Pending'
    ''', (session['user_id'],))
    active_requests = cursor.fetchone()[0]

    cursor.execute('''
        SELECT mp.PlanName, ms.Status
        FROM MealSubscription ms
        JOIN MealPlan mp ON ms.PlanID = mp.PlanID
        JOIN Guest g ON ms.GuestID = g.GuestID
        WHERE g.UserID = ? AND ms.Status = 'Active'
        LIMIT 1
    ''', (session['user_id'],))
    meal_plan = cursor.fetchone()

    cursor.execute('''
        SELECT * FROM Announcement ORDER BY AnnouncementDate DESC LIMIT 3
    ''')
    latest_announcements = cursor.fetchall()

    conn.close()
    return render_template('dashboard.html',
        booking=booking,
        recent_payments=recent_payments,
        active_requests=active_requests,
        meal_plan=meal_plan,
        latest_announcements=latest_announcements
    )

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

        try:
            guest = conn.execute('SELECT GuestID FROM Guest WHERE UserID = ?',
                                 (session['user_id'],)).fetchone()
            if not guest:
                flash('Guest profile not found.', 'error')
                return redirect(url_for('dashboard'))

            conn.execute('''
                INSERT INTO Booking (GuestID, RoomID, CheckInDate, CheckOutDate, Status)
                VALUES (?, ?, ?, ?, 'Pending')
            ''', (guest['GuestID'], room_id, check_in, check_out))
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

@app.route('/payments')
def payments():
    if 'user_id' not in session or session['role'] != 'Owner':
        return redirect(url_for('login'))
    conn = get_db()
    all_payments = conn.execute('''
        SELECT p.PaymentID, g.FirstName, g.LastName, r.RoomNo,
               p.Amount, p.PayMethod, p.Status, p.PaymentDate,
               p.LateFeeApplied, p.LateFeeAmount
        FROM Payment p
        JOIN Guest g ON p.GuestID = g.GuestID
        JOIN Room r ON p.RoomID = r.RoomID
        ORDER BY p.PaymentDate DESC
    ''').fetchall()
    conn.close()
    return render_template('payments.html', payments=all_payments)

@app.route('/add_payment', methods=['GET', 'POST'])
def add_payment():
    if 'user_id' not in session or session['role'] != 'Owner':
        return redirect(url_for('login'))
    conn = get_db()
    if request.method == 'POST':
        guest_id = request.form['GuestID']
        booking_id = request.form['BookingID']
        room_id = request.form['RoomID']
        amount = request.form['Amount']
        pay_method = request.form['PayMethod']
        status = request.form['Status']
        late_fee = request.form.get('LateFeeAmount', 0) or 0
        late_fee_applied = 1 if float(late_fee) > 0 else 0
        try:
            conn.execute('''
                INSERT INTO Payment (GuestID, RoomID, BookingID, Amount, PayMethod, Status, LateFeeApplied, LateFeeAmount)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (guest_id, room_id, booking_id, amount, pay_method, status, late_fee_applied, late_fee))
            conn.commit()
            flash('Payment recorded successfully!', 'success')
        except Exception as e:
            flash('Error recording payment.', 'error')
            print(e)
        finally:
            conn.close()
        return redirect(url_for('payments'))

    bookings = conn.execute('''
        SELECT b.BookingID, g.FirstName, g.LastName, r.RoomNo, r.RoomID, g.GuestID
        FROM Booking b
        JOIN Guest g ON b.GuestID = g.GuestID
        JOIN Room r ON b.RoomID = r.RoomID
    ''').fetchall()
    conn.close()
    return render_template('add_payment.html', bookings=bookings)

@app.route('/announcements')
def announcements():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    all_announcements = conn.execute('''
        SELECT * FROM Announcement ORDER BY AnnouncementDate DESC
    ''').fetchall()
    conn.close()
    return render_template('announcements.html', announcements=all_announcements)

@app.route('/add_announcement', methods=['GET', 'POST'])
def add_announcement():
    if 'user_id' not in session or session['role'] != 'Owner':
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['Title']
        announcement_type = request.form['AnnouncementType']
        description = request.form['Description']
        conn = get_db()
        try:
            conn.execute('''
                INSERT INTO Announcement (Title, AnnouncementType, AnnouncementDate, Description)
                VALUES (?, ?, CURRENT_TIMESTAMP, ?)
            ''', (title, announcement_type, description))
            conn.commit()
            flash('Announcement posted!', 'success')
        except Exception as e:
            flash('Error posting announcement.', 'error')
            print(e)
        finally:
            conn.close()
        return redirect(url_for('announcements'))
    return render_template('add_announcement.html')

@app.route('/delete_announcement/<int:announcement_id>')
def delete_announcement(announcement_id):
    if 'user_id' not in session or session['role'] != 'Owner':
        return redirect(url_for('login'))
    conn = get_db()
    conn.execute('DELETE FROM Announcement WHERE AnnouncementID = ?', (announcement_id,))
    conn.commit()
    conn.close()
    flash('Announcement deleted.', 'success')
    return redirect(url_for('announcements'))

@app.route('/meal_plans')
def meal_plans():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    plans = conn.execute('SELECT * FROM MealPlan').fetchall()
    guest = conn.execute('SELECT GuestID FROM Guest WHERE UserID = ?',
                         (session['user_id'],)).fetchone()
    subscription = None
    if guest:
        subscription = conn.execute('''
            SELECT ms.*, mp.PlanName FROM MealSubscription ms
            JOIN MealPlan mp ON ms.PlanID = mp.PlanID
            WHERE ms.GuestID = ? AND ms.Status = 'Active'
        ''', (guest['GuestID'],)).fetchone()
    conn.close()
    return render_template('meal_plans.html', plans=plans,
                           subscription=subscription)

@app.route('/subscribe_meal/<int:plan_id>')
def subscribe_meal(plan_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    try:
        guest = conn.execute('SELECT GuestID FROM Guest WHERE UserID = ?',
                             (session['user_id'],)).fetchone()
        if guest:
            conn.execute("UPDATE MealSubscription SET Status = 'Inactive' WHERE GuestID = ?",
                         (guest['GuestID'],))
            conn.execute('''
                INSERT INTO MealSubscription (GuestID, PlanID, StartDate, Status)
                VALUES (?, ?, DATE('now'), 'Active')
            ''', (guest['GuestID'], plan_id))
            conn.commit()
            flash('Meal plan subscribed!', 'success')
    except Exception as e:
        flash('Error subscribing to meal plan.', 'error')
        print(e)
    finally:
        conn.close()
    return redirect(url_for('meal_plans'))

@app.route('/services')
def services():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    all_services = conn.execute('SELECT * FROM Service').fetchall()
    conn.close()
    return render_template('services.html', services=all_services)

@app.route('/request_service', methods=['GET', 'POST'])
def request_service():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    if request.method == 'POST':
        service_id = request.form['ServiceID']
        details = request.form['RequestDetails']
        try:
            guest = conn.execute('SELECT GuestID FROM Guest WHERE UserID = ?',
                                 (session['user_id'],)).fetchone()
            booking = conn.execute('''
                SELECT RoomID FROM Booking WHERE GuestID = ?
                ORDER BY BookingID DESC LIMIT 1
            ''', (guest['GuestID'],)).fetchone()
            if not guest or not booking:
                flash('You need an active booking to request services.', 'error')
                return redirect(url_for('dashboard'))
            conn.execute('''
                INSERT INTO ServiceRequest (ServiceID, GuestID, RoomID, RequestDetails, RequestDate, Status)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, 'Pending')
            ''', (service_id, guest['GuestID'], booking['RoomID'], details))
            conn.commit()
            flash('Service request submitted!', 'success')
        except Exception as e:
            flash('Error submitting request.', 'error')
            print(e)
        finally:
            conn.close()
        return redirect(url_for('dashboard'))

    all_services = conn.execute('SELECT * FROM Service').fetchall()
    conn.close()
    return render_template('request_service.html', services=all_services)

@app.route('/my_profile')
def my_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    guest = conn.execute('''
        SELECT g.*, u.Email as UserEmail, u.Role
        FROM Guest g
        JOIN User u ON g.UserID = u.UserID
        WHERE g.UserID = ?
    ''', (session['user_id'],)).fetchone()
    conn.close()
    return render_template('my_profile.html', guest=guest)

@app.route('/visitor_entry', methods=['GET', 'POST'])
def visitor_entry():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    if request.method == 'POST':
        visitor_name = request.form['VisitorName']
        id_type = request.form['IDType']
        id_number = request.form['NumberOfID']
        purpose = request.form['VisitPurpose']
        time_in = request.form['TimeIn']
        time_out = request.form['TimeOut']
        try:
            guest = conn.execute('SELECT GuestID FROM Guest WHERE UserID = ?',
                                 (session['user_id'],)).fetchone()
            booking = conn.execute('''
                SELECT RoomID FROM Booking WHERE GuestID = ?
                ORDER BY BookingID DESC LIMIT 1
            ''', (guest['GuestID'],)).fetchone()
            if not guest or not booking:
                flash('You need an active booking to log visitors.', 'error')
                return redirect(url_for('dashboard'))
            conn.execute('''
                INSERT INTO Visitor (VisitorName, IDType, NumberOfID, VisitPurpose)
                VALUES (?, ?, ?, ?)
            ''', (visitor_name, id_type, id_number, purpose))
            visitor_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
            conn.execute('''
                INSERT INTO VisitorLog (VisitorID, GuestID, RoomID, TimeIn, TimeOut, GuestApprovalStatus)
                VALUES (?, ?, ?, ?, ?, 'Approved')
            ''', (visitor_id, guest['GuestID'], booking['RoomID'], time_in, time_out))
            conn.commit()
            flash('Visitor logged successfully!', 'success')
        except Exception as e:
            flash('Error logging visitor.', 'error')
            print(e)
        finally:
            conn.close()
        return redirect(url_for('dashboard'))

    guest = conn.execute('SELECT GuestID FROM Guest WHERE UserID = ?',
                         (session['user_id'],)).fetchone()
    visitor_logs = []
    if guest:
        visitor_logs = conn.execute('''
            SELECT v.VisitorName, v.VisitPurpose, vl.TimeIn, vl.TimeOut, vl.GuestApprovalStatus
            FROM VisitorLog vl
            JOIN Visitor v ON vl.VisitorID = v.VisitorID
            WHERE vl.GuestID = ?
            ORDER BY vl.TimeIn DESC
        ''', (guest['GuestID'],)).fetchall()
    conn.close()
    return render_template('visitor_entry.html', visitor_logs=visitor_logs)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)