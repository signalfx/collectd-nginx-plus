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
        expected_records = [expected_record_1, expected_record_2]

        self.plugin._emit_server_zone_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_emit_upsteams_metrics(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('upstream.requests', 'guage', 'requests')]
        expected_record_1 = MetricRecord('upstream.requests', 'guage', 104616, self.plugin.instance_id,
            {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.1:8080'})
        expected_record_2 = MetricRecord('upstream.requests', 'guage', 0, self.plugin.instance_id,
            {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.1:8081'})

        expected_record_3 = MetricRecord('upstream.requests', 'guage', 413822, self.plugin.instance_id,
            {'upstream.name' : 'hg-backend', 'upstream.peer.name' : '10.0.0.1:8088'})
        expected_record_4 = MetricRecord('upstream.requests', 'guage', 0, self.plugin.instance_id,
            {'upstream.name' : 'hg-backend', 'upstream.peer.name' : '10.0.0.1:8089'})

        expected_records = [expected_record_1, expected_record_2, expected_record_3, expected_record_4]

        self.plugin._emit_upstreams_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_emit_stream_server_zone_metrics(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('stream.server.zone.connections', 'guage', 'connections')]
        expected_record_1 = MetricRecord('stream.server.zone.connections', 'guage', 382002, self.plugin.instance_id, {'stream.server.zone.name' : 'postgresql_loadbalancer'})
        expected_record_2 = MetricRecord('stream.server.zone.connections', 'guage', 219222, self.plugin.instance_id, {'stream.server.zone.name' : 'dns_loadbalancer'})

        expected_records = [expected_record_1, expected_record_2]

        self.plugin._emit_stream_server_zone_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_emit_stream_upstreams_metrics(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('stream.upstreams.connections', 'guage', 'connections')]
        expected_record_1 = MetricRecord('stream.upstreams.connections', 'guage', 1, self.plugin.instance_id,
            {'stream.upstream.name' : 'postgresql_backends', 'stream.upstream.peer.name' : '10.0.0.2:15432'})
        expected_record_2 = MetricRecord('stream.upstreams.connections', 'guage', 191001, self.plugin.instance_id,
            {'stream.upstream.name' : 'postgresql_backends', 'stream.upstream.peer.name' : '10.0.0.2:15433'})

        expected_record_3 = MetricRecord('stream.upstreams.connections', 'guage', 146148, self.plugin.instance_id,
            {'stream.upstream.name' : 'dns_udp_backends', 'stream.upstream.peer.name' : '10.0.0.5:53'})
        expected_record_4 = MetricRecord('stream.upstreams.connections', 'guage', 73074, self.plugin.instance_id,
            {'stream.upstream.name' : 'dns_udp_backends', 'stream.upstream.peer.name' : '10.0.0.2:53'})

        expected_records = [expected_record_1, expected_record_2, expected_record_3, expected_record_4]

        self.plugin._emit_stream_upstreams_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_emit_cache_metrics(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('caches.size', 'guage', 'size')]
        expected_record = MetricRecord('caches.size', 'guage', 532680704, self.plugin.instance_id, {'cache.name' : 'http_cache'})

        self.plugin._emit_cache_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

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

    def _verify_records_captured(self, expected_records):
        for expected_record in expected_records:
            self.assertIsNotNone(next((record for record in self.mock_sink.captured_records if self._compare_records(expected_record, record)), None),
            'Captured records does not contain: ' + expected_record.to_string() + ' captured records: {}'.format([record.to_string() for record in self.mock_sink.captured_records]))

    def _compare_records(self, expected_record, actual_record):
        try:
            self._validate_single_record(expected_record, actual_record)
            return True
        except Exception as ex:
            pass
        return False


class MockMetricSink:
    def __init__(self):
        self.captured_records = []

    def emit(self, metric_record):
        self.captured_records.append(metric_record)
