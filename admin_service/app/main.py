#! /usr/bin/python3
# main.py - implements Conta App

import mysql.connector
from common.dbUtils import *
from common.apiserver import *


'''
Services:
    Register User
    Login
        Register Company
        Admin Company
            Add Income
            Add Costs
            Get Annual Income (input: year, CIF)
            Get Annual Profit
        Get Logs (if admin)
'''

'''
Utils
'''
from random import randint

def generateId(takenIds):
    id = None
    n = 1
    while n <= 10**8:
        id = str(randint(0, 10**8 - 1))
        if not id in takenIds:
            break
        n += 1
    # Check if limit reached
    if n > 10**8:
        return None
    return id

def getIds(idName, tableName):
    (cnx, cursor) = dbConnect()
    cursor.execute(f"SELECT DISTINCT {idName} FROM {tableName};")
    ids = [id[0] for id in cursor]
    dbClose(cnx, cursor)
    return ids

def getLogs():
    (cnx, cursor) = dbConnect()
    cursor.execute(f"SELECT * FROM logs;")
    entries = [entry for entry in cursor]
    dbClose(cnx, cursor)
    return "<br>".join(list(map(lambda s: str(s), entries)))

'''
User services
'''
AUTH_USER = ""
AUTH_USER_ID = ""

INSERT_USER = (
    "INSERT INTO users "
    "(ID, Username, Password, Email) "
    "VALUES (%s, %s, %s, %s)"
)
def addUser(username, password, email):
    # Check if username not already taken
    if username in getIds("Username", "users"):
        return "-1: Username already exists"

    # Generate User ID (distinct)
    userId = generateId(getIds("ID", "users"))
    if not userId:
        return "-1: Server error"

    # Connect to DB
    (cnx, cursor) = dbConnect()
    error = False

    # Insert the data
    # ID - unique, will return DB error message if duplicated
    try:
        cursor.execute(INSERT_USER, (userId, username, password, email))
        cnx.commit()
    except mysql.connector.Error as err:
        error = str(err)

    # Close DB connection
    dbClose(cnx, cursor)
    return error


def loginUser(username, password):
    global AUTH_USER_ID
    global AUTH_USER
    (cnx, cursor) = dbConnect()
    cursor.execute(f"SELECT ID, Username, Password FROM users WHERE Username = \'{username}\';")
    data = [d for d in cursor]
    dbClose(cnx, cursor)
    if not data:
        return "-1 : User not registered"
    data = data[0]
    if password != data[2]:
        return "-1 : Password not correct"
    
    AUTH_USER_ID = data[0]
    AUTH_USER = data[1]
    return "OK"

'''
Admin Company services
'''
INSERT_COMPANY = (
    "INSERT INTO companies "
    "(CIF, Category, Name, Description, UserId) "
    "VALUES (%s, %s, %s, %s, %s)"
)
def registerCompany(cif, category, name, description):
    global AUTH_USER_ID
    global AUTH_USER

    # Connect to DB
    (cnx, cursor) = dbConnect()
    error = False

    # Insert the data
    # ID - unique, will return DB error message if duplicated
    try:
        cursor.execute(INSERT_COMPANY, (cif, category, name, description, AUTH_USER_ID))
        cnx.commit()
    except mysql.connector.Error as err:
        error = str(err)

    # Close DB connection
    dbClose(cnx, cursor)
    return error

COMPANY_ADMIN = ""
def getUserCompanies():
    (cnx, cursor) = dbConnect()
    cursor.execute(f"SELECT CIF FROM companies WHERE UserId = \'{AUTH_USER_ID}\';")
    ids = [id[0] for id in cursor]
    dbClose(cnx, cursor)
    return ids

def adminComp(cif):
    global COMPANY_ADMIN
    if not cif in getUserCompanies():
        return "-1 : Not a valid company"
    COMPANY_ADMIN = cif
    return "OK"



'''
Income/Costs
'''
INSERT_INCOME = (
    "INSERT INTO revenues "
    "(OrderNr, Sum, Date, Details, CIF) "
    "VALUES (%s, %s, %s, %s, %s)"
)
def addIncome(orderNumber, ssum, date, details):
    global COMPANY_ADMIN

    if orderNumber in getIds("OrderNr", "revenues"):
        return "-1: OrderNr duplicated - already exists"

    # Connect to DB
    (cnx, cursor) = dbConnect()
    error = False

    # Insert the data
    try:
        cursor.execute(INSERT_INCOME, (orderNumber, ssum, date, details, COMPANY_ADMIN))
        cnx.commit()
    except mysql.connector.Error as err:
        error = str(err)

    # Close DB connection
    dbClose(cnx, cursor)
    if not error:
        return "OK"
    return error

