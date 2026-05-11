"""
Oracle database connection management for Cerner Millennium ETL.
"""

import logging
from typing import Optional
from contextlib import contextmanager
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionPool:
    def __init__(self, connection_string: str, min_size: int = 5, max_size: int = 20):
        self.connection_string = connection_string
        self.min_size = min_size
        self.max_size = max_size
        self._connections: list[dict] = []
        self._in_use: list[dict] = []

    def initialize(self) -> None:
        logger.info(f"Initializing connection pool (min={self.min_size}, max={self.max_size})")
        for _ in range(self.min_size):
            conn = self._create_connection()
            self._connections.append(conn)

    def _create_connection(self) -> dict:
        return {"connected": True, "created_at": datetime.utcnow()}

    @contextmanager
    def get_connection(self):
        if self._connections:
            conn = self._connections.pop()
        else:
            conn = self._create_connection()
        self._in_use.append(conn)
        try:
            yield conn
        finally:
            self._in_use.remove(conn)
            if len(self._connections) < self.max_size:
                self._connections.append(conn)

    def close_all(self) -> None:
        self._connections.clear()
        self._in_use.clear()
        logger.info("Connection pool closed")


class OracleDB:
    def __init__(self, connection_string: Optional[str] = None):
        self.connection_string = connection_string
        self._pool: Optional[ConnectionPool] = None

    def connect(self) -> bool:
        if self._pool:
            return True
        if self.connection_string:
            self._pool = ConnectionPool(self.connection_string)
            self._pool.initialize()
            return True
        logger.warning("No connection string provided, operating in mock mode")
        return True

    def disconnect(self) -> None:
        if self._pool:
            self._pool.close_all()
            self._pool = None

    def is_connected(self) -> bool:
        return self._pool is not None

    def execute(self, query: str, params: Optional[dict] = None) -> list[dict]:
        logger.info(f"Executing SQL (mock): {query[:100]}...")
        return []

    def execute_batch(self, query: str, params: list[dict]) -> int:
        logger.info(f"Executing batch SQL (mock): {query[:100]}...")
        return len(params)