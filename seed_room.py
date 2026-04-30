import sqlite3

def add_test_rooms():
  
    conn = sqlite3.connect('luckynest.db')
    cursor = conn.cursor()


    rooms_data = [
        ('101', '1', 'Deluxe Suite', 450.00, 1600.00, 200.00, '1'),
        ('205', '2', 'Standard Single', 250.00, 900.00, 100.00, '1'),
        ('310', '3', 'Penthouse', 850.00, 3200.00, 500.00, '1')
    ]

   
    cursor.executemany('''
        INSERT INTO Room (RoomNo, FloorLevel, RoomType, WeeklyRate, MonthlyRate, SecurityDeposit, IsAvailable)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', rooms_data)

   
    conn.commit()
    conn.close()
    
    print("✅ Successfully added 3 test rooms to the database!")

if __name__ == '__main__':
    add_test_rooms()