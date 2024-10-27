import os

from dotenv import load_dotenv
from typing import Union, Dict
import requests


# Load all default env values
load_dotenv()

# configure the logger
from etl import logger

logger = logger.configure_logger("PAPERBOY", "/carmagnole/etl/logs/api_log.log")

#######################
### API BASE CLASS ###
#######################


class BaseNews:
    def __init__(self, base_url: str, _api_key_param: str):
        """
        Base class for handling news API requests.

        :param base_url: The base URL of the news API.
        :param _api_key_param: The name of the API key parameter in query requests.
        """
        self.base_url = base_url
        self._api_key_param = _api_key_param

    def __log_request(self, endpoint, query_params):
        """
        Log the API request.
        """
        log_message = f"API Request: {endpoint}, Params: {query_params}"
        logger.info(log_message)

    def __log_response(self, response):
        """
        Log the API response information.
        """
        log_message = f"API Response: Status Code: {response.status_code}, Content Length: {len(response.text)} bytes"
        logger.info(log_message)

    def __log_error(self, error_message):
        """
        Log API request errors.
        """
        log_message = f"API Error: {error_message}"
        logger.error(log_message)

    def __buildQueryParams(self, query_params: Dict[str, str], **kwargs):
        """
        Build query parameters by merging kwargs with provided query_params.

        :param query_params: The original query parameters.
        :return: Merged query parameters.
        """

        # This is more secure I guess. IDK. Only the backend has access anyway
        if isinstance(self, NewsAPI):
            query_params[self._api_key_param] = os.environ.get("NEWSAPI_API_KEY")
        elif isinstance(self, GuardianAPI):
            query_params[self._api_key_param] = os.environ.get("GUARDIAN_API_KEY")

        for key, value in kwargs.items():
            if key in query_params:
                query_params[key] = value
        return dict(filter(lambda item: item[1] != "", query_params.items()))

    def makeRequest(
        self, endpoint, query_params: Dict[str, str], **kwargs
    ) -> Union[str, Dict] or int:
        """
        Make an API request to the given endpoint with query parameters. JSON output.

        :param endpoint: The API endpoint to request.
        :param query_params: The query parameters for the request.
        :return: JSON response or error code.
        """
        query_params = self.__buildQueryParams(query_params, **kwargs)
        try:
            response = requests.get(f"{self.base_url}/{endpoint}", params=query_params)

            query_params[self._api_key_param] = "***"

            # Log the request and response
            self.__log_request(
                endpoint=f"{self.base_url}/{endpoint}", query_params=query_params
            )

            if response.status_code == 200:
                self.__log_response(response)
                return response.json()
            else:
                self.__log_error(
                    f"API request failed with status code: {response.status_code}"
                )
                self.__log_error(
                    f"API request failed with status code: {response._content}"
                )

        except Exception as e:
            error_type = type(e).__name__
            self.__log_error(f"{error_type}: Connection Error")
            raise ConnectionError


#######################
##### NEWSAPI API #####
#######################


class NewsAPI(BaseNews):
    def __init__(self):
        """
        Sub-class for NewsAPI with modifications in query parameters.

        :param API_KEY: The API key for accessing the NewsAPI.
        """
        super().__init__("https://newsapi.org/v2", "apiKey")

    def getTopHeadlines(self, **kwargs: Dict[str, str]) -> Union[Dict, str]:
        """

        query_params = {
            'country': '',
            'category': 'general',
            'sources': "",
            'q': '',
            'pageSize': '100',
            'page': '',
            'language': 'en'
        }
        Returns:
            JSON object having all the news data
        """
        query_params = {
            "country": "",
            "category": "general",
            "sources": "",
            "q": "",
            "pageSize": "100",
            "page": "",
            "language": "en",
        }
        return self.makeRequest("top-headlines", query_params, **kwargs)

    def getEverything(self, **kwargs: Dict[str, str]) -> Union[Dict, str]:
        """_summary_

        query_params = {
            'q': '',
            'sources': 'bbc-news',
            'domains': '',
            'from': '',
            'to': '',
            'language': 'en',
            'sort_by': '',
            'pageSize': '100',
            'page': '',
        }
        Returns:
            JSON object having all the news data
        """
        query_params = {
            "q": "",
            "sources": "bbc-news",
            "domains": "",
            "from": "",
            "to": "",
            "language": "en",
            "sort_by": "",
            "pageSize": "100",
            "page": "",
        }

        if "from_date" in kwargs:
            query_params["from"] = kwargs["from_date"]
            del kwargs["from_date"]

        return self.makeRequest("everything", query_params, **kwargs)


#######################
#### GUARDIAN API #####
#######################


class GuardianAPI(BaseNews):
    def __init__(self):
        """
        Sub-class for GuardianAPI with modifications in query parameters.

        :param API_KEY: The API key for accessing the GuardianAPI.
        """
        super().__init__("https://content.guardianapis.com", "api-key")

    def searchContent(self, **kwargs: Dict[str, str]) -> Union[Dict, str]:
        """
        query_params = {
            'q': '',
            'format': 'json',
            'from-date': '',
            'language': 'en',
            'page-size': '200',
            'page': '',
            'type': 'article',
            'show-fields':'all'
        }

        Returns:
            JSON object having all the news data
        """
        query_params = {
            "q": "",
            "format": "json",
            "from-date": "",
            "language": "en",
            "page-size": "200",
            "page": "",
            "type": "article",
            "show-fields": "all",
        }

        if "from_date" in kwargs:
            query_params["from-date"] = kwargs["from_date"]
            del kwargs["from_date"]

        return self.makeRequest("search", query_params, **kwargs)


def newsApiFetch() -> NewsAPI:
    news_api = NewsAPI()
    return news_api


def guardianApiFetch() -> GuardianAPI:
    guardian_api = GuardianAPI()
    return guardian_api
