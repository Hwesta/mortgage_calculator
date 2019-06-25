README
------

Installation Requirements
=========================

* Python 3.6+
* Dependencies: ``pip install -r requirements.txt``
* Run server: ``env FLASK_APP=app.py flask run``
* Run tests: ``py.test``

Problem Statement
=================

::

    Create a mortgage calculator API using any language/tech stack.
    The API should accept and return JSON.

    GET /payment-amount
    Get the recurring payment amount of a mortgage
      Params:
        Asking Price
        Down Payment*
        Amortization Period**
        Payment schedule***
      Return:
        Payment amount per scheduled payment

    GET /mortgage-amount
    Get the maximum mortgage amount
      Params:
        payment amount
        Amortization Period**
        Payment schedule***
        Down Payment(optional)****
      Return:
        Maximum Mortgage that can be taken out

    PATCH /interest-rate
    Change the interest rate used by the application
      Params:
        Interest Rate
      Return:
        message indicating the old and new interest rate

    * Must be at least 5% of first $500k plus 10% of any amount above $500k (So $50k on a $750k mortgage)
    ** Min 5 years, max 25 years
    *** Weekly, biweekly, monthly
    **** If included its value should be added to the maximum mortgage returned

    Mortgage interest rate 2.5% per year

    Mortgage insurance is required on all mortgages with less than 20% down.
    Insurance must be calculated and added to the mortgage principal.
    Mortgage insurance is not available for mortgages > $1 million.

    Mortgage insurance rates are as follows:
    Down payment Insurance Cost
    5-9.99%     3.15%
    10-14.99%   2.4%
    15%-19.99%  1.8%
    20%+        N/A

    Payment formula: P = L[c(1 + c)^n]/[(1 + c)^n - 1]
    P = Payment
    L = Loan Principal
    c = Interest Rate

Notes
=====

I made a number of assumptions where the spec was unclear or didn't say.

* Assuming using a currency that has 2 decimal places
* Assuming housing costs don't bother including cents (so dealing with integers
  for asking price & down payment)
* Assuming amortization period is a whole number of years
* Assuming fixed rate mortgage
* Assuming a mortage over 1 million can't have down payment less than 20% since
  it can't get insurance for it
* Assuming don't have to deal with mortgage insurance on ``/mortgage-amount``
  endpoint
* ``n`` is missing from the provided formula explanation, assuming it refers to
  the number of payments made

Dealing with currency comes with many technical details around rounding errors
and fixed point math. Before releasing to production, I would want to work
closely with domain experts to get edge cases, test cases and a clearer spec.

Python's ``Decimal`` class handles fixed point math, which is useful for
currency where floating point errors are problematic. I left the rounding
algorithm as the default (``decimal.ROUND_HALF_EVEN``: Round to nearest with
ties going to nearest even integer).

The interest rate is stored in memory, defaulting to 2.5. It seemed like
overkill to set up a database to store one value. If this was in a production
environment, I would store it externally (possibly in an existing database or
key/value store) so it would persist across reboots.
