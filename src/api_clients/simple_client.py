import json
import requests
import allure

PROTOCOL = "http"
HOST = "localhost"
PORT = 8000
BASE_URL = f"{PROTOCOL}://{HOST}:{PORT}"


class HttpClient:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url.rstrip("/")

    def _attach_allure(self, method, url, request_body, request_headers, response):
        with allure.step(f"{method.upper()} {url}"):
            if request_body:
                allure.attach(
                    json.dumps(request_body, indent=2),
                    name="HTTP Request Body",
                    attachment_type=allure.attachment_type.JSON,
                )

            if request_headers:
                allure.attach(
                    json.dumps(dict(request_headers), indent=2),
                    name="HTTP Request Headers",
                    attachment_type=allure.attachment_type.JSON,
                )

            allure.attach(
                json.dumps(dict(response.headers), indent=2),
                name="Response Headers",
                attachment_type=allure.attachment_type.JSON,
            )

            try:
                response_body = response.json()
                body_text = json.dumps(response_body, indent=2)
                attachment_type = allure.attachment_type.JSON
            except Exception:
                body_text = response.text
                attachment_type = allure.attachment_type.TEXT

            allure.attach(
                response.status_code,
                name="HTTP Status Code",
                attachment_type=allure.attachment_type.TEXT,
            )
            allure.attach(
                body_text, name="Response Body", attachment_type=attachment_type
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
