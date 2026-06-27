from __future__ import annotations

from typing import Any

from .types import SeatConfig, SeatResult


class StorageError(RuntimeError):
    pass


class MySQLStorage:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    def _connect(self):
        try:
            import pymysql
        except ImportError as exc:
            raise StorageError("Missing dependency pymysql. Run setup.ps1 first.") from exc

        return pymysql.connect(
            host=self.config["host"],
            port=int(self.config["port"]),
            user=self.config["user"],
            password=self.config.get("password", ""),
            database=self.config["database"],
            charset=self.config.get("charset", "utf8mb4"),
            cursorclass=pymysql.cursors.DictCursor,
        )

    def fetch_seats(self) -> list[SeatConfig]:
        sql = """
            SELECT seat_id, floor, zone, camera_id, roi_x1, roi_y1, roi_x2, roi_y2, is_active
            FROM seat_config
            ORDER BY seat_id
        """
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                rows = cursor.fetchall()
        return [
            SeatConfig(
                seat_id=str(row["seat_id"]),
                floor=int(row["floor"]),
                zone=str(row["zone"]),
                camera_id=str(row["camera_id"]),
                roi_x1=int(row["roi_x1"]),
                roi_y1=int(row["roi_y1"]),
                roi_x2=int(row["roi_x2"]),
                roi_y2=int(row["roi_y2"]),
                is_active=bool(row["is_active"]),
            )
            for row in rows
        ]

    def write_status_log(self, results: list[SeatResult]) -> None:
        if not results:
            return
        sql = """
            INSERT INTO seat_status_log
                (seat_id, floor, zone, detected_at, has_person, has_object, status, suspect_duration)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        rows = [
            (
                result.seat_id,
                result.floor,
                result.zone,
                result.detected_at,
                1 if result.has_person else 0,
                1 if result.has_object else 0,
                result.status,
                result.suspect_duration,
            )
            for result in results
        ]
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.executemany(sql, rows)
            conn.commit()


class RedisStorage:
    def __init__(self, config: dict[str, Any], ttl_sec: int) -> None:
        self.config = config
        self.ttl_sec = ttl_sec
        self._client = None

    def _connect(self):
        if self._client is not None:
            return self._client
        try:
            import redis
        except ImportError as exc:
            raise StorageError("Missing dependency redis. Run setup.ps1 first.") from exc

        self._client = redis.Redis(
            host=self.config["host"],
            port=int(self.config["port"]),
            db=int(self.config.get("db", 0)),
            decode_responses=bool(self.config.get("decode_responses", True)),
        )
        self._client.ping()
        return self._client

    def get_suspect_min(self, seat_id: str) -> int:
        try:
            value = self._connect().hget(f"seat:{seat_id}", "suspect_min")
        except Exception as exc:
            raise StorageError(f"Failed to read Redis suspect_min for {seat_id}: {exc}") from exc
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    def write_results(self, results: list[SeatResult]) -> None:
        if not results:
            return
        try:
            client = self._connect()
            pipe = client.pipeline()
            for result in results:
                key = f"seat:{result.seat_id}"
                pipe.hset(key, mapping=result.redis_mapping())
                pipe.expire(key, self.ttl_sec)
            pipe.execute()
        except Exception as exc:
            raise StorageError(f"Failed to write Redis seat results: {exc}") from exc


def seats_from_fallback(config: dict[str, Any]) -> list[SeatConfig]:
    return [
        SeatConfig(
            seat_id=str(row["seat_id"]),
            floor=int(row["floor"]),
            zone=str(row["zone"]),
            camera_id=str(row["camera_id"]),
            roi_x1=int(row["roi_x1"]),
            roi_y1=int(row["roi_y1"]),
            roi_x2=int(row["roi_x2"]),
            roi_y2=int(row["roi_y2"]),
            is_active=bool(int(row.get("is_active", 1))),
        )
        for row in config.get("fallback_seats", [])
    ]

