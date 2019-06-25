from decimal import Decimal

import pytest

from app import app, calculate_max_mortgage, calculate_payment_amount


@pytest.mark.parametrize(
    "asking_price, down_payment, amortization_period, payment_schedule, result",
    [
        (
            # Happy path
            200000,
            100000,
            5,
            "monthly",
            {
                "interest_rate": 2.5,
                "monthly_payment": "1774.74",
                "mortgage_insurance": "0.00",
            },
        ),
        (
            # Mortgage insurance 3.15%
            100000,
            5000,
            5,
            "monthly",
            {
                "interest_rate": 2.5,
                "monthly_payment": "1741.90",
                "mortgage_insurance": "3150.00",
            },
        ),
        (
            # Mortgage insurance 2.4%
            100000,
            10000,
            5,
            "monthly",
            {
                "interest_rate": 2.5,
                "monthly_payment": "1639.86",
                "mortgage_insurance": "2400.00",
            },
        ),
        (
            # Mortgage insurance 1.8%
            100000,
            15005,
            5,
            "monthly",
            {
                "interest_rate": 2.5,
                "monthly_payment": "1540.38",
                "mortgage_insurance": "1800.00",
            },
        ),
    ],
)
def test_payment_amount_endpoint(
    asking_price, down_payment, amortization_period, payment_schedule, result
):
    """It should calculate a recurring payment amount"""
    with app.test_client() as c:
        response = c.get(
            "/payment-amount",
            json={
                "asking_price": asking_price,
                "down_payment": down_payment,
                "payment_schedule": payment_schedule,
                "amortization_period": amortization_period,
            },
        )
        assert response.status_code == 200
        j = response.get_json()
        assert j == result


@pytest.mark.parametrize(
    "asking_price, down_payment, amortization_period, payment_schedule, error",
    [
        (200000, 100000, 30, "monthly", "30 is greater than the maximum of 25"),
        (200000, 300000, 20, "monthly", "No mortgage required"),
        (750000, 5000, 20, "monthly", "Down payment is below minimum of 50000"),
    ],
)
def test_payment_amount_endpoint_errors(
    asking_price, down_payment, amortization_period, payment_schedule, error
):
    """It should verify payment endpoint inputs and return an error"""
    with app.test_client() as c:
        response = c.get(
            "/payment-amount",
            json={
                "asking_price": asking_price,
                "down_payment": down_payment,
                "payment_schedule": payment_schedule,
                "amortization_period": amortization_period,
            },
        )
        assert response.status_code == 400
        j = response.get_json()
        assert j["error"] == error


@pytest.mark.parametrize(
    "payment_amount, down_payment, amortization_period, payment_schedule, result",
    [
        # With down payment
        ("1774.74", 100000, 5, "monthly", {"interest_rate": 2.5, "mortgage": "200000"}),
        # Without down payment
        ("1774.74", None, 5, "monthly", {"interest_rate": 2.5, "mortgage": "100000"}),
    ],
)
def test_mortgage_amount_endpoint(
    payment_amount, down_payment, amortization_period, payment_schedule, result
):
    """It should calculate a recurring payment amount"""
    j = {
        "payment_amount": payment_amount,
        "payment_schedule": payment_schedule,
        "amortization_period": amortization_period,
    }
    if down_payment:
        j["down_payment"] = down_payment
    with app.test_client() as c:
        response = c.get("/mortgage-amount", json=j)
        assert response.status_code == 200
        j = response.get_json()
        assert j == result


@pytest.mark.parametrize(
    "payment_amount, down_payment, amortization_period, payment_schedule, error",
    [
        ("1234", 100000, 30, "monthly", "30 is greater than the maximum of 25"),
        (
            "aoeu",
            300000,
            20,
            "monthly",
            "Payment amount must be a string containing numbers",
        ),
    ],
)
def test_mortgage_amount_endpoint_errors(
    payment_amount, down_payment, amortization_period, payment_schedule, error
):
    """It should verify payment endpoint inputs and return an error"""
    with app.test_client() as c:
        response = c.get(
            "/mortgage-amount",
            json={
                "payment_amount": payment_amount,
                "down_payment": down_payment,
                "payment_schedule": payment_schedule,
                "amortization_period": amortization_period,
            },
        )
        assert response.status_code == 400
        j = response.get_json()
        assert j["error"] == error


def test_interest_rate():
    """It should update the current interest rate"""
    with app.test_client() as c:
        response = c.patch("/interest-rate", json={"interest_rate": 6.5})
        j = response.get_json()
        assert response.status_code == 200
        assert j == {"old_interest_rate": 2.5, "new_interest_rate": 6.5}


@pytest.mark.parametrize(
    "interest_rate, amortization_period, payment_schedule, principal, result",
    [
        (6.5, 30, "monthly", 200000, Decimal("1264.14")),
        (2.5, 30, "monthly", 200000, Decimal("790.24")),
        (2.5, 30, "biweekly", 200000, Decimal("364.59")),
        (2.5, 30, "weekly", 200000, Decimal("182.27")),
    ],
)
def test_payment_calculation(
    interest_rate, amortization_period, payment_schedule, principal, result
):
    """It should calculate the recurring payment amount correctly"""
    assert (
        calculate_payment_amount(
            interest_rate, amortization_period, payment_schedule, principal
        )
        == result
    )


@pytest.mark.parametrize(
    "payment_amount, interest_rate, amortization_period, payment_schedule, result",
    [
        (Decimal("1264.14"), 6.5, 30, "monthly", 200001),
        (Decimal("790.24"), 2.5, 30, "monthly", 200000),
        (Decimal("364.59"), 2.5, 30, "biweekly", 200000),
        (Decimal("182.27"), 2.5, 30, "weekly", 200005),
    ],
)
def test_max_mortgage_calculation(
    payment_amount, interest_rate, amortization_period, payment_schedule, result
):
    """It should calculate the recurring payment amount correctly"""
    print("result", repr(result))
    assert (
        calculate_max_mortgage(
            payment_amount, interest_rate, amortization_period, payment_schedule
        )
        == result
    )
