import re
from typing import Any

import psycopg2

from database import get_db_connection


def normalize_institution_name(name: str) -> str:
    cleaned_name = " ".join((name or "").strip().split())
    if not cleaned_name:
        raise ValueError("Institution name is required")
    return cleaned_name


def normalize_institution_code(code: str) -> str:
    cleaned_code = re.sub(r"[^A-Za-z0-9-]", "", (code or "").strip().upper())
    if not cleaned_code:
        raise ValueError("Institution code is required")
    return cleaned_code


def normalize_subdomain(subdomain: str | None) -> str | None:
    if subdomain is None:
        return None
    cleaned_subdomain = re.sub(r"[^a-z0-9-]", "", (subdomain or "").strip().lower())
    return cleaned_subdomain or None


def extract_institution_code_from_host(host: str | None) -> str | None:
    normalized_host = (host or "").split(":", 1)[0].strip().lower()
    if not normalized_host or normalized_host in {"localhost", "127.0.0.1"}:
        return None

    parts = [part for part in normalized_host.split(".") if part]
    if len(parts) < 3:
        return None

    candidate = parts[0]
    if candidate == "www":
        return None
    return normalize_institution_code(candidate)


def get_default_institution(connection=None) -> dict[str, Any] | None:
    def fetch(conn):
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, name, code, subdomain, plan_name, status
                    FROM institutions
                    ORDER BY is_default DESC, id ASC
                    LIMIT 1
                    """
                )
                row = cur.fetchone()
            return _row_to_institution(row)
        except psycopg2.Error:
            return _fallback_institution()

    if connection is not None:
        return fetch(connection)

    with get_db_connection() as conn:
        return fetch(conn)


def get_institution_by_code(code: str | None, connection=None) -> dict[str, Any] | None:
    normalized_code = normalize_institution_code(code or "") if code else None
    if not normalized_code:
        return None

    def fetch(conn):
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, name, code, subdomain, plan_name, status
                    FROM institutions
                    WHERE UPPER(code) = %s
                    LIMIT 1
                    """,
                    (normalized_code,),
                )
                row = cur.fetchone()
            return _row_to_institution(row)
        except psycopg2.Error:
            fallback = _fallback_institution()
            return fallback if fallback["code"] == normalized_code else None

    if connection is not None:
        return fetch(connection)

    with get_db_connection() as conn:
        return fetch(conn)


def list_institutions():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        i.id,
                        i.name,
                        i.code,
                        i.subdomain,
                        i.plan_name,
                        i.status,
                        i.is_default,
                        COUNT(DISTINCT u.id) AS user_count,
                        COUNT(DISTINCT s.id) AS student_count
                    FROM institutions i
                    LEFT JOIN users u ON u.institution_id = i.id
                    LEFT JOIN students s ON s.institution_id = i.id
                    GROUP BY i.id, i.name, i.code, i.subdomain, i.plan_name, i.status, i.is_default
                    ORDER BY i.is_default DESC, i.name ASC
                    """
                )
                rows = cur.fetchall()
    except psycopg2.Error:
        fallback = _fallback_institution()
        return [{
            **fallback,
            "is_default": True,
            "user_count": 0,
            "student_count": 0,
        }]

    return [
        {
            "id": row[0],
            "name": row[1],
            "code": row[2],
            "subdomain": row[3],
            "plan_name": row[4],
            "status": row[5],
            "is_default": row[6],
            "user_count": row[7],
            "student_count": row[8],
        }
        for row in rows
    ]


def create_institution(name: str, code: str, subdomain: str | None = None, plan_name: str = "starter"):
    normalized_name = normalize_institution_name(name)
    normalized_code = normalize_institution_code(code)
    normalized_subdomain = normalize_subdomain(subdomain) or normalized_code.lower()

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1
                FROM institutions
                WHERE UPPER(code) = %s OR LOWER(subdomain) = LOWER(%s)
                """,
                (normalized_code, normalized_subdomain),
            )
            if cur.fetchone():
                raise ValueError("Institution code or subdomain already exists")

            cur.execute(
                """
                INSERT INTO institutions (name, code, subdomain, plan_name, status, is_default)
                VALUES (%s, %s, %s, %s, 'active', FALSE)
                RETURNING id, name, code, subdomain, plan_name, status
                """,
                (normalized_name, normalized_code, normalized_subdomain, plan_name),
            )
            row = cur.fetchone()

    return _row_to_institution(row)


def _row_to_institution(row):
    if not row:
        return None
    return {
        "id": row[0],
        "name": row[1],
        "code": row[2],
        "subdomain": row[3],
        "plan_name": row[4],
        "status": row[5],
    }


def _fallback_institution():
    return {
        "id": 1,
        "name": "Default Campus",
        "code": "DEFAULT",
        "subdomain": "default",
        "plan_name": "starter",
        "status": "active",
    }
