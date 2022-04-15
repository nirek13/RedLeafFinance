import os
#export API_KEY=pk_f0724718bba34e1aaef4b3c2b74a5236
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from helpers import apology, login_required, lookup, usd
app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


app.jinja_env.filters["usd"] = usd

app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///finance.db")

if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
     '''index shows portfolio'''

     result = db.execute("SELECT cash FROM users WHERE id =:id", id = session["user_id"])
     cash = result[0]['cash']

     portfolio = db.execute("SELECT stock, quantity FROM portfolio2 where id = :id", id = session["user_id"])

     if not portfolio:
        return apology("sorry you have no holdings",200)

     grand_total = cash

     for stock in portfolio:
         price = lookup(stock['stock'])['price']
         total = stock['quantity'] * price
         stock.update({'price': price, 'total': total})
         grand_total += total

     return render_template("index.html", stocks=portfolio, cash=cash, total=grand_total)

     for stock in portfolio:
         price = lookup(stock['stock'])['price']
         total = stock['quantity'] * price
         stock.update({'price': price, 'total': total})
         grand_total += total
     print(detailedlookup("aapl"))
     return render_template("index.html", stocks=portfolio, cash=cash, total=grand_total)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock."""
    if request.method == "POST":

        if (not request.form.get("symbol")) or (not request.form.get("shares")):
            return apology("must provide stock symbol and number of shares")

        if int(request.form.get("shares")) <= 0:
            return apology("must provide valid number of shares (integer)")

        quote = lookup(request.form.get("symbol"))

        if quote == None:
            return apology("Stock symbol not valid, please try again")

        cost = int(request.form.get("shares")) * quote['price']
        result = db.execute("SELECT cash FROM users WHERE id=:id", id = session["user_id"])

        if cost > result[0]["cash"]:
            return apology("you do not have enough cash for this transaction")

        now = datetime.now()
        db.execute("UPDATE users SET cash=cash-:cost WHERE id=:id", cost=cost, id=session["user_id"]);
        add_transaction = db.execute("INSERT INTO transactions (user_id, stock, quantity, price, date) VALUES (:user_id, :stock, :quantity, :price, :date)",
        user_id=session["user_id"], stock=quote["symbol"], quantity=int(request.form.get("shares")), price=quote['price'], date=now.strftime("%Y-%m-%d %H:%M:%S"))
        curr_portfolio = db.execute("SELECT quantity FROM portfolio2 WHERE stock=:stock and id = :id", stock=quote["symbol"], id = session['user_id'])

        if not curr_portfolio:
            db.execute("INSERT INTO portfolio2 (stock, quantity, id) VALUES (:stock, :quantity, :id)",stock=quote["symbol"], quantity = int(request.form.get("shares")), id = session["user_id"])
        else:
            db.execute("UPDATE portfolio2 SET quantity=quantity+:quantity, id = :id WHERE stock=:stock and id = :user_id", quantity=int(request.form.get("shares")), id = session["user_id"], stock=quote["symbol"], user_id = session["user_id"]);

        return redirect("/")
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    if request.method == "POST":

        port = db.execute("SELECT stock, quantity, price, date FROM transactions WHERE user_id=:id", id=session["user_id"])

        if not port:
            return apology("sorry you have no transactions on record")
    else:
        port = db.execute("SELECT stock, quantity, price, date FROM transactions WHERE user_id=:id", id=session["user_id"])
        return render_template("history.html", stocks = port)



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    session.clear()

    if request.method == "POST":

        if not request.form.get("username"):
            return apology("must provide username", 403)

        elif not request.form.get("password"):
            return apology("must provide password", 403)

        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        session["user_id"] = rows[0]["id"]
        hecd = rows[0]["id"]

        return redirect("/")

    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    session.clear()

    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    if request.method == "POST":

        if not request.form.get("symbol"):
            return apology("must provide stock symbol")

        quote = lookup(request.form.get("symbol"))

        if quote == None:
            return apology("Stock symbol not valid, please try again")

        else:
            return render_template("quoted.html", quote=quote)

    else:
        return render_template("quote.html")

@app.route("/dquote", methods=["GET", "POST"])
@login_required
def dquote():
    """Get stock quote."""

    if request.method == "POST":

        if not request.form.get("symbol"):
            return apology("must provide stock symbol")

        quote = detailedlookup( request.form.get("symbol") )

        if quote == None:
            return apology("Stock symbol not valid, please try again")

        else:
            return render_template("dquoted.html", quote = quote)

    else:
        return render_template("quote.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":

        if not request.form.get("username"):
            return apology("Must provide username.",400)

        elif not request.form.get("password") or not request.form.get("confirmation"):
            return apology("Must provide pasword.",400)

        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords don't match.",400)

        rt = db.execute("select username from users where username = :username",username = request.form.get("username"))

        if len(rt) > 0 :
            return apology("username has already been used",400)

        hashed_password = generate_password_hash(request.form.get("password"))
        usernames = request.form.get("username")
        result = db.execute("insert into users (username,hash) values(:username,:hash_)",username = request.form.get("username"),hash_ = hashed_password)

        userid = db.execute("select id from users where username = :username", username =request.form.get("username"))
        row = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        session["user_id"] = row[0]["id"]

        return redirect("/")

    else:
        return render_template("register.html")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":

        if (not request.form.get("stock")) or (not request.form.get("shares")):
            return apology("must provide stock symbol and number of shares")

        if int(request.form.get("shares")) <= 0:
            return apology("must provide valid number of shares (integer)")

        available = db.execute("SELECT quantity FROM portfolio WHERE :stock=stock", stock=request.form.get("stock"))

        if int(request.form.get("shares")) > available[0]['quantity']:
            return apology("You may not sell more shares than you currently hold")

        quote = lookup(request.form.get("stock"))

        if quote == None:
            return apology("Stock symbol not valid, please try again")

        cost = int(request.form.get("shares")) * quote['price']

        db.execute("UPDATE users SET cash=cash+:cost WHERE id=:id", cost=cost, id=session["user_id"]);

        add_transaction = db.execute("INSERT INTO transactions (user_id, stock, quantity, price, date) VALUES (:user_id, :stock, :quantity, :price, :date)",
            user_id=session["user_id"], stock=quote["symbol"], quantity=-int(request.form.get("shares")), price=quote['price'], date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        db.execute("UPDATE portfolio SET quantity=quantity-:quantity WHERE stock=:stock",
            quantity=int(request.form.get("shares")), stock=quote["symbol"]);

        return redirect("/")
    else:
        portfolio = db.execute("SELECT stock FROM portfolio")
        return render_template("sell.html", stocks=portfolio)



@app.route("/AddFunds", methods=["GET", "POST"])
@login_required
def addfunds():
    if request.method == "POST":
        amount = request.form.get("amount")
        db.execute("update users set cash = cash + :amount1 where id = :id", amount1 = amount, id = session["user_id"])
        return redirect("/")
    else:
        return render_template("funds.html")

@app.route("/advisor")
@login_required
def advisor():
    #cprice = []
    outlook = []
    #cprice[None] * 100
    currprice = []
    price = []
    profitmade = []
    i = 0
    if request.method == "POST":

        port = db.execute("SELECT stock, quantity, price, date FROM transactions WHERE user_id=:id and quantity > 0", id = session["user_id"])
        print(type(port))
        count = db.execute("SELECT count(stock) date FROM transactions WHERE user_id=:id", id = session["user_id"])
        if not port:
            return apology("sorry you currently hold no stocks")
        #currprice = []
        print(currprice)
        print(port[i]['price'])
        print(port[i]['price'])
        print(port[i]['price'])
        print(port[i]['price'])

        for stock in port:

            print(port[i]['price'])

            currprice.append(lookup(stock['stock'])['price'])

            price.append(port[i]['price'])

            profitmade.append( currprice[i] - price[i])

            if profitmade[i] > 0:
                outlook.append("rising")

            elif profitmade[i] == 0:
                outlook.append("no change")

            else:
                outlook[i].append("falling")
            i+=1
    else:

        port = db.execute("SELECT stock, quantity, price, date FROM transactions WHERE user_id=:id and quantity > 0", id = session["user_id"])

        cnum = db.execute("SELECT count(stock) date FROM transactions WHERE user_id=:id", id = session["user_id"])

        if not port:
            return apology("sorry you currently hold no stocks")

        for stock in port:
            print(port[i]['price'])
            currprice.append(lookup(stock['stock'])['price'])
            price.append(port[i]['price'])
            profitmade.append( currprice[i] - price[i])

            if profitmade[i] > 0:
                outlook.append("rising")
            elif profitmade[i] == 0:
                outlook.append("no change")
            else:
                outlook.append("falling")
            i+=1
        return render_template("advisor.html", stocks = port, price = currprice, profit = profitmade , outlook = outlook, lenght = len(price))

@app.route("/other", methods=["GET", "POST"])
@login_required
def other():
    return render_template("Other.html")

@app.route("/news", methods=["GET", "POST"])
@login_required
def news():
    return render_template("News.html")

def errorhandler(e):
    """Handle error"""

    if not isinstance(e, HTTPException):
        e = InternalServerError()

    return apology(e.name, e.code)


for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
