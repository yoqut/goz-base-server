from typing import Optional, Dict, Any
import requests
import json

from configuration import env


class BaseService:
    """User service for API communication"""

    def __init__(self):
        self.driver_url =  env.DRIVER_BOT_URL
        self.passenger_url = env.PASSENGER_BOT_URL
        self.session: Optional[requests.Session] = None

    def __enter__(self):
        self.create_session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_session()

    def create_session(self):
        """Create requests session"""
        if self.session is None:
            headers = {'Content-Type': 'application/json'}
            self.session = requests.Session()
            self.session.headers.update(headers)

    def close_session(self):
        """Close requests session"""
        if self.session:
            self.session.close()
            self.session = None

    def _request(self, method: str, endpoint: str, driver = True, **kwargs) -> Dict[str, Any]:
        """Make sync HTTP request"""
        self.create_session()

        base_url = self.driver_url if driver else self.passenger_url

        url = f"{base_url}{endpoint}"
        print(url)
        try:
            response = self.session.request(method, url, **kwargs)

            # Check content type before trying to parse JSON
            content_type = response.headers.get('Content-Type', '').lower()

            if response.status_code == 204:  # No content
                return {}

            # Agar HTML qaytsa, JSON deb pars qilmaslik
            if 'text/html' in content_type:
                text_response = response.text

                if response.status_code == 404:
                    return {'detail': 'Not found'}
                else:
                    return {'error': f'Unexpected HTML response: {response.status_code}'}

            # JSON responseni pars qilish
            try:
                data = response.json()
            except json.JSONDecodeError:
                # Agar JSON pars qilib bo'lmasa
                text_response = response.text
                return {'error': f'Non-JSON response: {text_response[:100]}'}

            if not 200 <= response.status_code < 300:
                error_msg = data.get('detail') or data.get('error') or f'HTTP {response.status_code}'
                raise Exception(f"API Error: {error_msg}")

            return data

        except requests.RequestException as e:
            raise Exception(f"Network error: {str(e)}")
        except Exception as e:
            raise Exception(f"Request error: {str(e)}")