INSERT_COST = (
    "INSERT INTO costs "
    "(ID, Sum, Deductable, Date, Details, CIF) "
    "VALUES (%s, %s, %s, %s, %s, %s)"
)
def _addCost(ssum, deductable, date, details):
    global COMPANY_ADMIN

    # Generate ID (distinct)
    id = generateId(getIds("ID", "costs"))
    if not id:
        return "-1: Server error"

    # Translate deductable
    if deductable == 'Y':
        d = str(1)
    else:
        d = str(0)

    # Connect to DB
    (cnx, cursor) = dbConnect()
    error = False
    # Insert the data
    try:
        cursor.execute(INSERT_COST, (id, ssum, d, date, details, COMPANY_ADMIN))
        cnx.commit()
    except mysql.connector.Error as err:
        error = str(err)

    # Close DB connection
    dbClose(cnx, cursor)
    if not error:
        return "OK"
    return error

'''
Stats
'''
INC_TEMPLATE = "Venit Burt: {0}<br>\
    CAS: {1}<br>\
    CASS: {2}<br>\
    Venit Impozabil: {3}<br>\
    Impozit: {4}<br>\
    Venit Net: {5}<br>\
"
PROF_TEMPLATE = "Venit Net: {0}<br>\
    Cheltuieli Deductibile: {1}<br>\
    Cheltuieli Nedeductibile: {2}<br>\
    Profit: {3}<br>\
"
def getAnInc(year):
    global COMPANY_ADMIN
    (cnx, cursor) = dbConnect()
    cursor.execute(f"call calcul_venit_brut(\'{COMPANY_ADMIN}\', {year}, @`my_vb`);")
    cursor.execute("select @my_vb;")
    brut = [id[0] for id in cursor]
    brut = str(brut[0])
    cursor.execute(f"call calcul_venit_net(\'{COMPANY_ADMIN}\', \'{year}\', @`my_net`);")
    cursor.execute("select @my_net;")
    net = [id[0] for id in cursor]
    net = str(net[0])
    cursor.execute(f"call calcul_venit_impozabil(\'{COMPANY_ADMIN}\', \'{year}\', @`my_impo`);")
    cursor.execute("select @my_impo;")
    impo = [id[0] for id in cursor]
    impo = str(impo[0])
    cursor.execute(f"select `get_cas`(\'{COMPANY_ADMIN}\', \'{year}\');")
    cas = [id[0] for id in cursor]
    cas = str(cas[0])
    cursor.execute(f"select `get_cass`(\'{COMPANY_ADMIN}\', \'{year}\');")
    cass = [id[0] for id in cursor]
    cass = str(cass[0])
    cursor.execute(f"select `get_impozit`(\'{COMPANY_ADMIN}\', \'{year}\');")
    imp = [id[0] for id in cursor]
    imp = str(imp[0])
    dbClose(cnx, cursor)
    return INC_TEMPLATE.format(brut, cas, cass, impo, imp, net)


def getAnProf(year):
    global COMPANY_ADMIN
    (cnx, cursor) = dbConnect()
    cursor.execute(f"call calcul_venit_net(\'{COMPANY_ADMIN}\', \'{year}\', @`my_net`);")
    cursor.execute("select @my_net;")
    net = [id[0] for id in cursor]
    net = str(net[0])
    cursor.execute(f"call calcul_cheltuieli(\'{COMPANY_ADMIN}\', \'{year}\', 1, @`my_ded`);")
    cursor.execute("select @my_ded;")
    ded = [id[0] for id in cursor]
    ded = str(ded[0])
    cursor.execute(f"call calcul_cheltuieli(\'{COMPANY_ADMIN}\', \'{year}\', 0, @`my_neded`);")
    cursor.execute("select @my_neded;")
    neded = [id[0] for id in cursor]
    neded = str(neded[0])
    cursor.execute(f"call calcul_profit(\'{COMPANY_ADMIN}\', \'{year}\', @`my_profit`);")
    cursor.execute("select @my_profit;")
    profit = [id[0] for id in cursor]
    profit = str(profit[0])
    dbClose(cnx, cursor)
    return PROF_TEMPLATE.format(net, ded, neded, profit)


