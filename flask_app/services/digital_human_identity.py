"""数字人匿名浏览器身份的统一解析与Cookie兼容。"""

from flask import g, request


COOKIE_NAME = "yys_law_dh_identity"
COOKIE_MAX_AGE = 60 * 60 * 24 * 365


def _valid_client_id(value) -> bool:
    return (
        isinstance(value, str)
        and value.startswith("dhc_")
        and 4 < len(value) <= 100
    )


def get_digital_human_client_id() -> str:
    """Cookie为恢复权威，旧请求头用于首次兼容；两者都不放宽格式校验。"""
    cookie_value = request.cookies.get(COOKIE_NAME, "").strip()
    header_value = request.headers.get("X-Digital-Human-Client-ID", "").strip()
    if _valid_client_id(cookie_value):
        client_id = cookie_value
    elif _valid_client_id(header_value):
        client_id = header_value
    else:
        raise ValueError("缺少或无效的数字人客户端标识")
    g.digital_human_client_id = client_id
    return client_id


def persist_digital_human_identity(response):
    """仅写入HttpOnly身份Cookie，不把身份值暴露给前端响应体。"""
    client_id = getattr(g, "digital_human_client_id", None)
    if client_id and request.cookies.get(COOKIE_NAME) != client_id:
        response.set_cookie(
            COOKIE_NAME,
            client_id,
            max_age=COOKIE_MAX_AGE,
            httponly=True,
            secure=request.is_secure,
            samesite="Lax",
            path="/api/digital-human",
        )
    return response
