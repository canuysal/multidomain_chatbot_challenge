import requests
from typing import Optional, Dict, Any
from app.core.config import get_settings
from app.utils.error_handlers import handle_tool_errors, log_request_response, APIConnectionError
from app.core.logging_config import get_logger, log_request_start, log_request_end, log_error_with_context


class WeatherTool:
    """Tool for fetching weather information from OpenWeatherMap API"""

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.openweathermap_api_key
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
        self.logger = get_logger('app.tools.weather')

    @handle_tool_errors("OpenWeatherMap")
    @log_request_response("WeatherTool")
    def get_weather(self, city_name: str) -> str:
        """
        Fetch current weather conditions for a specific city

        Args:
            city_name (str): Name of the city to get weather for

        Returns:
            str: Formatted weather information or error message
        """
        request_id = log_request_start(self.logger, "GET", "OpenWeatherMap API", {"city": city_name})

        try:
            self.logger.info(f"🌤️ Fetching weather information for: {city_name}")

            if not city_name or not city_name.strip():
                self.logger.warning("❌ Empty city name provided")
                log_request_end(self.logger, request_id, 400)
                return "Please provide a valid city name."

            city_name = city_name.strip()
            self.logger.debug(f"🔍 Normalized city name: {city_name}")

            # Check if API key is available
            if not self.api_key or self.api_key == "test-weather-key":
                self.logger.info("🔑 Using mock weather data (no API key configured)")
                result = self._mock_weather_response(city_name)
                log_request_end(self.logger, request_id, 200, {"mock_response": True})
                return result

            # Make request to OpenWeatherMap API
            params = {
                'q': city_name,
                'appid': self.api_key,
                'units': 'metric'  # Use Celsius
            }

            self.logger.debug(f"📡 Making request to: {self.base_url} with params: {list(params.keys())}")
            response = requests.get(self.base_url, params=params, timeout=10)
            self.logger.debug(f"📥 Weather API response: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"✅ Successfully fetched weather data for {city_name}")
                result = self._format_weather_response(data)
                log_request_end(self.logger, request_id, 200, {"response_length": len(result)})
                return result

            elif response.status_code == 401:
                self.logger.error("❌ Weather API authentication failed")
                log_request_end(self.logger, request_id, 401)
                return "Weather service authentication failed. Please check the API key configuration."

            elif response.status_code == 404:
                self.logger.warning(f"❌ City '{city_name}' not found in weather API")
                log_request_end(self.logger, request_id, 404)
                return f"Sorry, I couldn't find weather information for '{city_name}'. Please check the spelling or try a different city name."

            elif response.status_code == 429:
                self.logger.warning("⚠️ Weather API rate limit exceeded")
                log_request_end(self.logger, request_id, 429)
                return "Weather service is temporarily unavailable due to rate limiting. Please try again later."

            else:
                self.logger.error(f"❌ Weather API error: {response.status_code}")
                log_request_end(self.logger, request_id, response.status_code)
                return f"Sorry, I encountered an error while fetching weather for '{city_name}'. Please try again later."

        except requests.exceptions.Timeout:
            log_error_with_context(self.logger, Exception("Request timeout"), "Weather API call", {"city": city_name})
            log_request_end(self.logger, request_id, 408)
            return "The weather request timed out. Please try again."

        except requests.exceptions.ConnectionError:
            log_error_with_context(self.logger, Exception("Connection error"), "Weather API call", {"city": city_name})
            log_request_end(self.logger, request_id, 503)
            return "Unable to connect to the weather service. Please check your internet connection."

        except requests.exceptions.RequestException as e:
            log_error_with_context(self.logger, e, "Weather API request", {"city": city_name})
            log_request_end(self.logger, request_id, 500)
            return f"An error occurred while fetching weather information: {str(e)}"

        except Exception as e:
            log_error_with_context(self.logger, e, "weather_processing", {"city": city_name})
            log_request_end(self.logger, request_id, 500)
            return f"An unexpected error occurred: {str(e)}"

    def _format_weather_response(self, data: Dict[Any, Any]) -> str:
        """
        Format the OpenWeatherMap API response into a readable format

        Args:
            data (Dict): OpenWeatherMap API response data

        Returns:
            str: Formatted weather response
        """
        try:
            city = data.get('name', 'Unknown')
            country = data.get('sys', {}).get('country', '')

            main = data.get('main', {})
            weather = data.get('weather', [{}])[0]
            wind = data.get('wind', {})

            temperature = main.get('temp')
            feels_like = main.get('feels_like')
            humidity = main.get('humidity')
            pressure = main.get('pressure')

            description = weather.get('description', 'Unknown')
            main_weather = weather.get('main', 'Unknown')

            wind_speed = wind.get('speed', 0)

            response = f"🌤️ **Weather in {city}"
            if country:
                response += f", {country}"
            response += "**\n\n"

            if temperature is not None:
                response += f"🌡️ **Temperature**: {temperature:.1f}°C"
                if feels_like is not None:
                    response += f" (feels like {feels_like:.1f}°C)"
                response += "\n"

            response += f"☁️ **Condition**: {description.title()}\n"

            if humidity:
                response += f"💧 **Humidity**: {humidity}%\n"

            if pressure:
                response += f"📊 **Pressure**: {pressure} hPa\n"

            if wind_speed:
                response += f"💨 **Wind Speed**: {wind_speed} m/s\n"

            return response.strip()

        except Exception as e:
            return f"Found weather information but couldn't format it properly: {str(e)}"

    def _mock_weather_response(self, city_name: str) -> str:
        """
        Return mock weather data when API key is not available

        Args:
            city_name (str): City name

        Returns:
            str: Mock weather response
        """
        return f"""🌤️ **Weather in {city_name}** (Mock Data)

🌡️ **Temperature**: 22.5°C (feels like 24.0°C)
☁️ **Condition**: Partly Cloudy
💧 **Humidity**: 65%
📊 **Pressure**: 1013 hPa
💨 **Wind Speed**: 3.2 m/s

⚠️ This is mock data. To get real weather information, please configure the OpenWeatherMap API key."""


# Create global instance for use in OpenAI service
weather_tool = WeatherTool()