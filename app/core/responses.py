from typing import Any


def success_response(
    message: str,
    data: Any = None,
) -> dict[str, Any]:
    response: dict[str, Any] = {
        "success": True,
        "message": message,
    }
    if data is not None:
        response["data"] = data
    return response


def error_response(
    message: str,
    *,
    details: Any = None,
    error_code: str | None = None,
) -> dict[str, Any]:
    response: dict[str, Any] = {
        "success": False,
        "message": message,
    }
    if error_code:
        response["error_code"] = error_code
    if details is not None:
        response["details"] = details
    return response
