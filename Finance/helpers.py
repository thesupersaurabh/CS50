import csv
import datetime
import pytz
import requests
import urllib.parse
import uuid
import time

from flask import redirect, render_template, session
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

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(symbol):
    """Look up quote for symbol."""

    # Prepare API request
    symbol = symbol.upper()
    end = datetime.datetime.now(pytz.timezone("US/Eastern"))
    start = end - datetime.timedelta(days=7)

    # Yahoo Finance API
    url = (
        f"https://query1.finance.yahoo.com/v7/finance/download/{urllib.parse.quote_plus(symbol)}"
        f"?period1={int(start.timestamp())}"
        f"&period2={int(end.timestamp())}"
        f"&interval=1d&events=history&includeAdjustedClose=true"
    )

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    }
    session = requests.Session()

    for attempt in range(5):  # Retry up to 5 times
        try:
            response = session.get(url, headers=headers)
            response.raise_for_status()

            # CSV header: Date,Open,High,Low,Close,Adj Close,Volume
            quotes = list(csv.DictReader(response.content.decode("utf-8").splitlines()))
            quotes.reverse()
            price = round(float(quotes[0]["Adj Close"]), 2)
            return {
                "name": symbol,
                "price": price,
                "symbol": symbol
            }
        except requests.RequestException as e:
            if response.status_code == 429:
                print(f"Rate limit exceeded. Retrying in {2 ** attempt} seconds...")
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                print(f"Error: {e}")
                return None
        except (ValueError, KeyError, IndexError) as e:
            print(f"Error processing data: {e}")
            return None

    print("Failed to retrieve data after several attempts.")
    return None


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"

