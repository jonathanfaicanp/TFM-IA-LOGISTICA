"""Read-only access to the historical trips stored in SQL Server."""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any


REQUIRED_ENVIRONMENT_VARIABLES = (
    "TFM_DB_SERVER",
    "TFM_DB_DATABASE",
    "TFM_DB_USER",
    "TFM_DB_PASSWORD",
)
DEFAULT_DRIVER = "ODBC Driver 17 for SQL Server"

HISTORICAL_QUERY = """
SELECT
    [Codigo Viaje],
    [Codigo Vehiculo],
    [Nombre Vehiculo],
    [Fecha de inicio],
    [Duracion],
    [Distancia],
    [Velocidad maxima],
    [Consumo],
    [Indicador de conduccion]
FROM [dbo].[WF_OPERATIVA_CAMIONES]
WHERE [Fecha de inicio] >= ?
  AND [Fecha de inicio] < ?
""".strip()

TRIP_BY_ID_QUERY = """
SELECT
    [Codigo Viaje],
    [Codigo Vehiculo],
    [Fecha de inicio],
    [Distancia],
    [Consumo],
    [Duracion]
FROM [dbo].[WF_OPERATIVA_CAMIONES]
WHERE [Codigo Viaje] = ?
""".strip()

ANALYTICAL_ROWS_QUERY = """
SELECT
    [Codigo Viaje],
    [Codigo Vehiculo],
    [Fecha de inicio],
    [Distancia],
    [Consumo],
    [Duracion]
FROM [dbo].[WF_OPERATIVA_CAMIONES]
WHERE [Fecha de inicio] >= ?
  AND [Fecha de inicio] < ?
""".strip()


def _to_analytical_row(column_names: list[str], sql_row: Any) -> dict[str, object]:
    analytical_row = dict(zip(column_names, sql_row))
    consumption_liters = analytical_row["Consumo"]
    analytical_row["Consumo"] = (
        None if consumption_liters is None else float(consumption_liters) * 1000
    )
    return analytical_row


@dataclass(frozen=True)
class SqlServerConfig:
    server: str
    database: str
    user: str
    password: str
    driver: str = DEFAULT_DRIVER

    @classmethod
    def from_environment(cls, environment: Mapping[str, str] | None = None) -> "SqlServerConfig":
        values = os.environ if environment is None else environment
        missing = [name for name in REQUIRED_ENVIRONMENT_VARIABLES if not values.get(name)]
        if missing:
            raise ValueError(
                "Falta configuración obligatoria de SQL Server: " + ", ".join(missing)
            )
        return cls(
            server=values["TFM_DB_SERVER"],
            database=values["TFM_DB_DATABASE"],
            user=values["TFM_DB_USER"],
            password=values["TFM_DB_PASSWORD"],
            driver=values.get("TFM_DB_DRIVER", DEFAULT_DRIVER),
        )

    def connection_string(self) -> str:
        def odbc_value(value: str) -> str:
            return "{" + value.replace("}", "}}") + "}"

        return ";".join(
            (
                f"DRIVER={odbc_value(self.driver)}",
                f"SERVER={odbc_value(self.server)}",
                f"DATABASE={odbc_value(self.database)}",
                f"UID={odbc_value(self.user)}",
                f"PWD={odbc_value(self.password)}",
            )
        )


class SqlHistoricalRepository:
    def __init__(
        self,
        config: SqlServerConfig,
        connection_factory: Callable[[str], Any] | None = None,
    ):
        self.config = config
        self._connection_factory = connection_factory or self._pyodbc_connect

    @staticmethod
    def _pyodbc_connect(connection_string: str) -> Any:
        try:
            import pyodbc
        except ImportError as error:
            raise RuntimeError(
                "El origen SQL requiere la dependencia pyodbc instalada."
            ) from error
        return pyodbc.connect(connection_string)

    @classmethod
    def from_environment(
        cls, environment: Mapping[str, str] | None = None
    ) -> "SqlHistoricalRepository":
        return cls(SqlServerConfig.from_environment(environment))

    def load_historical_rows(self) -> list[dict[str, object]]:
        connection = self._connection_factory(self.config.connection_string())
        try:
            cursor = connection.cursor()
            cursor.execute(
                HISTORICAL_QUERY,
                datetime(2024, 1, 1),
                datetime(2026, 1, 1),
            )
            column_names = [description[0] for description in cursor.description]
            historical_rows = []
            for sql_row in cursor.fetchall():
                historical_rows.append(_to_analytical_row(column_names, sql_row))
            return historical_rows
        finally:
            connection.close()

    def get_trip_by_id(self, trip_id: str) -> dict[str, object] | None:
        """Return one operational trip using the analytical units contract."""
        connection = self._connection_factory(self.config.connection_string())
        try:
            cursor = connection.cursor()
            cursor.execute(TRIP_BY_ID_QUERY, trip_id)
            sql_row = cursor.fetchone()
            if sql_row is None:
                return None

            column_names = [description[0] for description in cursor.description]
            return _to_analytical_row(column_names, sql_row)
        finally:
            connection.close()

    def load_rows_between(
        self, start_datetime: datetime, end_datetime: datetime
    ) -> list[dict[str, object]]:
        """Load analytical rows in the half-open interval between two dates."""
        connection = self._connection_factory(self.config.connection_string())
        try:
            cursor = connection.cursor()
            cursor.execute(
                ANALYTICAL_ROWS_QUERY,
                start_datetime,
                end_datetime,
            )
            column_names = [description[0] for description in cursor.description]
            return [
                _to_analytical_row(column_names, sql_row)
                for sql_row in cursor.fetchall()
            ]
        finally:
            connection.close()
