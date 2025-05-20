from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis
import json
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import time
from dotenv import load_dotenv, find_dotenv
import os
import requests
import logging

load_dotenv(find_dotenv())


BASE_URL = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/"
app = FastAPI(swagger_ui_parameters={"syntaxHighlight": False})

# Connect to Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)
REDIS_DB = os.getenv("REDIS_DB", 0)
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

redis_client = redis.StrictRedis(host=REDIS_HOST, port=str(REDIS_PORT), db=REDIS_DB, password=REDIS_PASSWORD)



# Define a Pydantic model for the weather data
class WeatherData(BaseModel):
    id: int
    city: str
    country: str
    temperature: float
    humidity: float
    wind_speed: float
    description: str
    timestamp: str

# Define a route to get weather data by city
@app.get("/weather/{city}")
async def get_weather(city: str):
    # city_query = city.replace("%20", " ").replace("%", " ")

    # check if API key is set
    API_KEY = os.getenv("API_KEY")
    if not API_KEY:
        raise HTTPException(status_code=500, detail="API key not set")

    # check redis cache
    cached = redis_client.get(f"weather:{city}")
    if cached:
        logging.info("Data found in redis")
        weather_data = json.loads(cached)
        return WeatherData(**weather_data)
    
    # if not found in cache, fetch from external API
    url = f"{BASE_URL}{city}?key={API_KEY}&unitGroup=metric&include=current"
    response = requests.get(url)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error fetching weather data")
    data = response.json()

    weather_data = {
        "id": int(time.time()),  # Generate a unique ID based on the current timestamp
        "city": data.get("address", "Unknown"),
        "country": data.get("resolvedAddress", "Unknown").split(",")[-1].strip(),
        "temperature": data.get("currentConditions", {}).get("temp", 0),
        "humidity": data.get("currentConditions", {}).get("humidity", 0),
        "wind_speed": data.get("currentConditions", {}).get("windspeed", 0),
        "description": data.get("currentConditions", {}).get("conditions"),
        "timestamp": data.get("currentConditions", {}).get("datetime")
    }

    # Store the data in redis with an expiration date of 1 hour
    redis_client.setex(f"weather:{city}", 3600, json.dumps(weather_data))

    # check if the data is stored in redis
    if redis_client.exists(f"weather:{city}"):
        logging.info("Data stored in redis")
    else:
        logging.info("Data not stored in redis")
    # return the weather data
    return WeatherData(**weather_data)