class AdminServer(ApiServer): 
    @ApiRoute("/")
    def index(req):
        content = ''
        with open('templates/index.html', 'r') as f:
            content = f.read()
        return content
    
    @ApiRoute("/register")
    def register(req):
        content = ''
        with open('templates/register.html', 'r') as f:
            content = f.read()
        return content
    @ApiRoute("/login")
    def login(req):
        content = ''
        with open('templates/login.html', 'r') as f:
            content = f.read()
        return content    

    @ApiRoute("/registerSubmit")
    def registerSubmit(req):
        content = ''
        msg = addUser(
            req["username"][0],
            req["password"][0],
            req["email"][0])
        with open('templates/login.html', 'r') as f:
            content = f.read() + str(msg)
        return content
    @ApiRoute("/loginSubmit")
    def loginSubmit(req):
        content = ''
        msg = loginUser(
            req["username"][0],
            req["password"][0])
        if msg == "OK":
            if req["username"][0] == "admin":
                with open('templates/admin_services.html', 'r') as f:
                    content = f.read()
            else:
                with open('templates/admin.html', 'r') as f:
                    content = f.read()
        else:
            with open('templates/login.html', 'r') as f:
                content = f.read() + str(msg)
        return content 

    @ApiRoute("/adminCompany")
    def adminCompany(req):
        content = ''
        with open('templates/choose_company.html', 'r') as f:
            content = f.read()
        return content
    @ApiRoute("/registerCompany")
    def registerCompany(req):
        content = ''
        with open('templates/register_company.html', 'r') as f:
            content = f.read()
        return content 

    @ApiRoute("/adminCompanySubmit")
    def adminCompanySubmit(req):
        content = ''
        msg = adminComp(
            req["cif"][0])
        if msg == "OK":
            with open('templates/services.html', 'r') as f:
                content = f.read()
        else:
            with open('templates/choose_company.html', 'r') as f:
                content = f.read() + str(msg)
        return content
    @ApiRoute("/registerCompanySubmit")
    def registerCompanySubmit(req):
        content = ''
        msg = registerCompany(
            req["cif"][0],
            req["category"][0],
            req["name"][0],
            req["description"][0])
        with open('templates/admin.html', 'r') as f:
            content = f.read() + str(msg)
        return content 
    @ApiRoute("/getLogsSubmit")
    def getLogsSubmit(req):
        content = ''
        msg = getLogs()
        if not msg:
            with open('templates/admin_services.html', 'r') as f:
                content = f.read() + str(msg)
        else:
            with open('templates/show.html', 'r') as f:
                content = f.read()
                content = content.replace("#TEXT#", msg)
        return content

    @ApiRoute("/addIncome")
    def addIncome(req):
        content = ''
        with open('templates/add_income.html', 'r') as f:
            content = f.read()
        return content
    @ApiRoute("/addCost")
    def addCost(req):
        content = ''
        with open('templates/add_cost.html', 'r') as f:
            content = f.read()
        return content
    @ApiRoute("/getAnnualIncome")
    def getAnnualIncome(req):
        content = ''
        with open('templates/annual_income.html', 'r') as f:
            content = f.read()
        return content
    @ApiRoute("/getMonthlyIncome")
    def getMonthlyIncome(req):
        content = ''
        with open('templates/monthly_income.html', 'r') as f:
            content = f.read()
        return content
    @ApiRoute("/getAnnualProfit")
    def getAnnualProfit(req):
        content = ''
        with open('templates/annual_profit.html', 'r') as f:
            content = f.read()
        return content                                


    @ApiRoute("/addIncomeSubmit")
    def addIncomeSubmit(req):
        content = ''
        msg = addIncome(
            req["orderNumber"][0],
            req["sum"][0],
            req["date"][0],
            req["details"][0])
        if msg == "OK":
            with open('templates/services.html', 'r') as f:
                content = f.read()
        else:
            with open('templates/add_income.html', 'r') as f:
                content = f.read() + str(msg)
        return content
    @ApiRoute("/addCostSubmit")
    def addCostSubmit(req):
        content = ''
        msg = _addCost(
            req["sum"][0],
            req["deductable"][0],
            req["date"][0],
            req["details"][0])
        if msg == "OK":
            with open('templates/services.html', 'r') as f:
                content = f.read()
        else:
            with open('templates/add_cost.html', 'r') as f:
                content = f.read() + str(msg)
        return content
    @ApiRoute("/getAnnualIncomeSubmit")
    def getAnnualIncomeSubmit(req):
        content = ''
        msg = getAnInc(
            req["year"][0]
        )
        with open('templates/show.html', 'r') as f:
            content = f.read()
            content = content.replace("#TEXT#", msg)
        return content
    @ApiRoute("/getMonthlyIncomeSubmit")
    def getMonthlyIncomeSubmit(req):
        content = ''
        with open('templates/show.html', 'r') as f:
            content = f.read()
        return content
    @ApiRoute("/getAnnualProfitSubmit")
    def getAnnualProfitSubmit(req):
        content = ''
        msg = getAnProf(
            req["year"][0]
        )
        with open('templates/show.html', 'r') as f:
            content = f.read()
            content = content.replace("#TEXT#", msg)
        return content

'''
Main
'''
if __name__ == "__main__":
    host = str(os.getenv('ADMIN_SRV_ADDR'))
    port = int(os.getenv('ADMIN_SRV_PORT'))
    initDb()
    AdminServer(host, port).serve_forever()
