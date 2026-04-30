import sqlite3

conn = sqlite3.connect('luckynest.db')
cursor = conn.cursor()

# Meal Plans
cursor.executemany('''
    INSERT OR IGNORE INTO MealPlan (PlanName, PlanPrice) VALUES (?, ?)
''', [
    ('Breakfast Only', 95.00),
    ('Lunch Only', 142.00),
    ('Dinner Only', 142.00),
    ('Full Day', 332.00),
])

# Services
cursor.executemany('''
    INSERT OR IGNORE INTO Service (ServiceName, Availability, ServicePrice) VALUES (?, ?, ?)
''', [
    ('Laundry (per load)', 'On request', '£1.90/load'),
    ('Laundry (weekly unlimited)', 'On request', '£14.25/week'),
    ('Housekeeping (basic)', 'Weekly', '£4.75/session'),
    ('Housekeeping (deep clean)', 'On request', '£9.50/session'),
    ('WiFi', 'All rooms', 'Included'),
    ('Parking', 'Limited', '£28.50/month'),
])

conn.commit()
conn.close()
print('Seed data added!')