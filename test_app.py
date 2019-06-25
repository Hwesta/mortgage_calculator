from app import app


def test_interest_rate():
    """It should update the current interest rate"""
    with app.test_client() as c:
        response = c.patch("/interest-rate", json={"interest_rate": 6.5})
        j = response.get_json()
        assert response.status_code == 200
        assert j == {"old_interest_rate": 2.5, "new_interest_rate": 6.5}
