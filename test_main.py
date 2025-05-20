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


def test_get_weather_redis_cache():
    # test the /weather endpoint with redis cache
    with patch("redis.StrictRedis.get") as mock_get:
        mock_get.return_value = b'{"id": 1, "city": "Durban", "country": "South Africa", "temperature": 25.0, "humidity": 60, "wind_speed": 10.0, "description": "Sunny", "timestamp": "2025-10-01T12:00:00Z"}'
        response = client.get("/weather/Durban")
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["city"] == "Durban"
        assert response_data["country"] == "South Africa"


def test_get_weather_redis_cache_not_found():
    # test the /weather endpoint with redis cache not found
    with patch("redis.StrictRedis.get") as mock_get, patch("requests.get") as mock_get_request:
        mock_get.return_value = None
        mock_get_request.return_value.status_code = 404
        mock_get_request.return_value.json.return_value = {"detail": "Error fetching weather data"}
        response = client.get("/weather/invalidcity")
        assert response.status_code == 404
        assert response.json() == {"detail": "Error fetching weather data"}

def test_api_key_not_set():
    # test the /weather endpoint with API key not set
    with patch("os.getenv") as mock_get:
        mock_get.return_value = None
        response = client.get("/weather/Durban")
        assert response.status_code == 500
        assert response.json() == {"detail": "API key not set"}



            



