# dbUtils.py - contains functions for initializing DB (creating DB, tables)
#   connecting/closing connection with DB
#   getting table information (description/contents) 

import os
import mysql.connector
from mysql.connector import errorcode

MYSQL_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
    # 'database': os.getenv('DB_NAME')
}
# DB_NAME = 'contabilitate'
DB_NAME = os.getenv('DB_NAME')

'''
Utils
'''
def dbConnect():
    global MYSQL_CONFIG
    # Connect to mysql server
    cnx = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = cnx.cursor()
    try:
        cursor.execute(f"USE {DB_NAME}")
    except mysql.connector.Error as err:
        print(err)
    return (cnx, cursor)

def dbClose(cnx, cursor):
    # Close cursor and connection
    cursor.close()
    cnx.close()

def getTableDescription(tableName):
    (cnx, cursor) = dbConnect()
    cursor.execute(f"DESC {tableName};")
    tableDesc = "\n".join([str(line) for line in cursor])
    dbClose(cnx, cursor)
    return tableDesc

def getTableContent(tableName):
    (cnx, cursor) = dbConnect()
    cursor.execute(f"SELECT * FROM {tableName};")
    tableContents = "\n".join([str(line) for line in cursor])
    dbClose(cnx, cursor)
    return tableContents

'''
SQL Database and Tables creation

Pentru fiecare zbor se vor retine cel putin urm ̆atoarele informatii:
• ID (de tip String);
• sursa s, i destinat, ia (ambele de tip String);
• ora de plecare (de tip int, ˆıntre 0 s, i 23) - se consider ̆a c ̆a toate plec ̆arile sunt la ore ”fixe”;
• ziua plec ̆arii (de tip int, ˆıntre 1 s, i 365) - se considera ̆ zborurile dintr-un singur an; zborurile din zile
diferite, de la aceeas, i ora, vor avea ID-uri diferite;
• durata zborului (de tip int) - se consider ̆a c ̆a este un num ̆ar ˆıntreg de ore;
• num ̆arul de locuri disponibile.
'''

# TABLES = {}
# TABLES['flights'] = (
#     "CREATE TABLE `flights` ("
#     "  `id` varchar(20) NOT NULL,"
#     "  `source` varchar(50) NOT NULL,"
#     "  `destination` varchar(50) NOT NULL,"
#     "  `day` int(3) NOT NULL,"
#     "  `hour` int(2) NOT NULL,"
#     "  `duration` int(3) NOT NULL,"
#     "  `seats` int(3) NOT NULL,"
#     "  PRIMARY KEY (`id`)"
#     ") ENGINE=InnoDB")
# TABLES['reservations'] = (
#     "CREATE TABLE `reservations` ("
#     "  `id` varchar(20) NOT NULL,"
#     "  `flightId` varchar(20) NOT NULL"
#     ") ENGINE=InnoDB")
# TABLES['tickets'] = (
#     "CREATE TABLE `tickets` ("
#     "  `id` varchar(20) NOT NULL,"
#     "  `resId` varchar(20) NOT NULL,"
#     "  `cardInfo` varchar(50) NOT NULL,"
#     "  PRIMARY KEY (`id`)"
#     ") ENGINE=InnoDB")


### BD2 Project ###
TABLES = {}
TABLES['users'] = (
    "CREATE TABLE `users` ("
    "  `ID` varchar(10) NOT NULL,"
    "  `Username` varchar(64) NOT NULL,"
    "  `Password` varchar(64) NOT NULL,"
    "  `Email` varchar(100) NOT NULL,"
    "  PRIMARY KEY (`ID`)"
    ") ENGINE=InnoDB")

# Brut vs Net
TABLES['contributions'] = (
    "CREATE TABLE `contributions` ("
    "  `Category` varchar(30) NOT NULL,"
    "  `CAS` double(5, 2) NOT NULL,"
    "  `CASS` double(5, 2) NOT NULL,"
    "  `Impozit` double(5, 2) NOT NULL,"
    "  PRIMARY KEY (`Category`)"
    ") ENGINE=InnoDB")

# CIF: RO#########C || RO + 10 cifre
TABLES['companies'] = (
    "CREATE TABLE `companies` ("
    "  `CIF` varchar(12) NOT NULL,"
    "  `Category` varchar(30) NOT NULL,"
    "  `Name` varchar(100) NOT NULL,"
    "  `Description` varchar(150) NOT NULL,"
    "  `UserId` varchar(10) NOT NULL,"
    "  PRIMARY KEY (`CIF`),"
    "  CONSTRAINT `users_comp_ibfk_1` FOREIGN KEY (`UserId`)"
    "    REFERENCES `users` (`ID`) ON DELETE CASCADE,"
    "  CONSTRAINT `cont_comp_ibfk_1` FOREIGN KEY (`Category`)"
    "    REFERENCES `contributions` (`Category`) ON DELETE CASCADE"
    ") ENGINE=InnoDB")

# Incasari
TABLES['revenues'] = (
    "CREATE TABLE `revenues` ("
    "  `OrderNr` int NOT NULL,"
    "  `Sum` double(12, 2) NOT NULL,"
    "  `Date` date NOT NULL,"
    "  `Details` varchar(150) NOT NULL,"
    "  `CIF` varchar(12) NOT NULL,"
    "  PRIMARY KEY (`OrderNr`),"
    "  CONSTRAINT `comp_rev_ibfk_1` FOREIGN KEY (`CIF`)"
    "    REFERENCES `companies` (`CIF`) ON DELETE CASCADE"
    ") ENGINE=InnoDB")

# Cheltuieli
TABLES['costs'] = (
    "CREATE TABLE `costs` ("
    "  `ID` varchar(10) NOT NULL,"
    "  `Sum` double(12, 2) NOT NULL,"
    "  `Deductable` boolean NOT NULL,"
    "  `Date` date NOT NULL,"
    "  `Details` varchar(150) NOT NULL,"
    "  `CIF` varchar(12) NOT NULL,"
    "  PRIMARY KEY (`ID`),"
    "  CONSTRAINT `comp_costs_ibfk_1` FOREIGN KEY (`CIF`)"
    "    REFERENCES `companies` (`CIF`) ON DELETE CASCADE"
    ") ENGINE=InnoDB")

# Logs

def initDb():
    # Connect to mysql server
    cnx = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = cnx.cursor()

    # Use/Create DB_NAME
    print(DB_NAME)
    try:
        cursor.execute(f"USE {DB_NAME}")
        # Create TABLES
        for table_name in TABLES:
            print(table_name)
            # cursor.execute(f"DROP TABLE {table_name}")
            table_description = TABLES[table_name]
            try:
                cursor.execute(table_description)
            except mysql.connector.Error as err:
                print(err.msg)
        # Exit as the database is created once when tables are added also
        cursor.close()
        cnx.close()
        return
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_BAD_DB_ERROR:
            try:
                cursor.execute(f"CREATE DATABASE {DB_NAME} DEFAULT CHARACTER SET utf8")
            except mysql.connector.Error as err:
                exit(1)
        else:
            exit(1)

    # Create TABLES
    try:
        cursor.execute(f"USE {DB_NAME}")
    except mysql.connector.Error as err:
        print(err.msg)

    for table_name in TABLES:
        # cursor.execute(f"DROP TABLE {table_name}")
        table_description = TABLES[table_name]
        try:
            cursor.execute(table_description)
        except mysql.connector.Error as err:
            print(err.msg)

    # Close cursor and connection
    cursor.close()
    cnx.close()

