import sqlite3
conn = sqlite3.connect('luckynest.db')
conn.execute("UPDATE User SET Role = 'Owner' WHERE Email = 'halim.kavak07@gmail.com'")
conn.commit()
conn.close()
print('Done!')