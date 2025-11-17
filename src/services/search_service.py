import base64
import time
from typing import Dict, Generator, List, Optional

import requests
from bs4 import BeautifulSoup

from ..config.settings import settings
from ..utils.logger import setup_logger
from .service import Service

logger = setup_logger(__name__)


class SearchService(Service):

    def __init__(self):
        super().__init__(logger)
        self.timeout = 30
        self.max_attempts = 20
        self.poll_interval = 5

    def search_docs(
        self,
        query: str,
        num_results: int = 5,
        fetch_full_content: bool = True
    ) -> Generator[Dict[str, str], None, None]:
        self.logger.info(f"Starting search for: {query}")

        search_results = self._search_yandex(query, num_results)

        if not search_results:
            self.logger.warning("No search results found")
            return

        for result in search_results:
            url = result['url']
            title = result['title']
            snippet = result['snippet']

            if fetch_full_content:
                self.logger.info(f"Fetching content from: {url}")
                content = self._fetch_page_content(url)

                if content:
                    yield {"content": content}
                else:
                    self.logger.warning(f"Could not fetch content from {url}, using snippet")
                    yield {"content": snippet}
            else:
                yield {"content": snippet}

    def _search_yandex(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """ Поиск через Yandex API """
        if not settings.yandex_folder_id or not settings.yandex_api_key:
            self.logger.warning("Yandex API credentials not found")
            return []

        try:
            search_url = "https://searchapi.api.cloud.yandex.net/v2/web/searchAsync"

            headers = {
                "Authorization": f"Api-Key {settings.yandex_api_key}",
                "Content-Type": "application/json"
            }

            body = {
                "query": {
                    "searchType": "SEARCH_TYPE_RU",
                    "queryText": query
                },
                "folderId": settings.yandex_folder_id,
                "responseFormat": "FORMAT_HTML",
                "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            self.logger.info(f"Starting async search for: {query}")
            response = requests.post(search_url, headers=headers, json=body, timeout=self.timeout)
            response.raise_for_status()

            operation_data = response.json()
            operation_id = operation_data.get('id')

            if not operation_id:
                self.logger.error("No operation ID received")
                return []

            self.logger.info(f"Operation ID: {operation_id}, waiting for results...")

            results = self._poll_search_operation(operation_id, headers, num_results)
            return results if results else []

        except Exception as e:
            self.logger.warning(f"Yandex Search API error: {e}")
            return []

    def _poll_search_operation(
        self,
        operation_id: str,
        headers: Dict[str, str],
        num_results: int
    ) -> List[Dict[str, str]]:
        operation_url = f"https://operation.api.cloud.yandex.net/operations/{operation_id}"
        attempt = 0

        while attempt < self.max_attempts:
            time.sleep(self.poll_interval)
            attempt += 1

            self.logger.debug(f"Checking operation status, attempt {attempt}/{self.max_attempts}")

            try:
                op_response = requests.get(operation_url, headers=headers, timeout=self.timeout)
                op_response.raise_for_status()
                op_data = op_response.json()

                if op_data.get('done'):
                    self.logger.info("Operation completed successfully")
                    return self._parse_search_results(op_data, num_results)

                if op_data.get('error'):
                    self.logger.error(f"Operation failed: {op_data['error']}")
                    return []

            except Exception as e:
                self.logger.error(f"Error polling operation: {e}")
                return []

        self.logger.warning(f"Operation timeout after {self.max_attempts} attempts")
        return []

    def _parse_search_results(self, op_data: Dict, num_results: int) -> List[Dict[str, str]]:
        if 'response' not in op_data or 'rawData' not in op_data['response']:
            self.logger.error("No response data in completed operation")
            return []

        raw_data = op_data['response']['rawData']
        html_result = base64.b64decode(raw_data).decode('utf-8')

        soup = BeautifulSoup(html_result, 'html.parser')
        results = []

        search_items = soup.find_all('li', class_='serp-item')

        if not search_items:
            search_items = soup.find_all(['li', 'div'], class_=['organic'])

        for idx, item in enumerate(search_items[:num_results], 1):
            try:
                link = item.find('a', class_=lambda x: x and ('organic__url' in x or 'OrganicTitle-Link' in x))
                if not link or not link.get('href'):
                    continue

                url = link.get('href', '')
                if not url.startswith('http'):
                    continue

                title_elem = item.find('span', class_=lambda x: x and ('organic__title' in x or 'OrganicTitleContentSpan' in x))
                if title_elem:
                    title = title_elem.get_text(strip=True)
                else:
                    title = link.get_text(strip=True) or 'No title'

                snippet_elem = item.find('span', class_=lambda x: x and 'OrganicTextContentSpan' in x)
                if snippet_elem:
                    snippet = snippet_elem.get_text(strip=True)
                else:
                    snippet_elem = item.find('div', class_=lambda x: x and 'organic__text' in x)
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''

                results.append({
                    'url': url,
                    'title': title,
                    'snippet': snippet,
                    'rank': idx
                })

            except Exception as e:
                self.logger.debug(f"Error parsing item: {e}")
                continue

        self.logger.info(f"Found {len(results)} results from Yandex Search API")
        return results

    def _fetch_page_content(self, url: str) -> Optional[str]:
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, timeout=self.timeout, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                element.decompose()

            text = soup.get_text(separator=' ', strip=True)

            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)

            return text

        except Exception as e:
            self.logger.error(f"Error fetching page content from {url}: {e}")
            return None

