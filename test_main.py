import pytest
from main import app
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

# create test client with appllication context
client = TestClient(app)

def test_get_weather():
    # test the /weather endpoint
    with patch("requests.get") as mock_get:
        # mock the response of the requests.get call
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 1,
            "address": "Durban",
            "resolvedAddress": "Durban, South Africa",
            "currentConditions": {
                "temp": 25.0,
                "humility": 60,
                "windspeed": 10.0,
                "conditions": "Sunny",
                "datetime": "2025-10-01T12:00:00Z"

            }
        }
        mock_get.return_value = mock_response
        # call the endpoint
        response = client.get("/weather/Durban")
        # check the response
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["city"] == "Durban"
        assert response_data["country"] == "South Africa"


def test_get_weather_not_found():
    # test the /weather endpoint with a non-existant city
    with patch("requests.get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response

        response = client.get("/weather/invalidcity")
        assert response.status_code == 404
        assert response.json() == {"detail": "Error fetching weather data"}


