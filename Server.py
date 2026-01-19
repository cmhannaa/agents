from fastmcp import FastMCP
import requests
mcp=FastMCP("Myserver")


@mcp.tool()
def get_weather(city):
    """
    Calls OpenWeatherMap API and returns temperature, humidity,
    wind speed and short weather description.
    """

    API_KEY = "fe7065c78217d6591c710d73fc7a34fc"  # <-- PUT YOUR REAL KEY HERE

    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": API_KEY,
            "units": "metric"   # return temperature in Celsius
        }

        response = requests.get(url, params=params)
        data = response.json()

        # If city not found or error
        if response.status_code != 200:
            return {
                "status": "error",
                "message": data.get("message", "Unknown error")
            }

        # Extract weather information
        temperature = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]
        condition = data["weather"][0]["description"]

        return {
            "status": "success",
            "weather": {
                "city": city,
                "temperature_c": temperature,
                "humidity": humidity,
                "wind_speed": wind_speed,
                "condition": condition
            }
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
def get_coordinates(city):
    """
    Calls the OpenStreetMap Nominatim API to get the latitude/longitude
    of the requested city. Returns a structured object used by MCP.
    """
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "format": "json",
            "q": city
        }

        # Nominatim *requires* a custom User-Agent header
        headers = {
            "User-Agent": "MCP-Server-Test/1.0"
        }

        # Make HTTP request
        response = requests.get(url, params=params, headers=headers)
        data = response.json()

        # If API returned no results
        if not data:
            return {
                "status": "error",
                "message": f"City '{city}' not found"
            }

        # Extract first result
        lat = float(data[0]["lat"])
        lon = float(data[0]["lon"])

        return {
            "status": "success",
            "coordinates": {"lat": lat, "lng": lon}
        }

    except Exception as e:
        # Any error becomes a tool error response
        return {"status": "error", "message": str(e)}


@mcp.tool()
def get_time(city):
    """
    Uses API Ninjas to get the local time of a city.
    """
    API_KEY = "DlabaewrP6ep7itDRuiJBsx3x2BZWR0kAzBvKQ1n"   # <-- required

    try:
        lookup = {
            "beirut": "beirut",
            "paris": "paris",
            "tokyo": "tokyo",
            "new york": "new york",
            "london": "london"
        }

        city_clean = city.lower().strip()
        query_city = lookup.get(city_clean)

        if not query_city:
            return {
                "status": "error",
                "message": f"No mapping for '{city}'. Add it to lookup."
            }

        url = f"https://api.api-ninjas.com/v1/worldtime?city={query_city}"

        headers = {
            "X-Api-Key": API_KEY
        }

        response = requests.get(url, headers=headers)
        data = response.json()

        if "error" in data:
            return {"status": "error", "message": data["error"]}

        return {
            "status": "success",
            "time": {
                "city": city,
                "timezone": data["timezone"],
                "datetime": data["datetime"],
                "day_of_week": data["day_of_week"],
                "hour": data["hour"],
                "minute": data["minute"],
                "second": data["second"]
            }
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
    

if __name__=='__main__':
    #mcp.run()     #by default the transport method is stdio its like writing mcp.run(transport="stdio")
    #mcp.run(transport="http", host="0.0.0.0", port=8000)  #here to run it on http or use the comamnd fastmcp run my_server.py:mcp --transport http --port 8000

    mcp.run(transport="sse")