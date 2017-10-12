from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import gettempdir
from helpers import *
# import sqlite3 Use this for SQL transactions
import pprint # to show full html requests
import sqlite3 # to control transactions/rollbacks
import datetime # for database timestamps
import matplotlib.pyplot as plt, mpld3, matplotlib
import pdfkit
from docusign_nodis import getLinkFromPDF


# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response
 
# custom filter
app.jinja_env.filters["usd"] = usd

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = gettempdir()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
# db = SQL("sqlite:///finance.db")
sql_connection = sqlite3.connect("finance.db")
sql_connection.isolation_level = None

@app.route("/")
@login_required
def index():

    portfolio_query = "SELECT 'Individual Trade', symbol, full_name, price_per_share, shares, total, trade_timestamp FROM \"ledger\" WHERE userid = "+ str(session["user_id"]) +" union all select 'Portfolio Total', symbol, full_name, round(avg(price_per_share),2) Average_Price, sum(shares) Total_Shares, round(sum(total),2) Total_Investment, trade_timestamp from \"ledger\" where userid = "+ str(session["user_id"]) +" group by symbol;"
    cash_query = "Select cash from \"users\" where id = "+ str(session["user_id"])
    print(cash_query)
    print(portfolio_query)
    try:  
        c = sql_connection.cursor() 
        c.execute(portfolio_query)
        portfolio = c.fetchall()

        c2 = sql_connection.cursor() 
        c2.execute(cash_query)
        cash = c2.fetchall()

        print(">>> Retrieved Portfolios for User " + str(session['user_id']))
        # print(portfolio)     
        # print(portfolio[0])
    except sql_connection.Error:
        print("failed!")
        flash('DB Error')
        return render_template('index.html')

    index_display = []
    total_value = 0.0
    for x in range(len(portfolio)):
        # print("BEFORE >> ", end="")
        # print(portfolio[x][1])
        # lookup(request.form.get("stock_symbol"))
        index_display.append(portfolio[x] + (lookup(portfolio[x][1]).get("price"), usd(round(lookup(portfolio[x][1]).get("price")*portfolio[x][4],2)) ,))
        total_value += round(lookup(portfolio[x][1]).get("price")*portfolio[x][4],2)
    # print(">>> {}".format(cash[0][0]))
    
    return render_template('index.html', portfolio_list=index_display, cash=usd(cash[0][0]), total_value=usd(total_value+cash[0][0]))


@app.route("/buy", methods=["GET", "POST"]) # --> combined the buy page into our quotes page
@login_required
def buy():
    """Buy shares of stock.""" 
    balance = db.execute("Select Cash from users where id=" +  str(session["user_id"]))
    # request_string = pprint.pformat(request.environ, depth=10)
    # print(request_string)
    if (float(request.form.get('trade_total')) < balance[0]['cash']):
        remaining_balance = (balance[0]['cash'] - float(request.form.get('trade_total')))
        ledger_insert = "Insert into ledger (transactionid, userid, symbol, full_name, price_per_share, shares, total, trade_timestamp) values (null, '"+ str(session['user_id'])+"', '"+request.form.get("symbol_input")+"', '"+request.form.get("full_name")+"', '"+request.form.get("price_input")+"', '"+request.form.get("num_shares")+"', '"+request.form.get("trade_total")+"', datetime('now'))"

        c = sql_connection.cursor()

        try:  # Test this with a failing case to check that rollback works
            c.execute("begin")
            c.execute("Update users set cash = " + str(remaining_balance) + " where id=" + str(session["user_id"]))
            c.execute(ledger_insert)
            c.execute("commit")
            flash("Bought "+ request.form.get('num_shares') +" shares of "+ request.form.get('symbol_input') +" for $"+ request.form.get('trade_total'))
            return render_template('trade.html', name='', price_str='', price='', symbol='')
        except sql_connection.Error:
            print("failed!")
            c.execute("rollback")
            flash('DB Error') 
            return render_template('trade.html', name='', price_str='', price='', symbol='')
    else:
        flash("Not enough cash to complete trade")
        return render_template('trade.html', name='', price_str='', price='', symbol='')
        
    return apology("Unknown Buy Error")

