from uuid import uuid4

from app.client import SampleApisCoffeeClient
from app.exceptions import CoffeeApiError, CoffeeNotFoundError


def main() -> int:
    client = SampleApisCoffeeClient(
        base_url="http://127.0.0.1:8000/coffee/hot"
    )
    marker = uuid4().hex[:8]
    created_id = None
    try:
        # 1. GET коллекции
        drinks = client.list_drinks()
        print(f"[1] получено напитков: {len(drinks)}")

        # 2. POST с меткой группы в названии
        payload = {
            "title": f"Workshop coffee {marker}",
            "description": "created by workshop client",
            "ingredients": ["water", "coffee"],
            "image": "https://example.com/coffee.png",
        }
        created = client.create_drink(payload)
        # 3. сразу сохраняем id из ответа POST
        created_id = created["id"]
        print(f"[2] создан id={created_id} title={created['title']!r}")

        # 4. GET по id -- сравниваем с отправленным
        fetched = client.get_drink(created_id)
        for field in ("title", "description", "ingredients", "image"):
            if fetched.get(field) != payload[field]:
                print(
                    f"[4] предупреждение: {field} отличается: "
                    f"{fetched.get(field)!r} != {payload[field]!r}"
                )
        print(f"[4] GET после POST: title={fetched.get('title')!r}")

        # 5. PUT -- полная замена + повторный GET
        replacement = {
            "title": f"Replaced {marker}",
            "description": "replaced via PUT",
            "ingredients": ["milk", "sugar"],
            "image": "https://example.com/replaced.png",
        }
        client.replace_drink(created_id, replacement)
        after_put = client.get_drink(created_id)
        for field, value in replacement.items():
            if after_put.get(field) != value:
                print(
                    f"[5] предупреждение PUT: {field} = "
                    f"{after_put.get(field)!r}, ожидалось {value!r}"
                )
        print(f"[5] PUT применён: title={after_put.get('title')!r}")

        # 6. PATCH -- частичное изменение + повторный GET
        client.update_drink(created_id, {"description": f"patched {marker}"})
        after_patch = client.get_drink(created_id)
        if after_patch.get("description") != f"patched {marker}":
            print(
                "[6] предупреждение PATCH: description="
                f"{after_patch.get('description')!r}"
            )
        for field in ("title", "ingredients", "image"):
            if after_patch.get(field) != replacement[field]:
                print(f"[6] предупреждение: поле {field} не сохранилось после PATCH")
        print(f"[6] PATCH применён: description={after_patch.get('description')!r}")

        # 7. DELETE → GET → ожидаем 404
        client.delete_drink(created_id)
        try:
            client.get_drink(created_id)
        except CoffeeNotFoundError:
            print(f"[7] удаление подтверждено: GET id={created_id} → 404")
            created_id = None
        else:
            raise CoffeeApiError(
                f"GET id={created_id} после DELETE вернул успех — не 404"
            )

        return 0
    except (CoffeeApiError, ValueError) as error:
        print(f"Ошибка: {error}. Метка группы: {marker}")
        return 1
    finally:
        if created_id is not None:
            try:
                client.delete_drink(created_id)
                print(f"[cleanup] удалён id={created_id}")
            except CoffeeNotFoundError:
                pass
            except CoffeeApiError as error:
                print(f"Не удалось удалить id={created_id}: {error}")


if __name__ == "__main__":
    raise SystemExit(main())
