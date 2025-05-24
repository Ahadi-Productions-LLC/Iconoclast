import json
import logging
import unittest
from pathlib import Path

from app.data.database.raw_data import RawDataCatalog
from app.tests.data.utils import load_catalog_with_path


class RawDataDeserializationTests(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_raw_data_missing_field_defaults_none(self):
        data_path = Path(__file__).parent / 'test_files' / 'raw_data_missing_field.json'
        raw_data = load_catalog_with_path(RawDataCatalog, data_path)

        datum = raw_data[0]
        self.assertEqual(datum.value[0].field_1, 'f1')
        self.assertEqual(datum.value[0].field_2, 'f2')
        self.assertEqual(datum.value[0].field_3, None)