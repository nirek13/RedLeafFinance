import os
import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(symbol):
    """Look up quote for symbol."""
    API_KEY= "pk_f0724718bba34e1aaef4b3c2b74a5236"
    # Contact API
    try:
        api_key = os.environ.get("API_KEY")
        url = f"https://cloud.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/quote?token={API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None
        # Parse response
    try:
        quote = response.json()
        return {
            "name": quote["companyName"],
            "price": float(quote["latestPrice"]),
            "symbol": quote["symbol"]
        }
    except (KeyError, TypeError, ValueError):
        return None

def detailedlookup(symbol):
    """Look up quote for symbol."""
    API_KEY= "pk_f0724718bba34e1aaef4b3c2b74a5236"
    # Contact API
    try:
        api_key = os.environ.get("API_KEY")
        url = f"https://cloud.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/quote?token={API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:

        quote = response.json()
        return {
            "Name": quote["companyName"],
            "Price": float(quote["latestPrice"]),
            "Symbol": quote["symbol"],
            "Year To Date Change" : float( quote["ytdChange"] ),
            "Year To Date High" : float(quote["week52High"]),
            "Change In Value" : float(quote["change"])
        }
    except (KeyError, TypeError, ValueError):
        return None




def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"
#app.jinja_env.globals.update(usd=usd)