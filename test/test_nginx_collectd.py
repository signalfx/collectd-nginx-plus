#!/usr/bin/env python
import os
import sys
import string
import json
import random
from mock import Mock

# Mock out the collectd module
# TODO: Write a mock implementation of collectd instead of just stubbing
sys.modules['collectd'] = Mock()

from unittest import TestCase
from plugin.nginx_plus_collectd import NginxPlusPlugin, MetricRecord, MetricDefinition

class NginxCollectdTest(TestCase):
    def setUp(self):
        self.plugin = NginxPlusPlugin()
        self.plugin.instance_id = self._random_string()
        self.mock_sink = MockMetricSink()

    def test_emit_top_level_metrics(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('connections.accepted', 'guage', 'connections.accepted')]
        expected_record = MetricRecord('connections.accepted', 'guage', 14527228, self.plugin.instance_id, {'nginx.version' : '1.11.10'})

        self.plugin._emit_top_level_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_emit_server_zone_metrics(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('server.zone.requests', 'guage', 'requests')]
        expected_record_1 = MetricRecord('server.zone.requests', 'guage', 465034, self.plugin.instance_id, {'server.zone.name' : 'hg.nginx.org'})
        expected_record_2 = MetricRecord('server.zone.requests', 'guage', 384296, self.plugin.instance_id, {'server.zone.name' : 'trac.nginx.org'})

        self.plugin._emit_server_zone_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(2, len(self.mock_sink.captured_records))
        #self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def _random_string(self, length=8):
        return ''.join(random.choice(string.lowercase) for i in range(length))

    def _random_int(self, start=0, stop=100000):
        return random.randint(start, stop)

    def _read_test_resource_json(self, relative_path):
        abs_path = os.path.join(os.path.dirname(__file__), relative_path)
        with open(abs_path) as json_file:
            return json.load(json_file)

    def _validate_single_record(self, expected_record, actual_record):
        self.assertIsNotNone(actual_record)
        self.assertEquals(expected_record.metric_name, actual_record.metric_name)
        self.assertEquals(expected_record.metric_type, actual_record.metric_type)
        self.assertEquals(expected_record.metric_value, actual_record.metric_value)
        self.assertEquals(expected_record.instance_id, actual_record.instance_id)
        self.assertDictEqual(expected_record.dimensions, actual_record.dimensions)
        self.assertIsNotNone(actual_record.timestamp)

    #def _verify_records_captured(self, expected_records):
    #    for expected_record in expected_records:


    def _compare_records(self, expected_record, actual_record):
        try:
            self._validate_single_record(expected_record, actual_record)
            return True
        except ex:
            pass
        return False


class MockMetricSink:
    def __init__(self):
        self.captured_records = []

    def emit(self, metric_record):
        self.captured_records.append(metric_record)
