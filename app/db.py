"""Thin wrapper over mysql-connector: one lazy connection, dict rows, friendly errors."""
import mysql.connector
from mysql.connector import Error

from .config import DB_CONFIG
from .errors import ParkingError, friendly_message


class Database:
    def __init__(self, config=None):
        self.config = dict(config or DB_CONFIG)
        self._conn = None

    def _connection(self):
        if self._conn is None or not self._conn.is_connected():
            try:
                self._conn = mysql.connector.connect(autocommit=True, connection_timeout=5, **self.config)
            except Error as e:
                raise ParkingError(friendly_message(e)) from e
        return self._conn

    def query(self, sql, params=None):
        """Run a SELECT and return a list of dict rows."""
        try:
            cur = self._connection().cursor(dictionary=True)
            cur.execute(sql, params or ())
            rows = cur.fetchall()
            cur.close()
            return rows
        except Error as e:
            raise ParkingError(friendly_message(e)) from e

    def query_one(self, sql, params=None):
        rows = self.query(sql, params)
        return rows[0] if rows else None

    def execute(self, sql, params=None):
        """Run INSERT / UPDATE / DELETE. Returns (rows_affected, last_insert_id)."""
        try:
            cur = self._connection().cursor()
            cur.execute(sql, params or ())
            result = (cur.rowcount, cur.lastrowid)
            cur.close()
            return result
        except Error as e:
            raise ParkingError(friendly_message(e)) from e

    def call(self, proc, args=()):
        """Call a stored procedure; returns a list of result sets (each a list of dicts)."""
        try:
            cur = self._connection().cursor()
            cur.callproc(proc, list(args))
            sets = []
            stored = cur.stored_results
            for res in (stored() if callable(stored) else stored):
                cols = res.column_names
                sets.append([dict(zip(cols, row)) for row in res.fetchall()])
            cur.close()
            return sets
        except Error as e:
            raise ParkingError(friendly_message(e)) from e

    def close(self):
        if self._conn is not None and self._conn.is_connected():
            self._conn.close()
