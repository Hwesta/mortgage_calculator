from decimal import Decimal

from flask import Flask, abort, jsonify, make_response, request
from flask_expects_json import expects_json

app = Flask(__name__)

# Constants

PAYMENTS_PER_YEAR = {"weekly": 52, "biweekly": 26, "monthly": 12}
INTEREST_RATE = 2.5
CENTS = Decimal("0.01")
PERCENT_5 = Decimal("0.05")
PERCENT_10 = Decimal("0.10")
PERCENT_15 = Decimal("0.15")
PERCENT_20 = Decimal("0.20")

# JSON schemas for endpoints

payment_schema = {
    "type": "object",
    "properties": {
        "asking_price": {"type": "integer"},
        "down_payment": {"type": "integer"},
        "payment_schedule": {
            "type": "string",
            "enum": ["weekly", "biweekly", "monthly"],
        },
        "amortization_period": {
            "type": "integer",  # Years
            "minimum": 5,
            "maximum": 25,
        },
    },
    "required": [
        "asking_price",
        "down_payment",
        "payment_schedule",
        "amortization_period",
    ],
}

interest_schema = {
    "type": "object",
    "properties": {"interest_rate": {"type": "number"}},
    "required": ["interest_rate"],
}

# Flask setup


@app.errorhandler(400)
def bad_request(error):
    """Return the error as JSON in an 'error' field"""
    return make_response(jsonify({"error": error.description}), 400)


# Endpoints


@app.route("/payment-amount")
@expects_json(payment_schema)
def payment_amount():
    """Get the recurring payment amount of a mortgage.

    JSON Params:
        Asking Price: Amount purchase is for, in whole dollars
        Down Payment: Amount put down up front, in whole dollars
        Amortization Period: Number of years the mortgage is for
        Payment schedule: One of weekly, biweekly or monthly

    Returns:
        200: JSON body with payment amount per scheduled payment
        400: Incoming data had an error. Details in 'error' field
    """
    j = request.get_json()
    asking_price = j["asking_price"]
    down_payment = j["down_payment"]
    payment_schedule = j["payment_schedule"]
    amortization_period = j["amortization_period"]

    if down_payment >= asking_price:
        abort(400, "No mortgage required")

    # Check down payment is enough of the asking price
    # Must be 5% of first 500K + 10% of remainder
    if asking_price > 500_000:
        min_down_payment = 500_000 * PERCENT_5 + (asking_price - 500_000) * PERCENT_10
    else:  # Less than or equal to 500,000
        min_down_payment = asking_price * PERCENT_5
    if down_payment < min_down_payment:
        abort(400, f"Down payment is below minimum of {min_down_payment:.0f}")

    # Check for mortgage insurance
    mortgage_insurance = Decimal(0)
    down_payment_percent = Decimal(down_payment / asking_price).quantize(PERCENT_5)
    if asking_price > 1_000_000 and down_payment_percent < PERCENT_20:
        # Reject large mortgages with small down payments
        abort(400, f"Mortgages over a 1,000,000 must have 20% down payment")
    elif asking_price <= 1_000_000 and down_payment_percent < PERCENT_20:
        # Add mortgage insurance for small mortgages
        # Down payment percent is > 5% and < 20% because of previous checks
        if PERCENT_5 <= down_payment_percent < PERCENT_10:
            mortgage_insurance = asking_price * Decimal("0.0315")  # 3.15%
        elif PERCENT_10 <= down_payment_percent < PERCENT_15:
            mortgage_insurance = asking_price * Decimal("0.024")  # 2.4%
        else:  # 10-15% down payment
            mortgage_insurance = asking_price * Decimal("0.018")  # 1.8%

    principal = asking_price - down_payment + mortgage_insurance

    monthly_payment = calculate_payment_amount(
        INTEREST_RATE, amortization_period, payment_schedule, principal
    )

    return jsonify(
        {
            "monthly_payment": str(monthly_payment),
            "interest_rate": INTEREST_RATE,
            "mortgage_insurance": str(mortgage_insurance.quantize(CENTS)),
        }
    )


@app.route("/interest-rate", methods=["PATCH"])
@expects_json(interest_schema)
def interest_rate():
    """
    Change the interest rate used by the application

    JSON Params:
        New interest rate
    Return:
        200: JSON with the old and new interest rates
        400: Incoming data had an error. Details in 'error' field
    """
    global INTEREST_RATE
    j = request.get_json()
    new_interest_rate = j["interest_rate"]
    old_interest_rate = INTEREST_RATE
    INTEREST_RATE = new_interest_rate
    return jsonify(
        {"old_interest_rate": old_interest_rate, "new_interest_rate": new_interest_rate}
    )


# Calculations


def calculate_payment_amount(
    interest_rate: float,
    amortization_period: int,
    payment_schedule: str,
    principal: int,
) -> Decimal:
    """Calculate recurring payment amount of a mortgage

    Args:
        interest_rate: Fixed interest rate for mortgage
        amortization_period: Length in years of the mortgage
        payment_schedule: How often payments are made (weekly, biweekly or monthly)
        principal: Total amount of the mortgage

    Returns:
        Recurring payment amount to 2 decimal places
    """
    payments_per_year = PAYMENTS_PER_YEAR[payment_schedule]
    r = Decimal((interest_rate / payments_per_year) / 100)  # Interest rate per payment
    N = amortization_period * payments_per_year  # Number of payments
    P = principal  # principal
    # assert r != 0

    # Because at least one variable is a Decimal, so is monthly_payment
    monthly_payment = (r * P * (1 + r) ** N) / ((1 + r) ** N - 1)
    return monthly_payment.quantize(CENTS)