@app.route("/history")
@login_required
def history():
    """Show history of transactions."""
    portfolio_query = "SELECT 'Individual Trade', symbol, full_name, price_per_share, shares, total, trade_timestamp FROM \"ledger\" WHERE userid = "+ str(session["user_id"]) +" union all select 'Portfolio Total', symbol, full_name, avg(price_per_share) Average_Price, sum(shares) Total_Shares, sum(total) Total_Investment, trade_timestamp from \"ledger\" where userid = "+ str(session["user_id"]) +" group by symbol;"

    print(portfolio_query)
    try:  
        c = sql_connection.cursor()
        c.execute(portfolio_query)
        portfolio = c.fetchall()
        print(">>> Retrieved Portfolios for User " + str(session['user_id']))
    except sql_connection.Error:
        print("failed!")
        flash('DB Error')
        return render_template('history.html')

    # print(len(portfolio))

    # for x in range(len(portfolio)):
    #     print(portfolio[x])
    return render_template('history.html', portfolio_list=portfolio)    
    


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""
    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            return apology("invalid username and/or password")

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))

@app.route("/trade", methods=["GET", "POST"])
@login_required
def trade():
    """Get stock quote."""
    if request.method == "POST":
        if len(request.form.get("stock_symbol")) == 0:
            flash("Enter a symbol")
            return render_template("trade.html", name='', price_str='', price='', symbol='')
        stock_quote = lookup(request.form.get("stock_symbol"))
        if stock_quote == None:
            flash("Unable to retrieve stock quote")
            return render_template("trade.html", name='', price_str='', price='', symbol='')
        return render_template("trade.html", name=stock_quote.get("name"), price_str=usd(stock_quote.get("price")), price = stock_quote.get("price"), symbol=stock_quote.get("symbol"))
    elif request.method == "GET":
        return render_template("trade.html", name='', price_str='', price='', symbol='')

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user."""
    # Require username, render apology if input blank or already in DB #
    if request.method == "POST":
        if not request.form.get("username"):
            return apology("must provide username")
        elif request.form.get("password") != request.form.get("confirm_password"):
            return apology("passwords don't match")
        matched_users = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        if len(matched_users) != 0:
            return apology("username already exists")
        new_user_id = db.execute("Select max(id) max_id from users")
        try:
            db.execute("Insert into users (id, username, hash) values (:user_id, :username, :pass_hash)", username=request.form.get("username"), pass_hash=pwd_context.encrypt(request.form.get("password")), user_id=new_user_id[0].get('max_id')+1)
            flash('Hey {}, thanks for registering!'.format(request.form.get("username")))
            session["user_id"] = new_user_id[0].get('max_id')+1
            return render_template("index.html")
        except:
            flash("DB Error")
            return render_template("register.html")
    return render_template("register.html")

@app.route("/sell", methods=["POST"])
@login_required
def sell():
    """Sell shares of stock."""
    print("SELLLLLLLING")
    #print("ns: {} sym: {} fn: {} pps: {} total: {}".format(request.form.get('num_shares_form'), request.form.get('symbol_form'), request.form.get('full_name_form'), request.form.get('pps_form'), request.form.get('total_form')))
    
    print("-----------")
    print(request.form.get('symbol_form'))
    
    shares_query = "select sum(shares) Total_Shares, symbol from \"ledger\" where userid = "+ str(session["user_id"]) +" and symbol = '"+ request.form.get('symbol_form') +"';"
    print(shares_query)
    try:  
        c2 = sql_connection.cursor() 
        c2.execute(shares_query)
        shares = c2.fetchall()
    except sql_connection.Error:
        print("failed!")
        flash('Cash lookup Error')
        return render_template('index.html')
 
    if shares[0][0] == None or int(shares[0][0]) < int(request.form.get("num_shares_form")) or int(shares[0][0]) <= 0:
        flash("Insufficient Shares")
        return redirect(url_for("index"))
    else:
        # delete_ledger_query = "Delete from \"ledger\" where symbol = "+ request.form.get("symbol") +" and userid = "+ str(session["user_id"])
        update_ledger_query = "insert into \"ledger\" (userid, symbol, full_name, price_per_share, shares, total, trade_timestamp) values ("+ str(session["user_id"]) +", '"+ request.form.get("symbol_form") +"', '"+ request.form.get("full_name_form") +"', "+ request.form.get("pps_form") +", -"+ request.form.get("num_shares_form") +", -"+ request.form.get("total_form") +", datetime(\'now\'))"
        update_users_query = "Update \"users\" set cash = cash + "+ str(request.form.get("total_form")) +" where id = "+ str(session["user_id"])
        
        print(update_ledger_query)
        print("-------------------------------------")
        print(update_users_query)
        try:  
            c = sql_connection.cursor() 
            c.execute(update_ledger_query)
            c.execute(update_users_query)
        except sql_connection.Error:
            flash('Update Error')
            return redirect(url_for("index")) 

    # return render_template("index.html") 
    return redirect(url_for("index"))


@app.route("/nodis", methods=["GET", "POST"])
def nodis():
    
    lease_text = "This contract is an agreement between {Renter}, who will be renting a house from {Owner}, who owns the house being rented. This arrangement will begin on {date} and will end on {date}. The rent for this house will be {rent}. This amount must be paid on {date} every month. Late payments will incur a fee of {fee}. A deposit in the amount of {deposit} will be held for the duration of the lease and will be returned to the renter within one month after the keys are surrendered. The major rules regarding this house are as follows: {house rental rules, concerning pets, smoking, and other major violations}. By signing this agreement, the renter acknowledges that a complete list of these rules has been provided to him or her, and that the renter has read and understood these rules."
    
    if request.method == "POST":    
        print("Terms: {}".format(request.form.get('addterms')))
        print("Leasee 1: {}".format(request.form.get('leasee1')))
        print("Leasee 2: {}".format(request.form.get('leasee2'))) 
 
        replacements = {"LEASEE_ONE_VAR":request.form.get('leasee1'), "LEASEE_TWO_VAR":request.form.get('leasee2'), "ADDITIONAL_TERMS_VAR":request.form.get('addterms')}
        
        with open('./templates/contract.html') as infile, open('./Client_Contracts/out_client.html', 'w') as outfile: # Replace HTML template with added fields
            for line in infile:
                for src, target in replacements.items():
                    line = line.replace(src, target)
                outfile.write(line)        

        with open("./Client_Contracts/out_client.html", "r") as contract:       # PDF finalized contract
            pdfkit.from_string(contract.read(), './Client_Contracts/Final.pdf')
            print(contract.read())
            
        URLS = getLinkFromPDF()
        flash("1. {}".format(URLS[0]))            
        flash("2. {}".format(URLS[1]))            
        # flash("1. SOMETHING")
        # flash("2. SOMETHING ELSE")

    return render_template("nodis.html")
     
UPLOADS_DEFAULT_DEST = "./Client_Contracts"
UPLOADS_FOLDER = "./Client_Contracts"
app.config['UPLOAD_FOLDER'] = "./Client_Contracts" # not sure which way is better here #
ALLOWED_EXTENSIONS = set(['pdf']) # set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
from werkzeug.utils import secure_filename
import os
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

        
@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'upload_request' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['upload_request']
        # if user does not select file, browser also
        # submit a empty part without filename
        print(file)
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return render_template("upload.html")
        
# Nodis Notes

## Got the pdf maker to work by manually getting this binary for the X server
# wget https://github.com/wkhtmltopdf/obsolete-downloads/releases/download/linux/wkhtmltopdf-0.10.0_beta2-static-amd64.tar.bz2
# tar xvjf wkhtmltopdf-0.10.0_beta2-static-amd64.tar.bz2
# sudo mv bin/wkhtmltopdf-amd64 /usr/local/bin/wkhtmltopdf
# sudo chmod +x /usr/local/bin/wkhtmltopdf