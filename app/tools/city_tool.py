import requests
from typing import Optional, Dict, Any
import json
from app.utils.error_handlers import handle_tool_errors, log_request_response, APIConnectionError
from app.core.logging_config import get_logger, log_request_start, log_request_end, log_error_with_context


class CityTool:
    """Tool for fetching city information from Wikipedia API"""

    def __init__(self):
        self.wikipedia_api_url = "https://en.wikipedia.org/api/rest_v1/page/summary"
        self.logger = get_logger('app.tools.city')

    @handle_tool_errors("Wikipedia")
    @log_request_response("CityTool")
    def get_city_info(self, city_name: str) -> str:
        """
        Fetch general information about a city from Wikipedia

        Args:
            city_name (str): Name of the city to search for

        Returns:
            str: Formatted city information or error message
        """
        request_id = log_request_start(self.logger, "GET", "Wikipedia API", {"city": city_name})

        try:
            self.logger.info(f"🏙️ Fetching city information for: {city_name}")

            if not city_name or not city_name.strip():
                self.logger.warning("❌ Empty city name provided")
                log_request_end(self.logger, request_id, 400)
                return "Please provide a valid city name."

            city_name = city_name.strip().title()
            self.logger.debug(f"🔍 Normalized city name: {city_name}")

            # Make request to Wikipedia API
            url = f"{self.wikipedia_api_url}/{city_name}"
            headers = {
                'User-Agent': 'MultiDomainChatbot/1.0 (https://example.com/contact)'
            }

            self.logger.debug(f"📡 Making request to: {url}")
            response = requests.get(url, headers=headers, timeout=10)
            self.logger.debug(f"📥 Wikipedia response: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"✅ Successfully fetched Wikipedia data for {city_name}")
                result = self._format_city_response(data, city_name)
                log_request_end(self.logger, request_id, 200, {"response_length": len(result)})
                return result

            elif response.status_code == 404:
                self.logger.warning(f"🔍 City '{city_name}' not found, trying variations")
                # Try with different variations
                variations = [
                    f"{city_name}_city",
                    f"{city_name},_United_States",
                    f"{city_name},_UK"
                ]

                for variation in variations:
                    try:
                        self.logger.debug(f"🔄 Trying variation: {variation}")
                        var_url = f"{self.wikipedia_api_url}/{variation}"
                        var_response = requests.get(var_url, headers=headers, timeout=10)
                        if var_response.status_code == 200:
                            data = var_response.json()
                            self.logger.info(f"✅ Found match with variation: {variation}")
                            result = self._format_city_response(data, city_name)
                            log_request_end(self.logger, request_id, 200, {"variation_used": variation})
                            return result
                    except Exception as e:
                        self.logger.debug(f"❌ Variation {variation} failed: {str(e)}")
                        continue

                self.logger.warning(f"❌ No variations found for city: {city_name}")
                log_request_end(self.logger, request_id, 404)
                return f"Sorry, I couldn't find information about '{city_name}' on Wikipedia. Please check the spelling or try a more specific name."

            else:
                self.logger.error(f"❌ Wikipedia API error: {response.status_code}")
                log_request_end(self.logger, request_id, response.status_code)
                return f"Sorry, I encountered an error while searching for '{city_name}'. Please try again later."

        except requests.exceptions.Timeout:
            log_error_with_context(self.logger, Exception("Request timeout"), "Wikipedia API call", {"city": city_name})
            log_request_end(self.logger, request_id, 408)
            return "The request timed out. Please try again."

        except requests.exceptions.ConnectionError:
            log_error_with_context(self.logger, Exception("Connection error"), "Wikipedia API call", {"city": city_name})
            log_request_end(self.logger, request_id, 503)
            return "Unable to connect to Wikipedia. Please check your internet connection."

        except requests.exceptions.RequestException as e:
            log_error_with_context(self.logger, e, "Wikipedia API request", {"city": city_name})
            log_request_end(self.logger, request_id, 500)
            return f"An error occurred while fetching city information: {str(e)}"

        except Exception as e:
            log_error_with_context(self.logger, e, "city_info_processing", {"city": city_name})
            log_request_end(self.logger, request_id, 500)
            return f"An unexpected error occurred: {str(e)}"

    def _format_city_response(self, data: Dict[Any, Any], city_name: str) -> str:
        """
        Format the Wikipedia API response into a readable format

        Args:
            data (Dict): Wikipedia API response data
            city_name (str): Original city name searched

        Returns:
            str: Formatted response
        """
        try:
            title = data.get('title', city_name)
            extract = data.get('extract', '')

            # Get coordinates if available
            coordinates = data.get('coordinates', {})
            lat = coordinates.get('lat')
            lon = coordinates.get('lon')

            response = f"🏙️ **{title}**\n\n"

            if extract:
                # Limit extract to reasonable length
                if len(extract) > 500:
                    extract = extract[:497] + "..."
                response += f"{extract}\n\n"

            if lat and lon:
                response += f"📍 **Location**: {lat:.4f}°, {lon:.4f}°\n"

            # Add Wikipedia URL if available
            if 'content_urls' in data and 'desktop' in data['content_urls']:
                wikipedia_url = data['content_urls']['desktop']['page']
                response += f"🔗 [Read more on Wikipedia]({wikipedia_url})"

            return response.strip()

        except Exception as e:
            return f"Found information about {city_name}, but couldn't format it properly: {str(e)}"


# Create global instance for use in OpenAI service
city_tool = CityTool()