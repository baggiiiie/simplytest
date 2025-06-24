import json
import requests
import allure
from typing import Dict
import curlify


PROTOCOL = "http"
HOST = "localhost"
PORT = 8000
BASE_URL = f"{PROTOCOL}://{HOST}:{PORT}"


class HttpClient:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.headers = {}
        self.set_jwt()  # Automatically set JWT on initialization

    def set_header(self, content: Dict):
        for key, value in content.items():
            self.headers[key] = value

    def set_jwt(self):
        # mock setting jwt
        JWT = "abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {JWT}",
        }
        self.set_header(headers)

    def _attach_allure(self, method, url, request_body, request_headers, response):
        with allure.step(f"{method.upper()} {url}"):
            allure.attach(
                json.dumps(dict(request_headers), indent=2),
                name="HTTP Request Headers",
                attachment_type=allure.attachment_type.JSON,
            )
            allure.attach(
                json.dumps(request_body, indent=2),
                name="HTTP Request Body",
                attachment_type=allure.attachment_type.JSON,
            )
            allure.attach(
                json.dumps(dict(response.headers), indent=2),
                name="Response Headers",
                attachment_type=allure.attachment_type.JSON,
            )
            allure.attach(
                str(response.status_code),
                name="HTTP Status Code",
                attachment_type=allure.attachment_type.TEXT,
            )
            try:
                response_body = response.json()
                body_text = json.dumps(response_body, indent=2)
                attachment_type = allure.attachment_type.JSON
            except Exception:
                body_text = response.text
                attachment_type = allure.attachment_type.TEXT
            allure.attach(
                body_text, name="Response Body", attachment_type=attachment_type
            )
            allure.attach(
                body=curlify.to_curl(response.request),
                name="cURL Command",
                attachment_type=allure.attachment_type.TEXT,
            )

    def _request(self, method, endpoint, **kwargs):
        url = self.base_url + endpoint
        data = kwargs.get("json") or kwargs.get("data")
        headers = kwargs.get("headers", {})

        response: requests.Response = requests.request(method, url, **kwargs)
        self._attach_allure(method, url, data, headers, response)
        return response

    def get(self, endpoint, **kwargs):
        return self._request("get", endpoint, **kwargs)

    def post(self, endpoint, **kwargs):
        return self._request("post", endpoint, **kwargs)

    def put(self, endpoint, **kwargs):
        return self._request("put", endpoint, **kwargs)

    def delete(self, endpoint, **kwargs):
        return self._request("delete", endpoint, **kwargs)

    def patch(self, endpoint, **kwargs):
        return self._request("patch", endpoint, **kwargs)

    def echo(self, **kwargs):
        response = self.post("/api/echo", json=kwargs)
        return response.json()

    def health_check(self):
        response = self.get("/api/health")
        return response.json()


my_client = HttpClient()
