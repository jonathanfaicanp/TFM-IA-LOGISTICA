"""Startup using only committed synthetic input and explicit CSV selection."""
import csv
import os
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from src.api import create_app, build_analytical_service


class SampleStartupTests(unittest.TestCase):
    def test_missing_private_csv_does_not_select_demo_silently(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch('src.api.DEFAULT_DATA_PATH', Path(directory)/'absent.csv'):
                with self.assertRaises(FileNotFoundError):
                    build_analytical_service({})

    def test_clean_environment_sample_startup_and_examples(self):
        path = Path(__file__).resolve().parents[1] / 'examples/sample_operativa.csv'
        with path.open(encoding='utf-8', newline='') as source:
            rows = list(csv.DictReader(source, delimiter=';'))
        environment = {'TFM_DATA_SOURCE': 'csv', 'TFM_DATA_PATH': str(path)}
        with patch.dict(os.environ, environment, clear=True), TestClient(create_app()) as client:
            self.assertEqual(client.get('/health').json(), {'status': 'ok'})
            for row, expected in zip(rows[-3:], ('NO_RELEVANT_DEVIATION', 'REVIEW', 'NOT_EVALUABLE')):
                payload = dict(trip_id=row['Codigo Viaje'], vehicle_id=row['Codigo Vehiculo'],
                               timestamp=row['Fecha de inicio'], distance_m=float(row['Distancia']),
                               consumption_ml=float(row['Consumo']), duration_seconds=float(row['Duracion']))
                response = client.post('/evaluate', json=payload)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()['overall_status'], expected)
                self.assertEqual(response.json()['analysis_coverage'], 'NONE' if expected == 'NOT_EVALUABLE' else 'COMPLETE')
