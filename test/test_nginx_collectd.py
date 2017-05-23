#!/usr/bin/env python
import os
import sys
import string
import json
import random
from mock import Mock, MagicMock

# Mock out the collectd module
# TODO: Write a mock implementation of collectd instead of just stubbing
sys.modules['collectd'] = Mock()

from unittest import TestCase
from plugin.nginx_plus_collectd import NginxPlusPlugin, MetricRecord, MetricDefinition,\
                                        DEFAULT_CONNECTION_METRICS, DEFAULT_SERVER_ZONE_METRICS,\
                                        DEFAULT_UPSTREAM_METRICS, DEFAULT_STREAM_SERVER_ZONE_METRICS,\
                                        DEFAULT_STREAM_UPSTREAM_METRICS, SERVER_ZONE_METRICS, SERVER_ZONE,\
                                        MEMORY_ZONE_METRICS, MEMORY_ZONE, UPSTREAM_METRICS, UPSTREAM,\
                                        CACHE_METRICS, CACHE, STREAM_SERVER_ZONE_METRICS, STREAM_SERVER_ZONE,\
                                        STREAM_UPSTREAM_METRICS, STREAM_UPSTREAM, STATUS_IP, STATUS_PORT

class NginxCollectdTest(TestCase):
    def setUp(self):
        self.plugin = NginxPlusPlugin()
        self.plugin._instance_id = self._random_string()
        self.mock_sink = MockMetricSink()

    def test_instance_id_set(self):
        expected_instance_id = '206.251.255.64'
        status_json = self._read_test_resource_json('resources/status_response.json')

        mock_nginx_agent = Mock()
        mock_nginx_agent.get_status = MagicMock(return_value=status_json)

        self.plugin._instance_id = None
        self.plugin.nginx_agent = mock_nginx_agent

        actual_instance_id = self.plugin.instance_id
        self.assertEquals(expected_instance_id, actual_instance_id)

    def test_no_emit_invalid_path(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('connection.accepted', 'guage', 'foo.bar')]
        self.plugin._emit_top_level_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(0, len(self.mock_sink.captured_records))

    def test_config_callback_only_defaults_emitters(self):
        expected_metric_names = self._get_default_metric_names()

        mock_config = Mock()
        mock_config.children = {}

        self.plugin.config_callback(mock_config)
        actual_metric_names = self._get_metrics_names_from_plugin()

        self.assertEquals(len(expected_metric_names), len(actual_metric_names))
        self.assertItemsEqual(expected_metric_names, actual_metric_names)

    def test_config_callback_server_zone_emitters(self):
        expected_metric_names = self._get_default_metric_names()
        expected_metric_names.extend(self._extract_metric_names_from_definitions(SERVER_ZONE_METRICS))

        mock_config = Mock()
        mock_config_child = Mock()
        mock_config_child.key = SERVER_ZONE
        mock_config_child.values = ['true']

        mock_config.children = [mock_config_child]

        self.plugin.config_callback(mock_config)
        actual_metric_names = self._get_metrics_names_from_plugin()

        self.assertEquals(len(expected_metric_names), len(actual_metric_names))
        self.assertItemsEqual(expected_metric_names, actual_metric_names)

    def test_config_callback_server_zone_emitters(self):
        expected_metric_names = self._get_default_metric_names()
        expected_metric_names.extend(self._extract_metric_names_from_definitions(MEMORY_ZONE_METRICS))

        mock_config = Mock()
        mock_config_child = Mock()
        mock_config_child.key = MEMORY_ZONE
        mock_config_child.values = ['true']

        mock_config.children = [mock_config_child]

        self.plugin.config_callback(mock_config)
        actual_metric_names = self._get_metrics_names_from_plugin()

        self.assertEquals(len(expected_metric_names), len(actual_metric_names))
        self.assertItemsEqual(expected_metric_names, actual_metric_names)

    def test_config_callback_upstream_emitters(self):
        expected_metric_names = self._get_default_metric_names()
        expected_metric_names.extend(self._extract_metric_names_from_definitions(UPSTREAM_METRICS))

        mock_config = Mock()
        mock_config_child = Mock()
        mock_config_child.key = UPSTREAM
        mock_config_child.values = ['true']

        mock_config.children = [mock_config_child]

        self.plugin.config_callback(mock_config)
        actual_metric_names = self._get_metrics_names_from_plugin()

        self.assertEquals(len(expected_metric_names), len(actual_metric_names))
        self.assertItemsEqual(expected_metric_names, actual_metric_names)

    def test_config_callback_cache_emitters(self):
        expected_metric_names = self._get_default_metric_names()
        expected_metric_names.extend(self._extract_metric_names_from_definitions(CACHE_METRICS))

        mock_config = Mock()
        mock_config_child = Mock()
        mock_config_child.key = CACHE
        mock_config_child.values = ['true']

        mock_config.children = [mock_config_child]

        self.plugin.config_callback(mock_config)
        actual_metric_names = self._get_metrics_names_from_plugin()

        self.assertEquals(len(expected_metric_names), len(actual_metric_names))
        self.assertItemsEqual(expected_metric_names, actual_metric_names)

    def test_config_callback_stream_server_zone_emitters(self):
        expected_metric_names = self._get_default_metric_names()
        expected_metric_names.extend(self._extract_metric_names_from_definitions(STREAM_SERVER_ZONE_METRICS))

        mock_config = Mock()
        mock_config_child = Mock()
        mock_config_child.key = STREAM_SERVER_ZONE
        mock_config_child.values = ['true']

        mock_config.children = [mock_config_child]

        self.plugin.config_callback(mock_config)
        actual_metric_names = self._get_metrics_names_from_plugin()

        self.assertEquals(len(expected_metric_names), len(actual_metric_names))
        self.assertItemsEqual(expected_metric_names, actual_metric_names)

    def test_config_callback_stream_upstream_emitters(self):
        expected_metric_names = self._get_default_metric_names()
        expected_metric_names.extend(self._extract_metric_names_from_definitions(STREAM_UPSTREAM_METRICS))

        mock_config = Mock()
        mock_config_child = Mock()
        mock_config_child.key = STREAM_UPSTREAM
        mock_config_child.values = ['true']

        mock_config.children = [mock_config_child]

        self.plugin.config_callback(mock_config)
        actual_metric_names = self._get_metrics_names_from_plugin()

        self.assertEquals(len(expected_metric_names), len(actual_metric_names))
        self.assertItemsEqual(expected_metric_names, actual_metric_names)

    def test_config_callback_status_ip_port(self):
        expected_ip = '192.168.0.24'
        expected_port = '411'

        mock_config_ip_child = Mock()
        mock_config_ip_child.key = STATUS_IP
        mock_config_ip_child.values = [expected_ip]

        mock_config_port_child = Mock()
        mock_config_port_child.key = STATUS_PORT
        mock_config_port_child.values = [expected_port]

        mock_config = Mock()
        mock_config.children = [mock_config_ip_child, mock_config_port_child]

        self.plugin.config_callback(mock_config)

        self.assertEquals(expected_ip, self.plugin.nginx_agent.status_ip)
        self.assertEquals(expected_port, self.plugin.nginx_agent.status_port)

    def test_read_callback(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        mock_nginx_agent = Mock()
        mock_nginx_agent.get_status = MagicMock(return_value=status_json)

        mock_emitter_1 = Mock()
        mock_emitter_2 = Mock()

        mock_sink = Mock()

        self.plugin.sink = mock_sink
        self.plugin.nginx_agent = mock_nginx_agent
        self.plugin.emitters = [mock_emitter_1, mock_emitter_2]

        self.plugin.read_callback()

        mock_emitter_1.emit.assert_called_with(status_json, mock_sink)
        mock_emitter_2.emit.assert_called_with(status_json, mock_sink)

    def test_read_callback_null_instance_id(self):
        status_json = {'foo' : 'bar'} # Does not include address, which is used for instance id

        mock_nginx_agent = Mock()
        mock_nginx_agent.get_status = MagicMock(return_value=status_json)

        mock_emitter_1 = Mock()
        mock_emitter_2 = Mock()

        mock_sink = Mock()

        self.plugin.sink = mock_sink
        self.plugin.nginx_agent = mock_nginx_agent
        self.plugin.emitters = [mock_emitter_1, mock_emitter_2]

        self.plugin.read_callback()

        mock_emitter_1.assert_not_called()
        mock_emitter_2.assert_not_called()

    def test_connections_accepted(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('connections.accepted', 'guage', 'connections.accepted')]
        expected_record = MetricRecord('connections.accepted', 'guage', 14527228, self.plugin.instance_id, {'nginx.version' : '1.11.10'})

        self.plugin._emit_top_level_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_connections_dropped(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('connections.dropped', 'guage', 'connections.dropped')]
        expected_record = MetricRecord('connections.dropped', 'guage', 0, self.plugin.instance_id, {'nginx.version' : '1.11.10'})

        self.plugin._emit_top_level_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_connections_idle(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('connections.idle', 'guage', 'connections.idle')]
        expected_record = MetricRecord('connections.idle', 'guage', 45, self.plugin.instance_id, {'nginx.version' : '1.11.10'})

        self.plugin._emit_top_level_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_ssl_successful(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('ssl.handshakes.successful', 'guage', 'ssl.handshakes')]
        expected_record = MetricRecord('ssl.handshakes.successful', 'guage', 166597, self.plugin.instance_id, {'nginx.version' : '1.11.10'})

        self.plugin._emit_top_level_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_ssl_failed(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('ssl.handshakes.failed', 'guage', 'ssl.handshakes_failed')]
        expected_record = MetricRecord('ssl.handshakes.failed', 'guage', 26154, self.plugin.instance_id, {'nginx.version' : '1.11.10'})

        self.plugin._emit_top_level_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_requests_total(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('requests.total', 'guage', 'requests.total')]
        expected_record = MetricRecord('requests.total', 'guage', 43878009, self.plugin.instance_id, {'nginx.version' : '1.11.10'})

        self.plugin._emit_top_level_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_requests_current(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('requests.current', 'guage', 'requests.current')]
        expected_record = MetricRecord('requests.current', 'guage', 5, self.plugin.instance_id, {'nginx.version' : '1.11.10'})

        self.plugin._emit_top_level_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_server_zone_requests(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('server.zone.requests', 'guage', 'requests')]
        expected_record_1 = MetricRecord('server.zone.requests', 'guage', 465034, self.plugin.instance_id, {'server.zone.name' : 'hg.nginx.org'})
        expected_record_2 = MetricRecord('server.zone.requests', 'guage', 384296, self.plugin.instance_id, {'server.zone.name' : 'trac.nginx.org'})
        expected_records = [expected_record_1, expected_record_2]

        self.plugin._emit_server_zone_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_server_zone_processing(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('server.zone.processing', 'guage', 'processing')]
        expected_record_1 = MetricRecord('server.zone.processing', 'guage', 0, self.plugin.instance_id, {'server.zone.name' : 'hg.nginx.org'})
        expected_record_2 = MetricRecord('server.zone.processing', 'guage', 3, self.plugin.instance_id, {'server.zone.name' : 'trac.nginx.org'})
        expected_records = [expected_record_1, expected_record_2]

        self.plugin._emit_server_zone_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_server_zone_discarded(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('server.zone.discarded', 'guage', 'discarded')]
        expected_record_1 = MetricRecord('server.zone.discarded', 'guage', 457, self.plugin.instance_id, {'server.zone.name' : 'hg.nginx.org'})
        expected_record_2 = MetricRecord('server.zone.discarded', 'guage', 41974, self.plugin.instance_id, {'server.zone.name' : 'trac.nginx.org'})
        expected_records = [expected_record_1, expected_record_2]

        self.plugin._emit_server_zone_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_server_zone_responses_total(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('server.zone.responses.total', 'guage', 'responses.total')]
        expected_record_1 = MetricRecord('server.zone.responses.total', 'guage', 464577, self.plugin.instance_id, {'server.zone.name' : 'hg.nginx.org'})
        expected_record_2 = MetricRecord('server.zone.responses.total', 'guage', 342319, self.plugin.instance_id, {'server.zone.name' : 'trac.nginx.org'})
        expected_records = [expected_record_1, expected_record_2]

        self.plugin._emit_server_zone_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_server_zone_responses_1xx(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('server.zone.responses.1xx', 'guage', 'responses.1xx')]
        expected_record_1 = MetricRecord('server.zone.responses.1xx', 'guage', 0, self.plugin.instance_id, {'server.zone.name' : 'hg.nginx.org'})
        expected_record_2 = MetricRecord('server.zone.responses.1xx', 'guage', 0, self.plugin.instance_id, {'server.zone.name' : 'trac.nginx.org'})
        expected_records = [expected_record_1, expected_record_2]

        self.plugin._emit_server_zone_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_server_zone_responses_2xx(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('server.zone.responses.2xx', 'guage', 'responses.2xx')]
        expected_record_1 = MetricRecord('server.zone.responses.2xx', 'guage', 450715, self.plugin.instance_id, {'server.zone.name' : 'hg.nginx.org'})
        expected_record_2 = MetricRecord('server.zone.responses.2xx', 'guage', 215961, self.plugin.instance_id, {'server.zone.name' : 'trac.nginx.org'})
        expected_records = [expected_record_1, expected_record_2]

        self.plugin._emit_server_zone_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_server_zone_responses_3xx(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('server.zone.responses.3xx', 'guage', 'responses.3xx')]
        expected_record_1 = MetricRecord('server.zone.responses.3xx', 'guage', 7834, self.plugin.instance_id, {'server.zone.name' : 'hg.nginx.org'})
        expected_record_2 = MetricRecord('server.zone.responses.3xx', 'guage', 78603, self.plugin.instance_id, {'server.zone.name' : 'trac.nginx.org'})
        expected_records = [expected_record_1, expected_record_2]

        self.plugin._emit_server_zone_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_server_zone_responses_4xx(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('server.zone.responses.4xx', 'guage', 'responses.4xx')]
        expected_record_1 = MetricRecord('server.zone.responses.4xx', 'guage', 5461, self.plugin.instance_id, {'server.zone.name' : 'hg.nginx.org'})
        expected_record_2 = MetricRecord('server.zone.responses.4xx', 'guage', 22380, self.plugin.instance_id, {'server.zone.name' : 'trac.nginx.org'})
        expected_records = [expected_record_1, expected_record_2]

        self.plugin._emit_server_zone_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_server_zone_responses_5xx(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('server.zone.responses.5xx', 'guage', 'responses.5xx')]
        expected_record_1 = MetricRecord('server.zone.responses.5xx', 'guage', 567, self.plugin.instance_id, {'server.zone.name' : 'hg.nginx.org'})
        expected_record_2 = MetricRecord('server.zone.responses.5xx', 'guage', 25375, self.plugin.instance_id, {'server.zone.name' : 'trac.nginx.org'})
        expected_records = [expected_record_1, expected_record_2]

        self.plugin._emit_server_zone_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_server_zone_bytes_received(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('server.zone.bytes.received', 'guage', 'received')]
        expected_record_1 = MetricRecord('server.zone.bytes.received', 'guage', 112274034, self.plugin.instance_id, {'server.zone.name' : 'hg.nginx.org'})
        expected_record_2 = MetricRecord('server.zone.bytes.received', 'guage', 123130586, self.plugin.instance_id, {'server.zone.name' : 'trac.nginx.org'})
        expected_records = [expected_record_1, expected_record_2]

        self.plugin._emit_server_zone_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_server_zone_bytes_sent(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('server.zone.bytes.sent', 'guage', 'sent')]
        expected_record_1 = MetricRecord('server.zone.bytes.sent', 'guage', 10968683492, self.plugin.instance_id, {'server.zone.name' : 'hg.nginx.org'})
        expected_record_2 = MetricRecord('server.zone.bytes.sent', 'guage', 5740717145, self.plugin.instance_id, {'server.zone.name' : 'trac.nginx.org'})
        expected_records = [expected_record_1, expected_record_2]

        self.plugin._emit_server_zone_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_memory_zone_pages_used(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('zones.pages.used', 'guage', 'pages.used')]
        expected_record = MetricRecord('zones.pages.used', 'guage', 6, self.plugin.instance_id, {'memory.zone.name' : 'nginxorg'})

        self.plugin._emit_memory_zone_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_memory_zone_pages_free(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('zones.pages.free', 'guage', 'pages.free')]
        expected_record = MetricRecord('zones.pages.free', 'guage', 1, self.plugin.instance_id, {'memory.zone.name' : 'nginxorg'})

        self.plugin._emit_memory_zone_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_upstreams_requests(self):
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

    def test_upstreams_active(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('upstreams.active', 'guage', 'active')]
        expected_record_1 = MetricRecord('upstreams.active', 'guage', 0, self.plugin.instance_id,
            {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.1:8080'})
        expected_record_2 = MetricRecord('upstreams.active', 'guage', 0, self.plugin.instance_id,
            {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.1:8081'})

        expected_record_3 = MetricRecord('upstreams.active', 'guage', 0, self.plugin.instance_id,
            {'upstream.name' : 'hg-backend', 'upstream.peer.name' : '10.0.0.1:8088'})
        expected_record_4 = MetricRecord('upstreams.active', 'guage', 0, self.plugin.instance_id,
            {'upstream.name' : 'hg-backend', 'upstream.peer.name' : '10.0.0.1:8089'})

        expected_records = [expected_record_1, expected_record_2, expected_record_3, expected_record_4]

        self.plugin._emit_upstreams_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_upstreams_responses_total(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('upstreams.responses.total', 'guage', 'responses.total')]
        expected_record_1 = MetricRecord('upstreams.responses.total', 'guage', 104616, self.plugin.instance_id,
            {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.1:8080'})
        expected_record_2 = MetricRecord('upstreams.responses.total', 'guage', 0, self.plugin.instance_id,
            {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.1:8081'})

        expected_record_3 = MetricRecord('upstreams.responses.total', 'guage', 413822, self.plugin.instance_id,
            {'upstream.name' : 'hg-backend', 'upstream.peer.name' : '10.0.0.1:8088'})
        expected_record_4 = MetricRecord('upstreams.responses.total', 'guage', 0, self.plugin.instance_id,
            {'upstream.name' : 'hg-backend', 'upstream.peer.name' : '10.0.0.1:8089'})

        expected_records = [expected_record_1, expected_record_2, expected_record_3, expected_record_4]

        self.plugin._emit_upstreams_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_upstreams_responses_1xx(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('upstreams.responses.1xx', 'guage', 'responses.1xx')]
        expected_record_1 = MetricRecord('upstreams.responses.1xx', 'guage', 0, self.plugin.instance_id,
            {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.1:8080'})
        expected_record_2 = MetricRecord('upstreams.responses.1xx', 'guage', 0, self.plugin.instance_id,
            {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.1:8081'})

        expected_record_3 = MetricRecord('upstreams.responses.1xx', 'guage', 0, self.plugin.instance_id,
            {'upstream.name' : 'hg-backend', 'upstream.peer.name' : '10.0.0.1:8088'})
        expected_record_4 = MetricRecord('upstreams.responses.1xx', 'guage', 0, self.plugin.instance_id,
            {'upstream.name' : 'hg-backend', 'upstream.peer.name' : '10.0.0.1:8089'})

        expected_records = [expected_record_1, expected_record_2, expected_record_3, expected_record_4]

        self.plugin._emit_upstreams_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_upstreams_responses_2xx(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('upstreams.responses.2xx', 'guage', 'responses.2xx')]
        expected_record_1 = MetricRecord('upstreams.responses.2xx', 'guage', 103711, self.plugin.instance_id,
            {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.1:8080'})
        expected_record_2 = MetricRecord('upstreams.responses.2xx', 'guage', 0, self.plugin.instance_id,
            {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.1:8081'})

        expected_record_3 = MetricRecord('upstreams.responses.2xx', 'guage', 408338, self.plugin.instance_id,
            {'upstream.name' : 'hg-backend', 'upstream.peer.name' : '10.0.0.1:8088'})
        expected_record_4 = MetricRecord('upstreams.responses.2xx', 'guage', 0, self.plugin.instance_id,
            {'upstream.name' : 'hg-backend', 'upstream.peer.name' : '10.0.0.1:8089'})

        expected_records = [expected_record_1, expected_record_2, expected_record_3, expected_record_4]

        self.plugin._emit_upstreams_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_upstreams_responses_3xx(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('upstreams.responses.3xx', 'guage', 'responses.3xx')]
        expected_record_1 = MetricRecord('upstreams.responses.3xx', 'guage', 538, self.plugin.instance_id,
            {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.1:8080'})
        expected_record_2 = MetricRecord('upstreams.responses.3xx', 'guage', 0, self.plugin.instance_id,
            {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.1:8081'})

        expected_record_3 = MetricRecord('upstreams.responses.3xx', 'guage', 0, self.plugin.instance_id,
            {'upstream.name' : 'hg-backend', 'upstream.peer.name' : '10.0.0.1:8088'})
        expected_record_4 = MetricRecord('upstreams.responses.3xx', 'guage', 0, self.plugin.instance_id,
            {'upstream.name' : 'hg-backend', 'upstream.peer.name' : '10.0.0.1:8089'})

        expected_records = [expected_record_1, expected_record_2, expected_record_3, expected_record_4]

        self.plugin._emit_upstreams_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_upstreams_responses_4xx(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('upstreams.responses.4xx', 'guage', 'responses.4xx')]
        expected_record_1 = MetricRecord('upstreams.responses.4xx', 'guage', 344, self.plugin.instance_id,
            {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.1:8080'})
        expected_record_2 = MetricRecord('upstreams.responses.4xx', 'guage', 0, self.plugin.instance_id,
            {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.1:8081'})

        expected_record_3 = MetricRecord('upstreams.responses.4xx', 'guage', 5471, self.plugin.instance_id,
            {'upstream.name' : 'hg-backend', 'upstream.peer.name' : '10.0.0.1:8088'})
        expected_record_4 = MetricRecord('upstreams.responses.4xx', 'guage', 0, self.plugin.instance_id,
            {'upstream.name' : 'hg-backend', 'upstream.peer.name' : '10.0.0.1:8089'})

        expected_records = [expected_record_1, expected_record_2, expected_record_3, expected_record_4]

        self.plugin._emit_upstreams_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_upstreams_responses_5xx(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('upstreams.responses.5xx', 'guage', 'responses.5xx')]
        expected_record_1 = MetricRecord('upstreams.responses.5xx', 'guage', 23, self.plugin.instance_id,
            {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.1:8080'})
        expected_record_2 = MetricRecord('upstreams.responses.5xx', 'guage', 0, self.plugin.instance_id,
            {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.1:8081'})

        expected_record_3 = MetricRecord('upstreams.responses.5xx', 'guage', 13, self.plugin.instance_id,
            {'upstream.name' : 'hg-backend', 'upstream.peer.name' : '10.0.0.1:8088'})
        expected_record_4 = MetricRecord('upstreams.responses.5xx', 'guage', 0, self.plugin.instance_id,
            {'upstream.name' : 'hg-backend', 'upstream.peer.name' : '10.0.0.1:8089'})

        expected_records = [expected_record_1, expected_record_2, expected_record_3, expected_record_4]

        self.plugin._emit_upstreams_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_upstreams_fails(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('upstreams.fails', 'guage', 'fails')]
        expected_record_1 = MetricRecord('upstreams.fails', 'guage', 0, self.plugin.instance_id,
            {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.1:8080'})
        expected_record_2 = MetricRecord('upstreams.fails', 'guage', 0, self.plugin.instance_id,
            {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.1:8081'})

        expected_record_3 = MetricRecord('upstreams.fails', 'guage', 0, self.plugin.instance_id,
            {'upstream.name' : 'hg-backend', 'upstream.peer.name' : '10.0.0.1:8088'})
        expected_record_4 = MetricRecord('upstreams.fails', 'guage', 0, self.plugin.instance_id,
            {'upstream.name' : 'hg-backend', 'upstream.peer.name' : '10.0.0.1:8089'})

        expected_records = [expected_record_1, expected_record_2, expected_record_3, expected_record_4]

        self.plugin._emit_upstreams_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_upstreams_unavailable(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('upstreams.unavailable', 'guage', 'unavail')]
        expected_record_1 = MetricRecord('upstreams.unavailable', 'guage', 0, self.plugin.instance_id,
            {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.1:8080'})
        expected_record_2 = MetricRecord('upstreams.unavailable', 'guage', 0, self.plugin.instance_id,
            {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.1:8081'})

        expected_record_3 = MetricRecord('upstreams.unavailable', 'guage', 0, self.plugin.instance_id,
            {'upstream.name' : 'hg-backend', 'upstream.peer.name' : '10.0.0.1:8088'})
        expected_record_4 = MetricRecord('upstreams.unavailable', 'guage', 0, self.plugin.instance_id,
            {'upstream.name' : 'hg-backend', 'upstream.peer.name' : '10.0.0.1:8089'})

        expected_records = [expected_record_1, expected_record_2, expected_record_3, expected_record_4]

        self.plugin._emit_upstreams_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_upstreams_health_check_checks(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('upstreams.health.checks.checks', 'guage', 'health_checks.checks')]
        expected_record_1 = MetricRecord('upstreams.health.checks.checks', 'guage', 38254, self.plugin.instance_id,
            {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.1:8080'})
        expected_record_2 = MetricRecord('upstreams.health.checks.checks', 'guage', 38303, self.plugin.instance_id,
            {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.1:8081'})

        expected_record_3 = MetricRecord('upstreams.health.checks.checks', 'guage', 38199, self.plugin.instance_id,
            {'upstream.name' : 'hg-backend', 'upstream.peer.name' : '10.0.0.1:8088'})
        expected_record_4 = MetricRecord('upstreams.health.checks.checks', 'guage', 38303, self.plugin.instance_id,
            {'upstream.name' : 'hg-backend', 'upstream.peer.name' : '10.0.0.1:8089'})

        expected_records = [expected_record_1, expected_record_2, expected_record_3, expected_record_4]

        self.plugin._emit_upstreams_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_upstreams_health_check_fails(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('upstreams.health.checks.fails', 'guage', 'health_checks.fails')]
        expected_record_1 = MetricRecord('upstreams.health.checks.fails', 'guage', 0, self.plugin.instance_id,
            {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.1:8080'})
        expected_record_2 = MetricRecord('upstreams.health.checks.fails', 'guage', 38303, self.plugin.instance_id,
            {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.1:8081'})

        expected_record_3 = MetricRecord('upstreams.health.checks.fails', 'guage', 0, self.plugin.instance_id,
            {'upstream.name' : 'hg-backend', 'upstream.peer.name' : '10.0.0.1:8088'})
        expected_record_4 = MetricRecord('upstreams.health.checks.fails', 'guage', 38303, self.plugin.instance_id,
            {'upstream.name' : 'hg-backend', 'upstream.peer.name' : '10.0.0.1:8089'})

        expected_records = [expected_record_1, expected_record_2, expected_record_3, expected_record_4]

        self.plugin._emit_upstreams_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_upstreams_health_check_unhealthy(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('upstreams.health.checks.unhealthy', 'guage', 'health_checks.unhealthy')]
        expected_record_1 = MetricRecord('upstreams.health.checks.unhealthy', 'guage', 0, self.plugin.instance_id,
            {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.1:8080'})
        expected_record_2 = MetricRecord('upstreams.health.checks.unhealthy', 'guage', 1, self.plugin.instance_id,
            {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.1:8081'})

        expected_record_3 = MetricRecord('upstreams.health.checks.unhealthy', 'guage', 0, self.plugin.instance_id,
            {'upstream.name' : 'hg-backend', 'upstream.peer.name' : '10.0.0.1:8088'})
        expected_record_4 = MetricRecord('upstreams.health.checks.unhealthy', 'guage', 1, self.plugin.instance_id,
            {'upstream.name' : 'hg-backend', 'upstream.peer.name' : '10.0.0.1:8089'})

        expected_records = [expected_record_1, expected_record_2, expected_record_3, expected_record_4]

        self.plugin._emit_upstreams_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_cache_size(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('caches.size', 'guage', 'size')]
        expected_record = MetricRecord('caches.size', 'guage', 532680704, self.plugin.instance_id, {'cache.name' : 'http_cache'})

        self.plugin._emit_cache_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_cache_size_max(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('caches.size.max', 'guage', 'max_size')]
        expected_record = MetricRecord('caches.size.max', 'guage', 536870912, self.plugin.instance_id, {'cache.name' : 'http_cache'})

        self.plugin._emit_cache_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_cache_hits(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('caches.hits', 'guage', 'hit.responses')]
        expected_record = MetricRecord('caches.hits', 'guage', 921734, self.plugin.instance_id, {'cache.name' : 'http_cache'})

        self.plugin._emit_cache_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_cache_misses(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('caches.misses', 'guage', 'miss.responses')]
        expected_record = MetricRecord('caches.misses', 'guage', 3396487, self.plugin.instance_id, {'cache.name' : 'http_cache'})

        self.plugin._emit_cache_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_stream_server_zone_connections(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('stream.server.zone.connections', 'guage', 'connections')]
        expected_record_1 = MetricRecord('stream.server.zone.connections', 'guage', 382002, self.plugin.instance_id, {'stream.server.zone.name' : 'postgresql_loadbalancer'})
        expected_record_2 = MetricRecord('stream.server.zone.connections', 'guage', 219222, self.plugin.instance_id, {'stream.server.zone.name' : 'dns_loadbalancer'})

        expected_records = [expected_record_1, expected_record_2]

        self.plugin._emit_stream_server_zone_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_stream_server_zone_processing(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('stream.server.zone.processing', 'guage', 'processing')]
        expected_record_1 = MetricRecord('stream.server.zone.processing', 'guage', 0, self.plugin.instance_id, {'stream.server.zone.name' : 'postgresql_loadbalancer'})
        expected_record_2 = MetricRecord('stream.server.zone.processing', 'guage', 0, self.plugin.instance_id, {'stream.server.zone.name' : 'dns_loadbalancer'})

        expected_records = [expected_record_1, expected_record_2]

        self.plugin._emit_stream_server_zone_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_stream_server_zone_session_2xx(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('stream.server.zone.session.2xx', 'guage', 'sessions.2xx')]
        expected_record_1 = MetricRecord('stream.server.zone.session.2xx', 'guage', 382002, self.plugin.instance_id, {'stream.server.zone.name' : 'postgresql_loadbalancer'})
        expected_record_2 = MetricRecord('stream.server.zone.session.2xx', 'guage', 219222, self.plugin.instance_id, {'stream.server.zone.name' : 'dns_loadbalancer'})

        expected_records = [expected_record_1, expected_record_2]

        self.plugin._emit_stream_server_zone_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_stream_server_zone_session_4xx(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('stream.server.zone.session.4xx', 'guage', 'sessions.4xx')]
        expected_record_1 = MetricRecord('stream.server.zone.session.4xx', 'guage', 0, self.plugin.instance_id, {'stream.server.zone.name' : 'postgresql_loadbalancer'})
        expected_record_2 = MetricRecord('stream.server.zone.session.4xx', 'guage', 0, self.plugin.instance_id, {'stream.server.zone.name' : 'dns_loadbalancer'})

        expected_records = [expected_record_1, expected_record_2]

        self.plugin._emit_stream_server_zone_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_stream_server_zone_session_5xx(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('stream.server.zone.session.5xx', 'guage', 'sessions.5xx')]
        expected_record_1 = MetricRecord('stream.server.zone.session.5xx', 'guage', 0, self.plugin.instance_id, {'stream.server.zone.name' : 'postgresql_loadbalancer'})
        expected_record_2 = MetricRecord('stream.server.zone.session.5xx', 'guage', 0, self.plugin.instance_id, {'stream.server.zone.name' : 'dns_loadbalancer'})

        expected_records = [expected_record_1, expected_record_2]

        self.plugin._emit_stream_server_zone_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_stream_upstream_connections(self):
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

    def test_stream_upstream_active(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('stream.upstreams.active', 'guage', 'active')]
        expected_record_1 = MetricRecord('stream.upstreams.active', 'guage', 0, self.plugin.instance_id,
            {'stream.upstream.name' : 'postgresql_backends', 'stream.upstream.peer.name' : '10.0.0.2:15432'})
        expected_record_2 = MetricRecord('stream.upstreams.active', 'guage', 0, self.plugin.instance_id,
            {'stream.upstream.name' : 'postgresql_backends', 'stream.upstream.peer.name' : '10.0.0.2:15433'})

        expected_record_3 = MetricRecord('stream.upstreams.active', 'guage', 0, self.plugin.instance_id,
            {'stream.upstream.name' : 'dns_udp_backends', 'stream.upstream.peer.name' : '10.0.0.5:53'})
        expected_record_4 = MetricRecord('stream.upstreams.active', 'guage', 0, self.plugin.instance_id,
            {'stream.upstream.name' : 'dns_udp_backends', 'stream.upstream.peer.name' : '10.0.0.2:53'})

        expected_records = [expected_record_1, expected_record_2, expected_record_3, expected_record_4]

        self.plugin._emit_stream_upstreams_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_stream_upstream_connections_max(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('stream.upstreams.connections.max', 'guage', 'max_conns')]
        expected_record_1 = MetricRecord('stream.upstreams.connections.max', 'guage', 42, self.plugin.instance_id,
            {'stream.upstream.name' : 'postgresql_backends', 'stream.upstream.peer.name' : '10.0.0.2:15432'})

        expected_records = [expected_record_1]

        self.plugin._emit_stream_upstreams_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_stream_upstream_bytes_sent(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('stream.upstreams.bytes.sent', 'guage', 'sent')]
        expected_record_1 = MetricRecord('stream.upstreams.bytes.sent', 'guage', 107, self.plugin.instance_id,
            {'stream.upstream.name' : 'postgresql_backends', 'stream.upstream.peer.name' : '10.0.0.2:15432'})
        expected_record_2 = MetricRecord('stream.upstreams.bytes.sent', 'guage', 20437107, self.plugin.instance_id,
            {'stream.upstream.name' : 'postgresql_backends', 'stream.upstream.peer.name' : '10.0.0.2:15433'})

        expected_record_3 = MetricRecord('stream.upstreams.bytes.sent', 'guage', 3945996, self.plugin.instance_id,
            {'stream.upstream.name' : 'dns_udp_backends', 'stream.upstream.peer.name' : '10.0.0.5:53'})
        expected_record_4 = MetricRecord('stream.upstreams.bytes.sent', 'guage', 1972998, self.plugin.instance_id,
            {'stream.upstream.name' : 'dns_udp_backends', 'stream.upstream.peer.name' : '10.0.0.2:53'})

        expected_records = [expected_record_1, expected_record_2, expected_record_3, expected_record_4]

        self.plugin._emit_stream_upstreams_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_stream_upstream_bytes_received(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('stream.upstreams.bytes.received', 'guage', 'received')]
        expected_record_1 = MetricRecord('stream.upstreams.bytes.received', 'guage', 13634, self.plugin.instance_id,
            {'stream.upstream.name' : 'postgresql_backends', 'stream.upstream.peer.name' : '10.0.0.2:15432'})
        expected_record_2 = MetricRecord('stream.upstreams.bytes.received', 'guage', 2743118929, self.plugin.instance_id,
            {'stream.upstream.name' : 'postgresql_backends', 'stream.upstream.peer.name' : '10.0.0.2:15433'})

        expected_record_3 = MetricRecord('stream.upstreams.bytes.received', 'guage', 19249800, self.plugin.instance_id,
            {'stream.upstream.name' : 'dns_udp_backends', 'stream.upstream.peer.name' : '10.0.0.5:53'})
        expected_record_4 = MetricRecord('stream.upstreams.bytes.received', 'guage', 9624780, self.plugin.instance_id,
            {'stream.upstream.name' : 'dns_udp_backends', 'stream.upstream.peer.name' : '10.0.0.2:53'})

        expected_records = [expected_record_1, expected_record_2, expected_record_3, expected_record_4]

        self.plugin._emit_stream_upstreams_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_stream_upstream_fails(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('stream.upstreams.fails', 'guage', 'fails')]
        expected_record_1 = MetricRecord('stream.upstreams.fails', 'guage', 0, self.plugin.instance_id,
            {'stream.upstream.name' : 'postgresql_backends', 'stream.upstream.peer.name' : '10.0.0.2:15432'})
        expected_record_2 = MetricRecord('stream.upstreams.fails', 'guage', 0, self.plugin.instance_id,
            {'stream.upstream.name' : 'postgresql_backends', 'stream.upstream.peer.name' : '10.0.0.2:15433'})

        expected_record_3 = MetricRecord('stream.upstreams.fails', 'guage', 0, self.plugin.instance_id,
            {'stream.upstream.name' : 'dns_udp_backends', 'stream.upstream.peer.name' : '10.0.0.5:53'})
        expected_record_4 = MetricRecord('stream.upstreams.fails', 'guage', 0, self.plugin.instance_id,
            {'stream.upstream.name' : 'dns_udp_backends', 'stream.upstream.peer.name' : '10.0.0.2:53'})

        expected_records = [expected_record_1, expected_record_2, expected_record_3, expected_record_4]

        self.plugin._emit_stream_upstreams_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_stream_upstream_unavailable(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('stream.upstreams.unavailable', 'guage', 'unavail')]
        expected_record_1 = MetricRecord('stream.upstreams.unavailable', 'guage', 0, self.plugin.instance_id,
            {'stream.upstream.name' : 'postgresql_backends', 'stream.upstream.peer.name' : '10.0.0.2:15432'})
        expected_record_2 = MetricRecord('stream.upstreams.unavailable', 'guage', 0, self.plugin.instance_id,
            {'stream.upstream.name' : 'postgresql_backends', 'stream.upstream.peer.name' : '10.0.0.2:15433'})

        expected_record_3 = MetricRecord('stream.upstreams.unavailable', 'guage', 0, self.plugin.instance_id,
            {'stream.upstream.name' : 'dns_udp_backends', 'stream.upstream.peer.name' : '10.0.0.5:53'})
        expected_record_4 = MetricRecord('stream.upstreams.unavailable', 'guage', 0, self.plugin.instance_id,
            {'stream.upstream.name' : 'dns_udp_backends', 'stream.upstream.peer.name' : '10.0.0.2:53'})

        expected_records = [expected_record_1, expected_record_2, expected_record_3, expected_record_4]

        self.plugin._emit_stream_upstreams_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_stream_upstream_health_check_checks(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('stream.upstreams.health.checks.checks', 'guage', 'health_checks.checks')]
        expected_record_1 = MetricRecord('stream.upstreams.health.checks.checks', 'guage', 76582, self.plugin.instance_id,
            {'stream.upstream.name' : 'postgresql_backends', 'stream.upstream.peer.name' : '10.0.0.2:15432'})
        expected_record_2 = MetricRecord('stream.upstreams.health.checks.checks', 'guage', 76582, self.plugin.instance_id,
            {'stream.upstream.name' : 'postgresql_backends', 'stream.upstream.peer.name' : '10.0.0.2:15433'})

        expected_record_3 = MetricRecord('stream.upstreams.health.checks.checks', 'guage', 76552, self.plugin.instance_id,
            {'stream.upstream.name' : 'dns_udp_backends', 'stream.upstream.peer.name' : '10.0.0.5:53'})
        expected_record_4 = MetricRecord('stream.upstreams.health.checks.checks', 'guage', 76552, self.plugin.instance_id,
            {'stream.upstream.name' : 'dns_udp_backends', 'stream.upstream.peer.name' : '10.0.0.2:53'})

        expected_records = [expected_record_1, expected_record_2, expected_record_3, expected_record_4]

        self.plugin._emit_stream_upstreams_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_stream_upstream_health_check_fails(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('stream.upstreams.health.checks.fails', 'guage', 'health_checks.fails')]
        expected_record_1 = MetricRecord('stream.upstreams.health.checks.fails', 'guage', 0, self.plugin.instance_id,
            {'stream.upstream.name' : 'postgresql_backends', 'stream.upstream.peer.name' : '10.0.0.2:15432'})
        expected_record_2 = MetricRecord('stream.upstreams.health.checks.fails', 'guage', 0, self.plugin.instance_id,
            {'stream.upstream.name' : 'postgresql_backends', 'stream.upstream.peer.name' : '10.0.0.2:15433'})

        expected_record_3 = MetricRecord('stream.upstreams.health.checks.fails', 'guage', 0, self.plugin.instance_id,
            {'stream.upstream.name' : 'dns_udp_backends', 'stream.upstream.peer.name' : '10.0.0.5:53'})
        expected_record_4 = MetricRecord('stream.upstreams.health.checks.fails', 'guage', 0, self.plugin.instance_id,
            {'stream.upstream.name' : 'dns_udp_backends', 'stream.upstream.peer.name' : '10.0.0.2:53'})

        expected_records = [expected_record_1, expected_record_2, expected_record_3, expected_record_4]

        self.plugin._emit_stream_upstreams_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_stream_upstream_health_check_unhealthy(self):
        status_json = self._read_test_resource_json('resources/status_response.json')

        metrics = [MetricDefinition('stream.upstreams.health.checks.unhealthy', 'guage', 'health_checks.unhealthy')]
        expected_record_1 = MetricRecord('stream.upstreams.health.checks.unhealthy', 'guage', 0, self.plugin.instance_id,
            {'stream.upstream.name' : 'postgresql_backends', 'stream.upstream.peer.name' : '10.0.0.2:15432'})
        expected_record_2 = MetricRecord('stream.upstreams.health.checks.unhealthy', 'guage', 0, self.plugin.instance_id,
            {'stream.upstream.name' : 'postgresql_backends', 'stream.upstream.peer.name' : '10.0.0.2:15433'})

        expected_record_3 = MetricRecord('stream.upstreams.health.checks.unhealthy', 'guage', 0, self.plugin.instance_id,
            {'stream.upstream.name' : 'dns_udp_backends', 'stream.upstream.peer.name' : '10.0.0.5:53'})
        expected_record_4 = MetricRecord('stream.upstreams.health.checks.unhealthy', 'guage', 0, self.plugin.instance_id,
            {'stream.upstream.name' : 'dns_udp_backends', 'stream.upstream.peer.name' : '10.0.0.2:53'})

        expected_records = [expected_record_1, expected_record_2, expected_record_3, expected_record_4]

        self.plugin._emit_stream_upstreams_metrics(status_json, metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def _random_string(self, length=8):
        return ''.join(random.choice(string.lowercase) for i in range(length))

    def _random_int(self, start=0, stop=100000):
        return random.randint(start, stop)

    def _extract_metric_names_from_definitions(self, metric_defs):
        return [metric_def.name for metric_def in metric_defs]

    def _extract_metic_names_from_emitter(self, emitter):
        return self._extract_metric_names_from_definitions(emitter.metrics)

    def _get_default_metric_names(self):
        metric_names = self._extract_metric_names_from_definitions(DEFAULT_CONNECTION_METRICS)
        metric_names.extend(self._extract_metric_names_from_definitions(DEFAULT_SERVER_ZONE_METRICS))
        metric_names.extend(self._extract_metric_names_from_definitions(DEFAULT_UPSTREAM_METRICS))
        metric_names.extend(self._extract_metric_names_from_definitions(DEFAULT_STREAM_SERVER_ZONE_METRICS))
        metric_names.extend(self._extract_metric_names_from_definitions(DEFAULT_STREAM_UPSTREAM_METRICS))

        return metric_names

    def _get_metrics_names_from_plugin(self):
        metric_names = []
        for emitter in self.plugin.emitters:
            metric_names.extend(self._extract_metic_names_from_emitter(emitter))
        return metric_names

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
