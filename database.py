import sqlite3

def get_db():
    conn = sqlite3.connect('luckynest.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS User (
            UserID INTEGER PRIMARY KEY AUTOINCREMENT,
            FirstName VARCHAR(50) NOT NULL,
            LastName VARCHAR(50) NOT NULL,
            Email VARCHAR(50) UNIQUE NOT NULL,
            TelNo VARCHAR(11) UNIQUE NOT NULL,
            Role VARCHAR(100) NOT NULL DEFAULT 'Guest',
            Password VARCHAR(255) NOT NULL
        );

        CREATE TABLE IF NOT EXISTS Guest (
            GuestID INTEGER PRIMARY KEY AUTOINCREMENT,
            UserID INT NOT NULL,
            FirstName VARCHAR(50) NOT NULL,
            LastName VARCHAR(50) NOT NULL,
            Email VARCHAR(50) UNIQUE NOT NULL,
            TelNo VARCHAR(11) UNIQUE NOT NULL,
            Address TEXT,
            IDProofType VARCHAR(50),
            IDNumber VARCHAR(20),
            Occupation VARCHAR(50),
            DOB DATE,
            EmergencyContactName VARCHAR(100),
            EmergencyContactRelationship VARCHAR(50),
            EmergencyContactNumber VARCHAR(20),
            FOREIGN KEY (UserID) REFERENCES User(UserID)
        );
    ''')
    
    conn.commit()
    conn.close()