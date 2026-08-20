from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_list_active_subscription_plans() -> None:
    response = client.get("/api/v1/subscriptions/plans")

    assert response.status_code == 200

    plans = response.json()
    plans_by_code = {
        plan["code"]: plan
        for plan in plans
    }

    assert {"day-pass", "monthly"}.issubset(
        plans_by_code
    )

    day_pass = plans_by_code["day-pass"]
    assert day_pass["price_minor_units"] == 100
    assert day_pass["currency"] == "CNY"
    assert day_pass["duration_days"] == 1
    assert day_pass["data_limit_bytes"] == 10_737_418_240
    assert day_pass["max_devices"] == 1

    monthly = plans_by_code["monthly"]
    assert monthly["price_minor_units"] == 1200
    assert monthly["currency"] == "CNY"
    assert monthly["duration_days"] == 30
    assert monthly["data_limit_bytes"] == 223_338_299_392
    assert monthly["max_devices"] == 3

    prices = [
        plan["price_minor_units"]
        for plan in plans
    ]
    assert prices == sorted(prices)