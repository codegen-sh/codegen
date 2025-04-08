import datetime
import decimal
from enum import Enum
from unittest.mock import MagicMock, patch

import pytest
from pydantic import SecretStr

from codegen.agents.client.openapi_client.api_client import ApiClient
from codegen.agents.client.openapi_client.api_response import ApiResponse
from codegen.agents.client.openapi_client.configuration import Configuration
from codegen.agents.client.openapi_client.exceptions import ApiException, ApiValueError


class TestEnum(Enum):
    VALUE1 = "value1"
    VALUE2 = "value2"


class TestModel:
    def __init__(self, name: str, value: int):
        self.name = name
        self.value = value

    def to_dict(self):
        return {"name": self.name, "value": self.value}


class TestApiClient:
    @pytest.fixture
    def api_client(self):
        config = Configuration()
        # Mock the RESTClientObject to avoid making actual HTTP requests
        with patch("codegen.agents.client.openapi_client.rest.RESTClientObject") as mock_rest:
            client = ApiClient(configuration=config)
            # Return the client with mocked rest_client
            yield client

    def test_init_default_configuration(self):
        """Test initialization with default configuration"""
        with patch("codegen.agents.client.openapi_client.configuration.Configuration.get_default") as mock_get_default:
            mock_config = MagicMock()
            mock_get_default.return_value = mock_config
            with patch("codegen.agents.client.openapi_client.rest.RESTClientObject"):
                client = ApiClient()
                assert client.configuration == mock_config
                assert client.user_agent == "OpenAPI-Generator/1.0.0/python"

    def test_user_agent(self, api_client):
        """Test user agent getter and setter"""
        api_client.user_agent = "TestAgent/1.0"
        assert api_client.user_agent == "TestAgent/1.0"
        assert api_client.default_headers["User-Agent"] == "TestAgent/1.0"

    def test_set_default_header(self, api_client):
        """Test setting default header"""
        api_client.set_default_header("Custom-Header", "Custom-Value")
        assert api_client.default_headers["Custom-Header"] == "Custom-Value"

    def test_sanitize_for_serialization_none(self, api_client):
        """Test sanitization of None value"""
        assert api_client.sanitize_for_serialization(None) is None

    def test_sanitize_for_serialization_enum(self, api_client):
        """Test sanitization of Enum value"""
        assert api_client.sanitize_for_serialization(TestEnum.VALUE1) == "value1"

    def test_sanitize_for_serialization_secret_str(self, api_client):
        """Test sanitization of SecretStr value"""
        secret = SecretStr("secret_value")
        assert api_client.sanitize_for_serialization(secret) == "secret_value"

    def test_sanitize_for_serialization_primitive(self, api_client):
        """Test sanitization of primitive values"""
        assert api_client.sanitize_for_serialization("string") == "string"
        assert api_client.sanitize_for_serialization(123) == 123
        assert api_client.sanitize_for_serialization(True) == True
        assert api_client.sanitize_for_serialization(b"bytes") == b"bytes"

    def test_sanitize_for_serialization_list(self, api_client):
        """Test sanitization of list values"""
        data = [1, "string", None]
        assert api_client.sanitize_for_serialization(data) == [1, "string", None]

    def test_sanitize_for_serialization_tuple(self, api_client):
        """Test sanitization of tuple values"""
        data = (1, "string", None)
        assert api_client.sanitize_for_serialization(data) == (1, "string", None)

    def test_sanitize_for_serialization_datetime(self, api_client):
        """Test sanitization of datetime values"""
        dt = datetime.datetime(2022, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
        assert api_client.sanitize_for_serialization(dt) == "2022-01-01T12:00:00+00:00"

        date = datetime.date(2022, 1, 1)
        assert api_client.sanitize_for_serialization(date) == "2022-01-01"

    def test_sanitize_for_serialization_decimal(self, api_client):
        """Test sanitization of Decimal values"""
        dec = decimal.Decimal("123.45")
        assert api_client.sanitize_for_serialization(dec) == "123.45"

    def test_sanitize_for_serialization_dict(self, api_client):
        """Test sanitization of dict values"""
        data = {"key1": "value1", "key2": 123, "key3": None}
        assert api_client.sanitize_for_serialization(data) == data

    def test_sanitize_for_serialization_model(self, api_client):
        """Test sanitization of OpenAPI model"""
        model = TestModel("test", 123)
        assert api_client.sanitize_for_serialization(model) == {"name": "test", "value": 123}

    def test_deserialize_primitive(self, api_client):
        """Test deserialization of primitive values"""
        # Testing through __deserialize method
        assert api_client._ApiClient__deserialize_primitive("123", int) == 123
        assert api_client._ApiClient__deserialize_primitive("true", bool) == True
        assert api_client._ApiClient__deserialize_primitive("12.34", float) == 12.34

    def test_deserialize_date(self, api_client):
        """Test deserialization of date values"""
        date_str = "2022-01-01"
        result = api_client._ApiClient__deserialize_date(date_str)
        assert isinstance(result, datetime.date)
        assert result.year == 2022
        assert result.month == 1
        assert result.day == 1

    def test_deserialize_datetime(self, api_client):
        """Test deserialization of datetime values"""
        dt_str = "2022-01-01T12:00:00Z"
        result = api_client._ApiClient__deserialize_datetime(dt_str)
        assert isinstance(result, datetime.datetime)
        assert result.year == 2022
        assert result.month == 1
        assert result.day == 1
        assert result.hour == 12
        assert result.minute == 0
        assert result.second == 0

    def test_deserialize_enum(self, api_client):
        """Test deserialization of enum values"""
        assert api_client._ApiClient__deserialize_enum("value1", TestEnum) == TestEnum.VALUE1

        # Test exception case
        with pytest.raises(ApiException):
            api_client._ApiClient__deserialize_enum("invalid", TestEnum)

    def test_parameters_to_tuples(self, api_client):
        """Test parameters_to_tuples method"""
        # Test with dictionary
        params = {"param1": "value1", "param2": "value2"}
        result = api_client.parameters_to_tuples(params, None)
        assert result == [("param1", "value1"), ("param2", "value2")]

        # Test with list of tuples
        params = [("param1", "value1"), ("param2", "value2")]
        result = api_client.parameters_to_tuples(params, None)
        assert result == params

        # Test with collection format
        params = {"param1": ["value1", "value2", "value3"]}
        collection_formats = {"param1": "csv"}
        result = api_client.parameters_to_tuples(params, collection_formats)
        assert result == [("param1", "value1,value2,value3")]

        # Test with 'multi' collection format
        params = {"param1": ["value1", "value2", "value3"]}
        collection_formats = {"param1": "multi"}
        result = api_client.parameters_to_tuples(params, collection_formats)
        assert result == [("param1", "value1"), ("param1", "value2"), ("param1", "value3")]

    def test_parameters_to_url_query(self, api_client):
        """Test parameters_to_url_query method"""
        # Test basic parameters
        params = {"param1": "value1", "param2": "value2"}
        result = api_client.parameters_to_url_query(params, None)
        assert result == "param1=value1&param2=value2"

        # Test with boolean values
        params = {"param1": True, "param2": False}
        result = api_client.parameters_to_url_query(params, None)
        assert result == "param1=true&param2=false"

        # Test with numeric values
        params = {"param1": 123, "param2": 45.67}
        result = api_client.parameters_to_url_query(params, None)
        assert result == "param1=123&param2=45.67"

        # Test with dict values (should be JSON serialized)
        params = {"param1": {"key": "value"}}
        result = api_client.parameters_to_url_query(params, None)
        assert result == "param1=%7B%22key%22%3A%20%22value%22%7D"

        # Test with 'multi' collection format
        params = {"param1": ["value1", "value2", "value3"]}
        collection_formats = {"param1": "multi"}
        result = api_client.parameters_to_url_query(params, collection_formats)
        assert result == "param1=value1&param1=value2&param1=value3"

    def test_select_header_accept(self, api_client):
        """Test select_header_accept method"""
        # Test empty accepts
        assert api_client.select_header_accept([]) is None

        # Test with JSON in accepts
        accepts = ["application/xml", "application/json", "text/plain"]
        assert api_client.select_header_accept(accepts) == "application/json"

        # Test without JSON in accepts
        accepts = ["application/xml", "text/plain"]
        assert api_client.select_header_accept(accepts) == "application/xml"

    def test_select_header_content_type(self, api_client):
        """Test select_header_content_type method"""
        # Test empty content types
        assert api_client.select_header_content_type([]) is None

        # Test with JSON in content types
        content_types = ["application/xml", "application/json", "text/plain"]
        assert api_client.select_header_content_type(content_types) == "application/json"

        # Test without JSON in content types
        content_types = ["application/xml", "text/plain"]
        assert api_client.select_header_content_type(content_types) == "application/xml"

    def test_update_params_for_auth(self, api_client):
        """Test update_params_for_auth method"""
        # Setup mock configuration
        api_client.configuration = MagicMock()
        api_client.configuration.auth_settings.return_value = {
            "api_key": {"in": "header", "key": "X-API-KEY", "value": "test-api-key", "type": "apiKey"},
            "query_param": {"in": "query", "key": "api_key", "value": "test-query-key", "type": "apiKey"},
            "cookie_auth": {"in": "cookie", "key": "session", "value": "test-cookie", "type": "apiKey"},
        }

        # Test authentication in header
        headers = {}
        queries = []
        api_client.update_params_for_auth(headers, queries, ["api_key"], "", "", None)
        assert headers == {"X-API-KEY": "test-api-key"}

        # Test authentication in query
        headers = {}
        queries = []
        api_client.update_params_for_auth(headers, queries, ["query_param"], "", "", None)
        assert queries == [("api_key", "test-query-key")]

        # Test authentication in cookie
        headers = {}
        queries = []
        api_client.update_params_for_auth(headers, queries, ["cookie_auth"], "", "", None)
        assert headers == {"Cookie": "test-cookie"}

        # Test with request_auth override
        headers = {}
        queries = []
        request_auth = {"in": "header", "key": "X-CUSTOM-KEY", "value": "custom-value", "type": "apiKey"}
        api_client.update_params_for_auth(headers, queries, ["api_key"], "", "", None, request_auth)
        assert headers == {"X-CUSTOM-KEY": "custom-value"}

        # Test with invalid auth location
        invalid_auth = {"in": "invalid", "key": "x-key", "value": "value", "type": "apiKey"}
        with pytest.raises(ApiValueError):
            api_client._apply_auth_params({}, [], "", "", None, invalid_auth)

    def test_param_serialize(self, api_client):
        """Test param_serialize method"""
        with patch.object(api_client, "sanitize_for_serialization") as mock_sanitize, patch.object(api_client, "default_headers", {}):  # Empty the default headers
            # Set return values for sanitize_for_serialization
            mock_sanitize.side_effect = lambda x: x

            # Test with basic parameters
            method = "GET"
            resource_path = "/test/{id}"
            path_params = {"id": "123"}
            query_params = {"query": "value"}
            header_params = {"header": "value"}
            body = {"body": "content"}

            result = api_client.param_serialize(method, resource_path, path_params, query_params, header_params, body, None, None, None, None, None)

            # Verify result
            assert isinstance(result, tuple)
            assert result[0] == "GET"  # method
            assert "/test/123" in result[1]  # url
            assert "query=value" in result[1]  # query params in url
            assert "header" in result[2]  # header_params contains 'header' key
            assert result[2]["header"] == "value"  # header_params has correct value
            assert result[3] == {"body": "content"}  # body

    def test_call_api(self, api_client):
        """Test call_api method"""
        # Mock the rest_client.request method
        api_client.rest_client.request = MagicMock()
        mock_response = MagicMock()
        api_client.rest_client.request.return_value = mock_response

        # Call the method
        response = api_client.call_api("GET", "https://api.example.com/test", {"header": "value"}, {"body": "content"}, [("param", "value")], 30)

        # Verify the call to rest_client.request
        api_client.rest_client.request.assert_called_once_with(
            "GET", "https://api.example.com/test", headers={"header": "value"}, body={"body": "content"}, post_params=[("param", "value")], _request_timeout=30
        )

        # Verify the result
        assert response == mock_response

        # Test exception case
        api_client.rest_client.request.side_effect = ApiException(400)
        with pytest.raises(ApiException):
            api_client.call_api("GET", "https://api.example.com/test")

    def test_response_deserialize(self, api_client):
        """Test response_deserialize method"""
        # Mock RESTResponse
        response_data = MagicMock()
        response_data.status = 200
        response_data.data = b'{"name": "test", "value": 123}'
        response_data.getheader.return_value = "application/json"
        response_data.getheaders.return_value = {"Content-Type": "application/json"}

        # Create a mock response to return
        mock_api_response = MagicMock(spec=ApiResponse)

        # Mock deserialize method and ApiResponse constructor
        with (
            patch.object(api_client, "deserialize") as mock_deserialize,
            patch("codegen.agents.client.openapi_client.api_client.ApiResponse", return_value=mock_api_response) as mock_api_response_class,
        ):
            mock_deserialize.return_value = {"name": "test", "value": 123}

            # Test successful response deserialization
            response_types_map = {"200": "TestModel"}
            result = api_client.response_deserialize(response_data, response_types_map)

            # Verify ApiResponse was called with correct params
            mock_api_response_class.assert_called_once_with(status_code=200, data={"name": "test", "value": 123}, headers={"Content-Type": "application/json"}, raw_data=response_data.data)

            # Verify the result
            assert result == mock_api_response

    def test_response_deserialize_error(self, api_client):
        """Test response_deserialize method with error response"""
        # Mock RESTResponse for error
        response_data = MagicMock()
        response_data.status = 400
        response_data.data = b'{"error": "Bad Request"}'
        response_data.getheader.return_value = "application/json"
        response_data.getheaders.return_value = {"Content-Type": "application/json"}

        # Mock methods
        with patch.object(api_client, "deserialize") as mock_deserialize, patch("codegen.agents.client.openapi_client.exceptions.ApiException.from_response") as mock_exception:
            mock_deserialize.return_value = {"error": "Bad Request"}
            mock_exception.side_effect = ApiException(400)

            # Test error response
            response_types_map = {"400": "ErrorModel"}
            with pytest.raises(ApiException):
                api_client.response_deserialize(response_data, response_types_map)
