import pytest
from unittest.mock import Mock, patch, MagicMock
from app.tools.city_tool import CityTool
from app.tools.weather_tool import WeatherTool
from app.tools.research_tool import ResearchTool
from app.tools.product_tool import ProductTool
from app.models.product import Product
from decimal import Decimal


class TestCityTool:
    """Test cases for CityTool"""

    def setup_method(self):
        self.city_tool = CityTool()

    @patch('app.tools.city_tool.requests.get')
    def test_get_city_info_success(self, mock_get):
        # Mock successful Wikipedia API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'title': 'Paris',
            'extract': 'Paris is the capital and most populous city of France.',
            'coordinates': {'lat': 48.8566, 'lon': 2.3522},
            'content_urls': {'desktop': {'page': 'https://en.wikipedia.org/wiki/Paris'}}
        }
        mock_get.return_value = mock_response

        result = self.city_tool.get_city_info("Paris")

        assert "Paris" in result
        assert "capital and most populous city of France" in result
        assert "48.8566" in result
        mock_get.assert_called_once()

    @patch('app.tools.city_tool.requests.get')
    def test_get_city_info_not_found(self, mock_get):
        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = self.city_tool.get_city_info("NonexistentCity")

        assert "couldn't find information" in result
        assert "NonexistentCity" in result

    def test_get_city_info_empty_input(self):
        result = self.city_tool.get_city_info("")
        assert "Please provide a valid city name" in result

    @patch('app.tools.city_tool.requests.get')
    def test_get_city_info_timeout(self, mock_get):
        mock_get.side_effect = Exception("timeout")
        result = self.city_tool.get_city_info("Paris")
        assert "error" in result.lower()


class TestWeatherTool:
    """Test cases for WeatherTool"""

    def setup_method(self):
        self.weather_tool = WeatherTool()

    @patch('app.tools.weather_tool.requests.get')
    def test_get_weather_success(self, mock_get):
        # Mock successful OpenWeatherMap API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'name': 'London',
            'sys': {'country': 'GB'},
            'main': {
                'temp': 15.5,
                'feels_like': 14.2,
                'humidity': 73,
                'pressure': 1013
            },
            'weather': [{'description': 'light rain', 'main': 'Rain'}],
            'wind': {'speed': 3.5}
        }
        mock_get.return_value = mock_response

        result = self.weather_tool.get_weather("London")

        assert "London" in result
        assert "15.5°C" in result
        assert "light rain" in result.lower()

    def test_get_weather_mock_response(self):
        # Test with mock API key
        result = self.weather_tool.get_weather("London")

        # Should return mock data when API key is not configured
        assert "Mock Data" in result
        assert "London" in result

    def test_get_weather_empty_input(self):
        result = self.weather_tool.get_weather("")
        assert "Please provide a valid city name" in result


class TestResearchTool:
    """Test cases for ResearchTool"""

    def setup_method(self):
        self.research_tool = ResearchTool()

    @patch('app.tools.research_tool.requests.get')
    def test_search_research_success(self, mock_get):
        # Mock successful Semantic Scholar API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [{
                'title': 'Machine Learning in Practice',
                'authors': [{'name': 'John Doe'}, {'name': 'Jane Smith'}],
                'year': 2023,
                'abstract': 'This paper explores machine learning applications.',
                'citationCount': 150,
                'url': 'https://example.com/paper1'
            }]
        }
        mock_get.return_value = mock_response

        result = self.research_tool.search_research("machine learning")

        assert "Machine Learning in Practice" in result
        assert "John Doe" in result
        assert "150" in result

    @patch('app.tools.research_tool.requests.get')
    def test_search_research_no_results(self, mock_get):
        # Mock empty response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': []}
        mock_get.return_value = mock_response

        result = self.research_tool.search_research("nonexistent topic")

        assert "No research papers found" in result

    def test_search_research_empty_input(self):
        result = self.research_tool.search_research("")
        assert "Please provide a valid research topic" in result


class TestProductTool:
    """Test cases for ProductTool"""

    def setup_method(self):
        self.product_tool = ProductTool()

    @patch('app.tools.product_tool.SessionLocal')
    def test_find_products_success(self, mock_session):
        # Mock database session and query
        mock_db = Mock()
        mock_session.return_value = mock_db

        # Mock product results
        mock_product = Mock()
        mock_product.name = "iPhone 15"
        mock_product.category = "Smartphones"
        mock_product.brand = "Apple"
        mock_product.price = Decimal("999.00")
        mock_product.in_stock = True
        mock_product.stock_quantity = 10
        mock_product.description = "Latest iPhone model"
        mock_product.id = 1

        mock_query = Mock()
        mock_query.filter.return_value.limit.return_value.all.return_value = [mock_product]
        mock_db.query.return_value = mock_query
        mock_db.__enter__ = Mock(return_value=mock_db)
        mock_db.__exit__ = Mock(return_value=None)

        result = self.product_tool.find_products("iPhone")

        assert "iPhone 15" in result
        assert "Apple" in result
        assert "$999.00" in result

    def test_find_products_empty_input(self):
        result = self.product_tool.find_products("")
        assert "Please provide a search term" in result

    @patch('app.tools.product_tool.SessionLocal')
    def test_find_products_no_results(self, mock_session):
        # Mock database session with no results
        mock_db = Mock()
        mock_session.return_value = mock_db

        mock_query = Mock()
        mock_query.filter.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value = mock_query
        mock_db.__enter__ = Mock(return_value=mock_db)
        mock_db.__exit__ = Mock(return_value=None)

        result = self.product_tool.find_products("nonexistent")

        assert "No products found" in result


# Integration test for all tools
class TestToolsIntegration:
    """Integration tests for all tools working together"""

    def test_all_tools_instantiate(self):
        """Test that all tools can be instantiated without errors"""
        city_tool = CityTool()
        weather_tool = WeatherTool()
        research_tool = ResearchTool()
        product_tool = ProductTool()

        assert city_tool is not None
        assert weather_tool is not None
        assert research_tool is not None
        assert product_tool is not None

    def test_all_tools_have_main_methods(self):
        """Test that all tools have their main methods"""
        city_tool = CityTool()
        weather_tool = WeatherTool()
        research_tool = ResearchTool()
        product_tool = ProductTool()

        assert hasattr(city_tool, 'get_city_info')
        assert hasattr(weather_tool, 'get_weather')
        assert hasattr(research_tool, 'search_research')
        assert hasattr(product_tool, 'find_products')

    def test_all_tools_handle_empty_input(self):
        """Test that all tools handle empty input gracefully"""
        city_tool = CityTool()
        weather_tool = WeatherTool()
        research_tool = ResearchTool()
        product_tool = ProductTool()

        city_result = city_tool.get_city_info("")
        weather_result = weather_tool.get_weather("")
        research_result = research_tool.search_research("")
        product_result = product_tool.find_products("")

        # All should return user-friendly error messages
        assert "valid" in city_result.lower() or "provide" in city_result.lower()
        assert "valid" in weather_result.lower() or "provide" in weather_result.lower()
        assert "valid" in research_result.lower() or "provide" in research_result.lower()
        assert "search term" in product_result.lower() or "provide" in product_result.lower()


if __name__ == "__main__":
    pytest.main([__file__])