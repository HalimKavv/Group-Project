import sqlite3

conn = sqlite3.connect('luckynest.db')
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

    CREATE TABLE IF NOT EXISTS Room (
        RoomID INTEGER PRIMARY KEY AUTOINCREMENT,
        RoomNo VARCHAR(10) NOT NULL,
        FloorLevel VARCHAR(10) NOT NULL,
        RoomType VARCHAR(20) NOT NULL,
        WeeklyRate DECIMAL(10,2) NOT NULL,
        MonthlyRate DECIMAL(10,2) NOT NULL,
        SecurityDeposit DECIMAL(10,2),
        IsAvailable TEXT NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS Booking (
        BookingID INTEGER PRIMARY KEY AUTOINCREMENT,
        GuestID INT NOT NULL,
        RoomID INT NOT NULL,
        BookingDate DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CheckInDate DATE NOT NULL,
        CheckOutDate DATE NOT NULL,
        Status VARCHAR(20) NOT NULL,
        TotalAmount DECIMAL(10,2),
        SecurityDepositPaid TEXT DEFAULT 0,
        FOREIGN KEY (GuestID) REFERENCES Guest(GuestID),
        FOREIGN KEY (RoomID) REFERENCES Room(RoomID)
    );

    CREATE TABLE IF NOT EXISTS Payment (
        PaymentID INTEGER PRIMARY KEY AUTOINCREMENT,
        GuestID INT NOT NULL,
        RoomID INT NOT NULL,
        BookingID INT NOT NULL,
        PaymentDate DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        Amount DECIMAL(10,2) NOT NULL,
        PayMethod VARCHAR(30) NOT NULL,
        Status VARCHAR(20) NOT NULL,
        LateFeeApplied INT DEFAULT 0,
        LateFeeAmount DECIMAL(10,2),
        FOREIGN KEY (GuestID) REFERENCES Guest(GuestID),
        FOREIGN KEY (RoomID) REFERENCES Room(RoomID),
        FOREIGN KEY (BookingID) REFERENCES Booking(BookingID)
    );

    CREATE TABLE IF NOT EXISTS Service (
        ServiceID INTEGER PRIMARY KEY AUTOINCREMENT,
        ServiceName VARCHAR(50) UNIQUE,
        Availability VARCHAR(50),
        ServicePrice VARCHAR(50)
    );

    CREATE TABLE IF NOT EXISTS ServiceRequest (
        RequestID INTEGER PRIMARY KEY AUTOINCREMENT,
        ServiceID INT NOT NULL,
        GuestID INT NOT NULL,
        RoomID INT NOT NULL,
        RequestDetails TEXT NOT NULL,
        RequestDate DATETIME NOT NULL,
        Status VARCHAR(50) NOT NULL DEFAULT 'Pending',
        Cost DECIMAL(10,2),
        FOREIGN KEY (ServiceID) REFERENCES Service(ServiceID),
        FOREIGN KEY (GuestID) REFERENCES Guest(GuestID),
        FOREIGN KEY (RoomID) REFERENCES Room(RoomID)
    );

    CREATE TABLE IF NOT EXISTS MealPlan (
        PlanID INTEGER PRIMARY KEY AUTOINCREMENT,
        PlanName VARCHAR(50),
        PlanPrice DECIMAL(10,2) NOT NULL
    );

    CREATE TABLE IF NOT EXISTS MealSubscription (
        SubscriptionID INTEGER PRIMARY KEY AUTOINCREMENT,
        GuestID INT NOT NULL,
        PlanID INT NOT NULL,
        StartDate DATE NOT NULL,
        EndDate DATE,
        Status VARCHAR(20) NOT NULL DEFAULT 'Pending',
        FOREIGN KEY (GuestID) REFERENCES Guest(GuestID),
        FOREIGN KEY (PlanID) REFERENCES MealPlan(PlanID)
    );

    CREATE TABLE IF NOT EXISTS Visitor (
        VisitorID INTEGER PRIMARY KEY AUTOINCREMENT,
        VisitorName VARCHAR(100) NOT NULL,
        IDType VARCHAR(50) NOT NULL,
        NumberOfID VARCHAR(50) NOT NULL,
        VisitPurpose TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS VisitorLog (
        LogID INTEGER PRIMARY KEY AUTOINCREMENT,
        VisitorID INT NOT NULL,
        GuestID INT NOT NULL,
        RoomID INT NOT NULL,
        TimeIn DATETIME NOT NULL,
        TimeOut DATETIME NOT NULL,
        GuestApprovalStatus VARCHAR(20) NOT NULL DEFAULT 'Pending',
        FOREIGN KEY (VisitorID) REFERENCES Visitor(VisitorID),
        FOREIGN KEY (GuestID) REFERENCES Guest(GuestID),
        FOREIGN KEY (RoomID) REFERENCES Room(RoomID)
    );

    CREATE TABLE IF NOT EXISTS Announcement (
        AnnouncementID INTEGER PRIMARY KEY AUTOINCREMENT,
        Title VARCHAR(150) NOT NULL,
        AnnouncementType VARCHAR(30) NOT NULL,
        AnnouncementDate DATETIME NOT NULL,
        Description TEXT NOT NULL
    );
''')

conn.commit()
conn.close()
print('All tables created!')