"""
Описание запроса создания горячего кофе
---------------------------------------
- HTTP-метод и URL:
POST http://127.0.0.1:8000/coffee/hot          (локальный мок)
POST https://api.sampleapis.com/coffee/hot     (публичный API)

- необходимые заголовки:
Content-Type: application/json   (requests ставит сам при json=...)
Accept: application/json         (необязателен)

- параметры JSON-тела (тип, обязательность, ограничения):
поле title -- тип string -- обязательное -- непустое
поле description -- тип string -- необязательное -- ограничений нет
поле ingredients -- тип array of string -- необязательное -- список строк
поле image -- тип string (URL) -- необязательное -- ограничений нет
поле id -- тип number -- необязательное -- задаёт сервер, клиент не передаёт

- какие поля задаёт клиент, а какие создаёт сервер:
клиент -- title (с меткой группы), description, ingredients, image
сервер — id (игнорирует клиентский, присваивает свой)

- ожидаемый успешный статус и форма ответа:
201 Created. Тело -- JSON-объект созданного напитка:
{"title": str, "description": str, "ingredients": [str], "image": str, "id": int}

- какие правила подтверждены запросами к API, а какие проверяем только в клиенте:
Подтверждено запросами к моку:
GET /coffee/hot → 200, application/json, массив объектов;
GET /coffee/hot/{id} для несуществующего id → 404;
POST → 201, возвращает созданный объект с новым id;
POST без title → 400, тело содержит ожидаемую схему
{"title":"string","description":"string","ingredients":"array",
"image":"string","id":"number"} — значит, title обязателен;
PUT заменяет все переданные поля;
PATCH меняет только переданные, остальные сохраняются;
DELETE → 200, тело {} (уточнить curl.exe -i).

Проверяется только в клиенте:
title непустой (API требует наличие, а непустоту проверяем сами);
ingredients — список строк.

"""

import requests
from app.exceptions import CoffeeApiError, CoffeeNotFoundError

JsonObject = dict[str, object]


class SampleApisCoffeeClient:
    def __init__(
        self,
        base_url: str = "https://api.sampleapis.com/coffee/hot",
        timeout: float = 10.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def list_drinks(self) -> list[JsonObject]:
        response = self._request("GET")
        data = response.json()
        if not isinstance(data, list):
            raise CoffeeApiError("ожидался JSON-массив в ответе на GET коллекции")
        return data

    def get_drink(self, drink_id: int) -> JsonObject:
        response = self._request("GET", str(drink_id))
        data = response.json()
        if not isinstance(data, dict):
            raise CoffeeApiError("ожидался JSON-объект в ответе на GET ресурса")
        return data

    def create_drink(self, payload: JsonObject) -> JsonObject:
        response = self._request("POST", payload=payload)
        data = response.json()
        if not isinstance(data, dict):
            raise CoffeeApiError("ожидался JSON-объект в ответе на POST")
        return data

    def replace_drink(
        self,
        drink_id: int,
        payload: JsonObject,
    ) -> JsonObject:
        response = self._request("PUT", str(drink_id), payload)
        data = response.json()
        if not isinstance(data, dict):
            raise CoffeeApiError("ожидался JSON-объект в ответе на PUT")
        return data

    def update_drink(
        self,
        drink_id: int,
        changes: JsonObject,
    ) -> JsonObject:
        response = self._request("PATCH", str(drink_id), changes)
        data = response.json()
        if not isinstance(data, dict):
            raise CoffeeApiError("ожидался JSON-объект в ответе на PATCH")
        return data

    def delete_drink(self, drink_id: int) -> None:
        self._request("DELETE", str(drink_id))

    def _request(
        self,
        method: str,
        path: str = "",
        payload: JsonObject | None = None,
    ) -> requests.Response:
        url = self._base_url + (f"/{path}" if path else "")

        try:
            response = requests.request(
                method,
                url,
                json=payload,
                timeout=self._timeout,
            )
        except requests.Timeout as error:
            raise CoffeeApiError(f"timeout при {method} {url}") from error
        except requests.RequestException as error:
            raise CoffeeApiError(
                f"сетевая ошибка при {method} {url}: {error}"
            ) from error

        if response.status_code == 404:
            raise CoffeeNotFoundError(f"{method} {url}: 404 Not Found")
        if not (200 <= response.status_code < 300):
            raise CoffeeApiError(f"{method} {url}: HTTP {response.status_code}")

        if not response.content:
            return response

        ctype = response.headers.get("Content-Type", "")
        if "application/json" not in ctype.lower():
            raise CoffeeApiError(
                f"{method} {url}: неожиданный Content-Type {ctype!r}"
            )

        try:
            response.json()
        except ValueError as error:
            raise CoffeeApiError(f"{method} {url}: некорректный JSON") from error

        return response
