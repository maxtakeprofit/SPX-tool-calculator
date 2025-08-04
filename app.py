from flask import Flask, render_template
import yfinance as yf

app = Flask(__name__)

def get_expected_move(symbol="^SPX", spread_width=20):
    # Fetch SPX data
    spx = yf.Ticker(symbol)
    price = spx.history(period="1d")["Close"].iloc[-1]

    # Get nearest expiration
    expirations = spx.options
    if not expirations:
        return None
    nearest_exp = expirations[0]

    # Get option chain for nearest expiration
    chain = spx.option_chain(nearest_exp)
    calls = chain.calls
    puts = chain.puts

    # Find ATM strike
    atm_strike = min(calls['strike'], key=lambda x: abs(x - price))
    atm_call = calls.loc[calls['strike'] == atm_strike]
    atm_put = puts.loc[puts['strike'] == atm_strike]

    # Expected move = ATM straddle premium
    expected_move = float(atm_call['lastPrice']) + float(atm_put['lastPrice'])

    # Target short call strike (price + 1.5 x EM)
    short_strike = round((price + 1.5 * expected_move) / 5) * 5
    long_strike = short_strike + spread_width

    # Premiums
    short_call_price = calls.loc[calls['strike'] == short_strike]['lastPrice']
    long_call_price = calls.loc[calls['strike'] == long_strike]['lastPrice']

    credit = 0
    if not short_call_price.empty and not long_call_price.empty:
        credit = float(short_call_price) - float(long_call_price)

    return {
        "price": round(price, 2),
        "expected_move": round(expected_move, 2),
        "sell_strike": short_strike,
        "buy_strike": long_strike,
        "credit": round(credit, 2)
    }

@app.route("/")
def index():
    data = get_expected_move()
    if not data:
        return render_template("index.html", error="No option data available")
    return render_template("index.html", data=data)

if __name__ == "__main__":
    app.run(debug=True)
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
