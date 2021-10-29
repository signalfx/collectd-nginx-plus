#!/usr/bin/env python
import os
import sys
import string
import json
import random
from unittest import TestCase
from mock import Mock, MagicMock, patch

# Mock out the collectd module
sys.modules['collectd'] = Mock()

from plugin.nginx_plus_collectd import NginxPlusPlugin, MetricRecord, MetricDefinition,\
                                        DEFAULT_CONNECTION_METRICS, DEFAULT_SERVER_ZONE_METRICS,\
                                        DEFAULT_UPSTREAM_METRICS, SERVER_ZONE_METRICS, SERVER_ZONE,\
                                        MEMORY_ZONE_METRICS, MEMORY_ZONE, UPSTREAM_PEER_METRICS, UPSTREAM,\
                                        CACHE_METRICS, CACHE, STREAM_SERVER_ZONE_METRICS, STREAM_SERVER_ZONE,\
                                        STREAM_UPSTREAM_PEER_METRICS, STREAM_UPSTREAM, STATUS_HOST, STATUS_PORT,\
                                        DEFAULT_SSL_METRICS, DEFAULT_REQUESTS_METRICS, DEBUG_LOG_LEVEL, log_handler,\
                                        USERNAME, PASSWORD, DIMENSION, DIMENSIONS, DEFAULT_CACHE_METRICS,\
                                        PROCESSES_METRICS, PROCESSES, UPSTREAM_METRICS, STREAM_UPSTREAM_METRICS


class NginxCollectdTest(TestCase):
    def setUp(self):
        self.plugin = NginxPlusPlugin()
        self.plugin._instance_id = self._random_string()
        self.mock_sink = MockMetricSink()
        self.plugin.nginx_agent = self._build_mock_nginx_agent()

        self.plugin._reload_ephemeral_global_dimensions()

    def test_instance_id_set(self):
        self.plugin.nginx_agent.status_port = self._random_int()
        expected_instance_id = '18.193.151.235:' + str(self.plugin.nginx_agent.status_port)

        self.plugin._instance_id = None

        actual_instance_id = self.plugin.instance_id
        self.assertEquals(expected_instance_id, actual_instance_id)

    def test_no_emit_invalid_path(self):
        metrics = [MetricDefinition('connection.accepted', 'counter', 'foo.bar')]
        self.plugin._emit_connection_metrics(metrics, self.mock_sink)

        self.assertEquals(0, len(self.mock_sink.captured_records))

    @patch('requests.get')
    def test_configure_only_defaults_emitters(self, mock_requests_get):
        mock_requests_get.side_effect = self._mocked_requests_get

        expected_metric_names = self._get_default_metric_names()

        mock_config = Mock()
        mock_config.children = {}

        self.plugin.configure(mock_config)
        actual_metric_names = self._get_metrics_names_from_plugin()

        self.assertEquals(len(expected_metric_names), len(actual_metric_names))
        self.assertItemsEqual(expected_metric_names, actual_metric_names)

    @patch('requests.get')
    def test_configure_server_zone_emitters(self, mock_requests_get):
        mock_requests_get.side_effect = self._mocked_requests_get

        expected_metric_names = self._get_default_metric_names()
        expected_metric_names.extend(self._extract_metric_names_from_definitions(SERVER_ZONE_METRICS))

        mock_config = Mock()
        mock_config_child = Mock()
        mock_config_child.key = SERVER_ZONE
        mock_config_child.values = ['true']

        mock_config.children = [mock_config_child]

        self.plugin.configure(mock_config)
        actual_metric_names = self._get_metrics_names_from_plugin()

        self.assertEquals(len(expected_metric_names), len(actual_metric_names))
        self.assertItemsEqual(expected_metric_names, actual_metric_names)

    @patch('requests.get')
    def test_configure_memory_zone_emitters(self, mock_requests_get):
        mock_requests_get.side_effect = self._mocked_requests_get

        expected_metric_names = self._get_default_metric_names()
        expected_metric_names.extend(self._extract_metric_names_from_definitions(MEMORY_ZONE_METRICS))

        mock_config = Mock()
        mock_config_child = Mock()
        mock_config_child.key = MEMORY_ZONE
        mock_config_child.values = ['true']

        mock_config.children = [mock_config_child]

        self.plugin.configure(mock_config)
        actual_metric_names = self._get_metrics_names_from_plugin()

        self.assertEquals(len(expected_metric_names), len(actual_metric_names))
        self.assertItemsEqual(expected_metric_names, actual_metric_names)

    @patch('requests.get')
    def test_configure_upstream_emitters(self, mock_requests_get):
        mock_requests_get.side_effect = self._mocked_requests_get

        expected_metric_names = self._get_default_metric_names()
        expected_metric_names.extend(self._extract_metric_names_from_definitions(UPSTREAM_METRICS))
        expected_metric_names.extend(self._extract_metric_names_from_definitions(UPSTREAM_PEER_METRICS))

        mock_config = Mock()
        mock_config_child = Mock()
        mock_config_child.key = UPSTREAM
        mock_config_child.values = ['true']

        mock_config.children = [mock_config_child]

        self.plugin.configure(mock_config)
        actual_metric_names = self._get_metrics_names_from_plugin()

        self.assertEquals(len(expected_metric_names), len(actual_metric_names))
        self.assertItemsEqual(expected_metric_names, actual_metric_names)

    @patch('requests.get')
    def test_configure_cache_emitters(self, mock_requests_get):
        mock_requests_get.side_effect = self._mocked_requests_get

        expected_metric_names = self._get_default_metric_names()
        expected_metric_names.extend(self._extract_metric_names_from_definitions(CACHE_METRICS))

        mock_config = Mock()
        mock_config_child = Mock()
        mock_config_child.key = CACHE
        mock_config_child.values = ['true']

        mock_config.children = [mock_config_child]

        self.plugin.configure(mock_config)
        actual_metric_names = self._get_metrics_names_from_plugin()

        self.assertEquals(len(expected_metric_names), len(actual_metric_names))
        self.assertItemsEqual(expected_metric_names, actual_metric_names)

    @patch('requests.get')
    def test_configure_stream_server_zone_emitters(self, mock_requests_get):
        mock_requests_get.side_effect = self._mocked_requests_get

        expected_metric_names = self._get_default_metric_names()
        expected_metric_names.extend(self._extract_metric_names_from_definitions(STREAM_SERVER_ZONE_METRICS))

        mock_config = Mock()
        mock_config_child = Mock()
        mock_config_child.key = STREAM_SERVER_ZONE
        mock_config_child.values = ['true']

        mock_config.children = [mock_config_child]

        self.plugin.configure(mock_config)
        actual_metric_names = self._get_metrics_names_from_plugin()

        self.assertEquals(len(expected_metric_names), len(actual_metric_names))
        self.assertItemsEqual(expected_metric_names, actual_metric_names)

    @patch('requests.get')
    def test_configure_stream_upstream_emitters(self, mock_requests_get):
        mock_requests_get.side_effect = self._mocked_requests_get

        expected_metric_names = self._get_default_metric_names()
        expected_metric_names.extend(self._extract_metric_names_from_definitions(STREAM_UPSTREAM_METRICS))
        expected_metric_names.extend(self._extract_metric_names_from_definitions(STREAM_UPSTREAM_PEER_METRICS))

        mock_config = Mock()
        mock_config_child = Mock()
        mock_config_child.key = STREAM_UPSTREAM
        mock_config_child.values = ['true']

        mock_config.children = [mock_config_child]

        self.plugin.configure(mock_config)
        actual_metric_names = self._get_metrics_names_from_plugin()

        self.assertEquals(len(expected_metric_names), len(actual_metric_names))
        self.assertItemsEqual(expected_metric_names, actual_metric_names)

    @patch('requests.get')
    def test_configure_processes_emitters(self, mock_requests_get):
        mock_requests_get.side_effect = self._mocked_requests_get

        expected_metric_names = self._get_default_metric_names()
        expected_metric_names.extend(self._extract_metric_names_from_definitions(PROCESSES_METRICS))

        mock_config = Mock()
        mock_config_child = Mock()
        mock_config_child.key = PROCESSES
        mock_config_child.values = ['true']

        mock_config.children = [mock_config_child]

        self.plugin.configure(mock_config)
        actual_metric_names = self._get_metrics_names_from_plugin()

        self.assertEquals(len(expected_metric_names), len(actual_metric_names))
        self.assertItemsEqual(expected_metric_names, actual_metric_names)

    @patch('requests.get')
    def test_configure_status_host_port(self, mock_requests_get):
        mock_requests_get.side_effect = self._mocked_requests_get

        expected_ip = '192.168.0.24'
        expected_port = '411'

        mock_config_ip_child = Mock()
        mock_config_ip_child.key = STATUS_HOST
        mock_config_ip_child.values = [expected_ip]

        mock_config_port_child = Mock()
        mock_config_port_child.key = STATUS_PORT
        mock_config_port_child.values = [expected_port]

        mock_config = Mock()
        mock_config.children = [mock_config_ip_child, mock_config_port_child]

        self.plugin.configure(mock_config)

        self.assertEquals(expected_ip, self.plugin.nginx_agent.status_host)
        self.assertEquals(expected_port, self.plugin.nginx_agent.status_port)

    @patch('requests.get')
    def test_configure_debug_logging(self, mock_requests_get):
        mock_requests_get.side_effect = self._mocked_requests_get

        mock_config = Mock()
        mock_config_child = Mock()
        mock_config_child.key = DEBUG_LOG_LEVEL
        mock_config_child.values = ['true']

        mock_config.children = [mock_config_child]

        self.plugin.configure(mock_config)
        self.assertTrue(log_handler.debug)

    @patch('requests.get')
    def test_configure_username_password(self, mock_requests_get):
        mock_requests_get.side_effect = self._mocked_requests_get

        expected_username = self._random_string()
        expected_password = self._random_string()
        expected_auth_tuple = (expected_username, expected_password)

        mock_config_child_1 = Mock()
        mock_config_child_1.key = USERNAME
        mock_config_child_1.values = [expected_username]

        mock_config_child_2 = Mock()
        mock_config_child_2.key = PASSWORD
        mock_config_child_2.values = [expected_password]

        mock_config = Mock()
        mock_config.children = [mock_config_child_1, mock_config_child_2]

        self.plugin.configure(mock_config)
        self.assertEquals(expected_auth_tuple, self.plugin.nginx_agent.auth_tuple)

    @patch('requests.get')
    def test_configure_additional_dimensions(self, mock_requests_get):
        mock_requests_get.side_effect = self._mocked_requests_get

        self.plugin.global_dimensions = {} # Reset the global dimensions

        expected_dim_key_1 = self._random_string()
        expected_dim_value_1 = self._random_string()

        expected_dim_key_2 = self._random_string()
        expected_dim_value_2 = self._random_string()

        expected_global_dimensions = {expected_dim_key_1 : expected_dim_value_1,
                                      expected_dim_key_2 : expected_dim_value_2}

        mock_config_child_1 = Mock()
        mock_config_child_1.key = DIMENSION
        mock_config_child_1.values = [expected_dim_key_1, expected_dim_value_1]

        mock_config_child_2 = Mock()
        mock_config_child_2.key = DIMENSION
        mock_config_child_2.values = [expected_dim_key_2, expected_dim_value_2]

        mock_config = Mock()
        mock_config.children = [mock_config_child_1, mock_config_child_2]

        self.plugin.configure(mock_config)
        self.assertDictEqual(expected_global_dimensions, self.plugin.global_dimensions)

    @patch('requests.get')
    def test_configure_additional_dimensions_missing_value(self, mock_requests_get):
        mock_requests_get.side_effect = self._mocked_requests_get

        self.plugin.global_dimensions = {} # Reset the global dimensions

        expected_dim_key = self._random_string()
        expected_dim_value = self._random_string()

        missing_dim_key = self._random_string()

        expected_global_dimensions = {expected_dim_key : expected_dim_value}

        mock_config_child_1 = Mock()
        mock_config_child_1.key = DIMENSION
        mock_config_child_1.values = [expected_dim_key, expected_dim_value]

        mock_config_child_2 = Mock()
        mock_config_child_2.key = DIMENSION
        mock_config_child_2.values = [missing_dim_key]

        mock_config = Mock()
        mock_config.children = [mock_config_child_1, mock_config_child_2]

        self.plugin.configure(mock_config)
        self.assertDictEqual(expected_global_dimensions, self.plugin.global_dimensions)

    @patch('requests.get')
    def test_configure_neo_agent_dimension_str(self, mock_requests_get):
        mock_requests_get.side_effect = self._mocked_requests_get

        self.plugin.global_dimensions = {} # Reset the global dimensions

        expected_dim_key = self._random_string()
        expected_dim_value = self._random_string()

        expected_global_dimensions = {expected_dim_key : expected_dim_value}
        dimensions_str = '{}={}'.format(expected_dim_key, expected_dim_value)

        mock_config_child = Mock()
        mock_config_child.key = DIMENSIONS
        mock_config_child.values = [dimensions_str]

        mock_config = Mock()
        mock_config.children = [mock_config_child]

        self.plugin.configure(mock_config)
        self.assertDictEqual(expected_global_dimensions, self.plugin.global_dimensions)

    @patch('requests.get')
    def test_configure_neo_agent_dimension_str_malformed(self, mock_requests_get):
        mock_requests_get.side_effect = self._mocked_requests_get

        self.plugin.global_dimensions = {} # Reset the global dimensions

        expected_dim_key = self._random_string()
        expected_dim_value = self._random_string()
        missing_dim_key = self._random_string()

        expected_global_dimensions = {expected_dim_key : expected_dim_value}
        dimensions_str = '{}={},{}'.format(expected_dim_key, expected_dim_value, missing_dim_key)

        mock_config_child = Mock()
        mock_config_child.key = DIMENSIONS
        mock_config_child.values = [dimensions_str]

        mock_config = Mock()
        mock_config.children = [mock_config_child]

        self.plugin.configure(mock_config)
        self.assertDictEqual(expected_global_dimensions, self.plugin.global_dimensions)

    def test_read(self):
        mock_emitter_1 = Mock()
        mock_emitter_2 = Mock()
        mock_sink = Mock()

        self.plugin.sink = mock_sink
        self.plugin.emitters = [mock_emitter_1, mock_emitter_2]

        self.plugin.read()

        mock_emitter_1.emit.assert_called_with(mock_sink)
        mock_emitter_2.emit.assert_called_with(mock_sink)

    def test_read_null_instance_id(self):
        mock_nginx_agent = Mock()
        mock_nginx_agent.get_nginx_address = MagicMock(return_value=None)

        mock_emitter_1 = Mock()
        mock_emitter_2 = Mock()

        mock_sink = Mock()

        self.plugin.sink = mock_sink
        self.plugin.nginx_agent = mock_nginx_agent
        self.plugin.emitters = [mock_emitter_1, mock_emitter_2]

        self.plugin.read()

        mock_emitter_1.assert_not_called()
        mock_emitter_2.assert_not_called()

    def test_connections_accepted(self):
        metrics = [MetricDefinition('connections.accepted', 'counter', 'accepted')]
        expected_record = MetricRecord('connections.accepted', 'counter', 18717986, self.plugin.instance_id,
                                       {'nginx.version' : '1.21.3'})

        self.plugin._emit_connection_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_connections_dropped(self):
        metrics = [MetricDefinition('connections.dropped', 'counter', 'dropped')]
        expected_record = MetricRecord('connections.dropped', 'counter', 0, self.plugin.instance_id,
                                       {'nginx.version' : '1.21.3'})

        self.plugin._emit_connection_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_connections_idle(self):
        metrics = [MetricDefinition('connections.idle', 'counter', 'idle')]
        expected_record = MetricRecord('connections.idle', 'counter', 44, self.plugin.instance_id,
                                       {'nginx.version' : '1.21.3'})

        self.plugin._emit_connection_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_ssl_successful(self):
        metrics = [MetricDefinition('ssl.handshakes.successful', 'counter', 'handshakes')]
        expected_record = MetricRecord('ssl.handshakes.successful', 'counter', 172619, self.plugin.instance_id,
                                       {'nginx.version' : '1.21.3'})

        self.plugin._emit_ssl_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_ssl_failed(self):
        metrics = [MetricDefinition('ssl.handshakes.failed', 'counter', 'handshakes_failed')]
        expected_record = MetricRecord('ssl.handshakes.failed', 'counter', 32483, self.plugin.instance_id,
                                       {'nginx.version' : '1.21.3'})

        self.plugin._emit_ssl_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_ssl_session_reuses(self):
        metrics = [MetricDefinition('ssl.sessions.reuses', 'counter', 'session_reuses')]
        expected_record = MetricRecord('ssl.sessions.reuses', 'counter', 26952, self.plugin.instance_id,
                                       {'nginx.version' : '1.21.3'})

        self.plugin._emit_ssl_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_requests_total(self):
        metrics = [MetricDefinition('requests.total', 'counter', 'total')]
        expected_record = MetricRecord('requests.total', 'counter', 56371877, self.plugin.instance_id,
                                       {'nginx.version' : '1.21.3'})

        self.plugin._emit_requests_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_requests_current(self):
        metrics = [MetricDefinition('requests.current', 'gauge', 'current')]
        expected_record = MetricRecord('requests.current', 'gauge', 6, self.plugin.instance_id,
                                       {'nginx.version' : '1.21.3'})

        self.plugin._emit_requests_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_server_zone_requests(self):
        metrics = [MetricDefinition('server.zone.requests', 'counter', 'requests')]
        expected_record = MetricRecord('server.zone.requests', 'counter', 64475, self.plugin.instance_id,
                                        {'server.zone.name' : 'hg.nginx.org', 'nginx.version' : '1.21.3'})

        self.plugin._emit_server_zone_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_server_zone_processing(self):
        metrics = [MetricDefinition('server.zone.processing', 'counter', 'processing')]
        expected_record = MetricRecord('server.zone.processing', 'counter', 0, self.plugin.instance_id,
                                         {'server.zone.name' : 'hg.nginx.org', 'nginx.version' : '1.21.3'})

        self.plugin._emit_server_zone_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_server_zone_discarded(self):
        metrics = [MetricDefinition('server.zone.discarded', 'counter', 'discarded')]
        expected_record = MetricRecord('server.zone.discarded', 'counter', 0, self.plugin.instance_id,
                                         {'server.zone.name' : 'hg.nginx.org', 'nginx.version' : '1.21.3'})

        self.plugin._emit_server_zone_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_server_zone_responses_total(self):
        metrics = [MetricDefinition('server.zone.responses.total', 'counter', 'responses.total')]
        expected_record = MetricRecord('server.zone.responses.total', 'counter', 64475, self.plugin.instance_id,
                                         {'server.zone.name' : 'hg.nginx.org', 'nginx.version' : '1.21.3'})

        self.plugin._emit_server_zone_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_server_zone_responses_1xx(self):
        metrics = [MetricDefinition('server.zone.responses.1xx', 'counter', 'responses.1xx')]
        expected_record = MetricRecord('server.zone.responses.1xx', 'counter', 0, self.plugin.instance_id,
                                         {'server.zone.name' : 'hg.nginx.org', 'nginx.version' : '1.21.3'})

        self.plugin._emit_server_zone_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_server_zone_responses_2xx(self):
        metrics = [MetricDefinition('server.zone.responses.2xx', 'counter', 'responses.2xx')]
        expected_record = MetricRecord('server.zone.responses.2xx', 'counter', 63239, self.plugin.instance_id,
                                         {'server.zone.name' : 'hg.nginx.org', 'nginx.version' : '1.21.3'})

        self.plugin._emit_server_zone_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_server_zone_responses_3xx(self):
        metrics = [MetricDefinition('server.zone.responses.3xx', 'counter', 'responses.3xx')]
        expected_record = MetricRecord('server.zone.responses.3xx', 'counter', 883, self.plugin.instance_id,
                                         {'server.zone.name' : 'hg.nginx.org', 'nginx.version' : '1.21.3'})

        self.plugin._emit_server_zone_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_server_zone_responses_4xx(self):
        metrics = [MetricDefinition('server.zone.responses.4xx', 'counter', 'responses.4xx')]
        expected_record = MetricRecord('server.zone.responses.4xx', 'counter', 353, self.plugin.instance_id,
                                         {'server.zone.name' : 'hg.nginx.org', 'nginx.version' : '1.21.3'})

        self.plugin._emit_server_zone_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_server_zone_responses_5xx(self):
        metrics = [MetricDefinition('server.zone.responses.5xx', 'counter', 'responses.5xx')]
        expected_record = MetricRecord('server.zone.responses.5xx', 'counter', 0, self.plugin.instance_id,
                                         {'server.zone.name' : 'hg.nginx.org', 'nginx.version' : '1.21.3'})

        self.plugin._emit_server_zone_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_server_zone_bytes_received(self):
        metrics = [MetricDefinition('server.zone.bytes.received', 'counter', 'received')]
        expected_record = MetricRecord('server.zone.bytes.received', 'counter', 34641169, self.plugin.instance_id,
                                         {'server.zone.name' : 'hg.nginx.org', 'nginx.version' : '1.21.3'})

        self.plugin._emit_server_zone_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_server_zone_bytes_sent(self):
        metrics = [MetricDefinition('server.zone.bytes.sent', 'counter', 'sent')]
        expected_record = MetricRecord('server.zone.bytes.sent', 'counter', 8187139290, self.plugin.instance_id,
                                         {'server.zone.name' : 'hg.nginx.org', 'nginx.version' : '1.21.3'})

        self.plugin._emit_server_zone_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_memory_zone_pages_used(self):
        metrics = [MetricDefinition('zones.pages.used', 'counter', 'pages.used')]
        expected_record = MetricRecord('zones.pages.used', 'counter', 6, self.plugin.instance_id,
                                       {'memory.zone.name' : 'nginxorg', 'nginx.version' : '1.21.3'})

        self.plugin._emit_memory_zone_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_memory_zone_pages_free(self):
        metrics = [MetricDefinition('zones.pages.free', 'counter', 'pages.free')]
        expected_record = MetricRecord('zones.pages.free', 'counter', 9, self.plugin.instance_id,
                                       {'memory.zone.name' : 'nginxorg', 'nginx.version' : '1.21.3'})

        self.plugin._emit_memory_zone_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_upstreams_requests(self):
        metrics = [MetricDefinition('upstream.requests', 'counter', 'requests')]
        expected_record = MetricRecord('upstream.requests', 'counter', 124446, self.plugin.instance_id,
                                         {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.10:8080',
                                          'nginx.version' : '1.21.3'})

        self.plugin._emit_upstreams_peer_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_upstreams_active(self):
        metrics = [MetricDefinition('upstreams.active', 'counter', 'active')]
        expected_record = MetricRecord('upstreams.active', 'counter', 0, self.plugin.instance_id,
                                         {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.10:8080',
                                          'nginx.version' : '1.21.3'})

        self.plugin._emit_upstreams_peer_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_upstreams_responses_total(self):
        metrics = [MetricDefinition('upstreams.responses.total', 'counter', 'responses.total')]
        expected_record = MetricRecord('upstreams.responses.total', 'counter', 124445, self.plugin.instance_id,
                                         {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.10:8080',
                                          'nginx.version' : '1.21.3'})

        self.plugin._emit_upstreams_peer_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_upstreams_responses_1xx(self):
        metrics = [MetricDefinition('upstreams.responses.1xx', 'counter', 'responses.1xx')]
        expected_record = MetricRecord('upstreams.responses.1xx', 'counter', 0, self.plugin.instance_id,
                                         {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.10:8080',
                                          'nginx.version' : '1.21.3'})

        self.plugin._emit_upstreams_peer_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_upstreams_responses_2xx(self):
        metrics = [MetricDefinition('upstreams.responses.2xx', 'counter', 'responses.2xx')]
        expected_record = MetricRecord('upstreams.responses.2xx', 'counter', 122295, self.plugin.instance_id,
                                         {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.10:8080',
                                          'nginx.version' : '1.21.3'})

        self.plugin._emit_upstreams_peer_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_upstreams_responses_3xx(self):
        metrics = [MetricDefinition('upstreams.responses.3xx', 'counter', 'responses.3xx')]
        expected_record = MetricRecord('upstreams.responses.3xx', 'counter', 2017, self.plugin.instance_id,
                                         {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.10:8080',
                                          'nginx.version' : '1.21.3'})

        self.plugin._emit_upstreams_peer_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_upstreams_responses_4xx(self):
        metrics = [MetricDefinition('upstreams.responses.4xx', 'counter', 'responses.4xx')]
        expected_record = MetricRecord('upstreams.responses.4xx', 'counter', 133, self.plugin.instance_id,
                                         {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.10:8080',
                                          'nginx.version' : '1.21.3'})

        self.plugin._emit_upstreams_peer_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_upstreams_responses_5xx(self):
        metrics = [MetricDefinition('upstreams.responses.5xx', 'counter', 'responses.5xx')]
        expected_record = MetricRecord('upstreams.responses.5xx', 'counter', 0, self.plugin.instance_id,
                                         {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.10:8080',
                                          'nginx.version' : '1.21.3'})

        self.plugin._emit_upstreams_peer_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_upstreams_fails(self):
        metrics = [MetricDefinition('upstreams.fails', 'counter', 'fails')]
        expected_record = MetricRecord('upstreams.fails', 'counter', 0, self.plugin.instance_id,
                                         {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.10:8080',
                                          'nginx.version' : '1.21.3'})

        self.plugin._emit_upstreams_peer_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_upstreams_unavailable(self):
        metrics = [MetricDefinition('upstreams.unavailable', 'counter', 'unavail')]
        expected_record = MetricRecord('upstreams.unavailable', 'counter', 0, self.plugin.instance_id,
                                         {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.10:8080',
                                          'nginx.version' : '1.21.3'})

        self.plugin._emit_upstreams_peer_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_upstreams_health_check_checks(self):
        metrics = [MetricDefinition('upstreams.health.checks.checks', 'counter', 'health_checks.checks')]
        expected_record = MetricRecord('upstreams.health.checks.checks', 'counter', 0, self.plugin.instance_id,
                                         {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.10:8080',
                                          'nginx.version' : '1.21.3'})

        self.plugin._emit_upstreams_peer_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_upstreams_health_check_fails(self):
        metrics = [MetricDefinition('upstreams.health.checks.fails', 'counter', 'health_checks.fails')]
        expected_record = MetricRecord('upstreams.health.checks.fails', 'counter', 0, self.plugin.instance_id,
                                         {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.10:8080',
                                          'nginx.version' : '1.21.3'})

        self.plugin._emit_upstreams_peer_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_upstreams_health_check_unhealthy(self):
        metrics = [MetricDefinition('upstreams.health.checks.unhealthy', 'counter', 'health_checks.unhealthy')]
        expected_record = MetricRecord('upstreams.health.checks.unhealthy', 'counter', 0, self.plugin.instance_id,
                                         {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.10:8080',
                                          'nginx.version' : '1.21.3'})

        self.plugin._emit_upstreams_peer_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])


    def test_upstreams_response_time(self):
        metrics = [MetricDefinition('upstreams.response.time', 'gauge', 'response_time')]
        expected_record = MetricRecord('upstreams.response.time', 'gauge', 10, self.plugin.instance_id,
                                         {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.10:8080',
                                          'nginx.version' : '1.21.3'})



        self.plugin._emit_upstreams_peer_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_upstreams_header_time(self):
        metrics = [MetricDefinition('upstreams.header.time', 'gauge', 'header_time')]
        expected_record = MetricRecord('upstreams.header.time', 'gauge', 10, self.plugin.instance_id,
                                         {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.10:8080',
                                          'nginx.version' : '1.21.3'})



        self.plugin._emit_upstreams_peer_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_upstreams_downtime(self):
        metrics = [MetricDefinition('upstreams.downtime', 'counter', 'downtime')]
        expected_record = MetricRecord('upstreams.downtime', 'counter', 0, self.plugin.instance_id,
                                         {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.10:8080',
                                          'nginx.version' : '1.21.3'})

        self.plugin._emit_upstreams_peer_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_upstreams_bytes_received(self):
        metrics = [MetricDefinition('upstreams.bytes.received', 'counter', 'received')]
        expected_record = MetricRecord('upstreams.bytes.received', 'counter', 14253868039, self.plugin.instance_id,
                                         {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.10:8080',
                                          'nginx.version' : '1.21.3'})

        self.plugin._emit_upstreams_peer_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_upstreams_bytes_sent(self):
        metrics = [MetricDefinition('upstreams.bytes.sent', 'counter', 'sent')]
        expected_record = MetricRecord('upstreams.bytes.sent', 'counter', 56541432, self.plugin.instance_id,
                                         {'upstream.name' : 'trac-backend', 'upstream.peer.name' : '10.0.0.10:8080',
                                          'nginx.version' : '1.21.3'})

        self.plugin._emit_upstreams_peer_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_upstreams_keepalive(self):
        metrics = [MetricDefinition('upstreams.keepalive', 'gauge', 'keepalive')]
        expected_record = MetricRecord('upstreams.keepalive', 'gauge', 0, self.plugin.instance_id,
                                         {'upstream.name' : 'trac-backend', 'nginx.version' : '1.21.3'})

        self.plugin._emit_upstreams_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_upstreams_zombies(self):
        metrics = [MetricDefinition('upstreams.zombies', 'gauge', 'zombies')]
        expected_record = MetricRecord('upstreams.zombies', 'gauge', 0, self.plugin.instance_id,
                                         {'upstream.name' : 'trac-backend', 'nginx.version' : '1.21.3'})

        self.plugin._emit_upstreams_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_cache_size(self):
        metrics = [MetricDefinition('caches.size', 'gauge', 'size')]
        expected_record = MetricRecord('caches.size', 'gauge', 19005440, self.plugin.instance_id,
                                       {'cache.name' : 'http_cache', 'nginx.version' : '1.21.3'})

        self.plugin._emit_cache_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_cache_size_max(self):
        metrics = [MetricDefinition('caches.size.max', 'gauge', 'max_size')]
        expected_record = MetricRecord('caches.size.max', 'gauge', 536870912, self.plugin.instance_id,
                                       {'cache.name' : 'http_cache', 'nginx.version' : '1.21.3'})

        self.plugin._emit_cache_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_cache_hits_responses(self):
        metrics = [MetricDefinition('caches.hit.responses', 'counter', 'hit.responses')]
        expected_record = MetricRecord('caches.hit.responses', 'counter', 284813, self.plugin.instance_id,
                                       {'cache.name' : 'http_cache', 'nginx.version' : '1.21.3'})

        self.plugin._emit_cache_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_cache_misses_responses(self):
        metrics = [MetricDefinition('caches.miss.responses', 'counter', 'miss.responses')]
        expected_record = MetricRecord('caches.miss.responses', 'counter', 1304, self.plugin.instance_id,
                                       {'cache.name' : 'http_cache', 'nginx.version' : '1.21.3'})

        self.plugin._emit_cache_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_cache_stale_responses(self):
        metrics = [MetricDefinition('caches.stale.responses', 'counter', 'stale.responses')]
        expected_record = MetricRecord('caches.stale.responses', 'counter', 0, self.plugin.instance_id,
                                       {'cache.name' : 'http_cache', 'nginx.version' : '1.21.3'})

        self.plugin._emit_cache_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_cache_revalidated_responses(self):
        metrics = [MetricDefinition('caches.revalidated.responses', 'counter', 'revalidated.responses')]
        expected_record = MetricRecord('caches.revalidated.responses', 'counter', 0, self.plugin.instance_id,
                                       {'cache.name' : 'http_cache', 'nginx.version' : '1.21.3'})

        self.plugin._emit_cache_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_cache_expired_responses(self):
        metrics = [MetricDefinition('caches.expired.responses', 'counter', 'expired.responses')]
        expected_record = MetricRecord('caches.expired.responses', 'counter', 4058, self.plugin.instance_id,
                                       {'cache.name' : 'http_cache', 'nginx.version' : '1.21.3'})

        self.plugin._emit_cache_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_cache_bypass_responses(self):
        metrics = [MetricDefinition('caches.bypass.responses', 'counter', 'bypass.responses')]
        expected_record = MetricRecord('caches.bypass.responses', 'counter', 0, self.plugin.instance_id,
                                       {'cache.name' : 'http_cache', 'nginx.version' : '1.21.3'})

        self.plugin._emit_cache_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_cache_updating_responses(self):
        metrics = [MetricDefinition('caches.updating.responses', 'counter', 'updating.responses')]
        expected_record = MetricRecord('caches.updating.responses', 'counter', 0, self.plugin.instance_id,
                                       {'cache.name' : 'http_cache', 'nginx.version' : '1.21.3'})

        self.plugin._emit_cache_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_cache_hits_bytes(self):
        metrics = [MetricDefinition('caches.hit.bytes', 'counter', 'hit.bytes')]
        expected_record = MetricRecord('caches.hit.bytes', 'counter', 36874385656, self.plugin.instance_id,
                                       {'cache.name' : 'http_cache', 'nginx.version' : '1.21.3'})

        self.plugin._emit_cache_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_cache_misses_bytes(self):
        metrics = [MetricDefinition('caches.miss.bytes', 'counter', 'miss.bytes')]
        expected_record = MetricRecord('caches.miss.bytes', 'counter', 160222600, self.plugin.instance_id,
                                       {'cache.name' : 'http_cache', 'nginx.version' : '1.21.3'})

        self.plugin._emit_cache_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_cache_stale_bytes(self):
        metrics = [MetricDefinition('caches.stale.bytes', 'counter', 'stale.bytes')]
        expected_record = MetricRecord('caches.stale.bytes', 'counter', 0, self.plugin.instance_id,
                                       {'cache.name' : 'http_cache', 'nginx.version' : '1.21.3'})

        self.plugin._emit_cache_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_cache_revalidated_bytes(self):
        metrics = [MetricDefinition('caches.revalidated.bytes', 'counter', 'revalidated.bytes')]
        expected_record = MetricRecord('caches.revalidated.bytes', 'counter', 0, self.plugin.instance_id,
                                       {'cache.name' : 'http_cache', 'nginx.version' : '1.21.3'})

        self.plugin._emit_cache_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_cache_expired_bytes(self):
        metrics = [MetricDefinition('caches.expired.bytes', 'counter', 'expired.bytes')]
        expected_record = MetricRecord('caches.expired.bytes', 'counter', 497995136, self.plugin.instance_id,
                                       {'cache.name' : 'http_cache', 'nginx.version' : '1.21.3'})

        self.plugin._emit_cache_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_cache_bypass_bytes(self):
        metrics = [MetricDefinition('caches.bypass.bytes', 'counter', 'bypass.bytes')]
        expected_record = MetricRecord('caches.bypass.bytes', 'counter', 0, self.plugin.instance_id,
                                       {'cache.name' : 'http_cache', 'nginx.version' : '1.21.3'})

        self.plugin._emit_cache_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_cache_updating_bytes(self):
        metrics = [MetricDefinition('caches.updating.bytes', 'counter', 'updating.bytes')]
        expected_record = MetricRecord('caches.updating.bytes', 'counter', 0, self.plugin.instance_id,
                                       {'cache.name' : 'http_cache', 'nginx.version' : '1.21.3'})

        self.plugin._emit_cache_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_cache_miss_responses_written(self):
        metrics = [MetricDefinition('caches.miss.responses.written', 'counter', 'miss.responses_written')]
        expected_record = MetricRecord('caches.miss.responses.written', 'counter', 1304, self.plugin.instance_id,
                                       {'cache.name' : 'http_cache', 'nginx.version' : '1.21.3'})

        self.plugin._emit_cache_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_cache_miss_bytes_written(self):
        metrics = [MetricDefinition('caches.miss.bytes.written', 'counter', 'miss.bytes_written')]
        expected_record = MetricRecord('caches.miss.bytes.written', 'counter', 160222600, self.plugin.instance_id,
                                       {'cache.name' : 'http_cache', 'nginx.version' : '1.21.3'})

        self.plugin._emit_cache_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_cache_expired_responses_written(self):
        metrics = [MetricDefinition('caches.expired.responses.written', 'counter', 'expired.responses_written')]
        expected_record = MetricRecord('caches.expired.responses.written', 'counter', 4058, self.plugin.instance_id,
                                       {'cache.name' : 'http_cache', 'nginx.version' : '1.21.3'})

        self.plugin._emit_cache_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_cache_expired_bytes_written(self):
        metrics = [MetricDefinition('caches.expired.bytes.written', 'counter', 'expired.bytes_written')]
        expected_record = MetricRecord('caches.expired.bytes.written', 'counter', 497995136, self.plugin.instance_id,
                                       {'cache.name' : 'http_cache', 'nginx.version' : '1.21.3'})

        self.plugin._emit_cache_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_cache_bypass_responses_written(self):
        metrics = [MetricDefinition('caches.bypass.responses.written', 'counter', 'bypass.responses_written')]
        expected_record = MetricRecord('caches.bypass.responses.written', 'counter', 0, self.plugin.instance_id,
                                       {'cache.name' : 'http_cache', 'nginx.version' : '1.21.3'})

        self.plugin._emit_cache_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_cache_bypass_bytes_written(self):
        metrics = [MetricDefinition('caches.bypass.bytes.written', 'counter', 'bypass.bytes_written')]
        expected_record = MetricRecord('caches.bypass.bytes.written', 'counter', 0, self.plugin.instance_id,
                                       {'cache.name' : 'http_cache', 'nginx.version' : '1.21.3'})

        self.plugin._emit_cache_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_stream_server_zone_connections(self):
        metrics = [MetricDefinition('stream.server.zone.connections', 'counter', 'connections')]
        expected_record = MetricRecord('stream.server.zone.connections', 'counter', 132765, self.plugin.instance_id,
                                         {'stream.server.zone.name' : 'dns_loadbalancer', 'nginx.version' : '1.21.3'})

        self.plugin._emit_stream_server_zone_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_stream_server_zone_processing(self):
        metrics = [MetricDefinition('stream.server.zone.processing', 'counter', 'processing')]
        expected_record = MetricRecord('stream.server.zone.processing', 'counter', 0, self.plugin.instance_id,
                                         {'stream.server.zone.name' : 'dns_loadbalancer', 'nginx.version' : '1.21.3'})

        self.plugin._emit_stream_server_zone_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_stream_server_zone_session_2xx(self):
        metrics = [MetricDefinition('stream.server.zone.session.2xx', 'counter', 'sessions.2xx')]
        expected_record = MetricRecord('stream.server.zone.session.2xx', 'counter', 132765, self.plugin.instance_id,
                                         {'stream.server.zone.name' : 'dns_loadbalancer', 'nginx.version' : '1.21.3'})

        self.plugin._emit_stream_server_zone_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_stream_server_zone_session_4xx(self):
        metrics = [MetricDefinition('stream.server.zone.session.4xx', 'counter', 'sessions.4xx')]
        expected_record = MetricRecord('stream.server.zone.session.4xx', 'counter', 0, self.plugin.instance_id,
                                         {'stream.server.zone.name' : 'dns_loadbalancer', 'nginx.version' : '1.21.3'})

        self.plugin._emit_stream_server_zone_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_stream_server_zone_session_5xx(self):
        metrics = [MetricDefinition('stream.server.zone.session.5xx', 'counter', 'sessions.5xx')]
        expected_record = MetricRecord('stream.server.zone.session.5xx', 'counter', 0, self.plugin.instance_id,
                                         {'stream.server.zone.name' : 'dns_loadbalancer', 'nginx.version' : '1.21.3'})

        self.plugin._emit_stream_server_zone_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_stream_upstream_connections(self):
        metrics = [MetricDefinition('stream.upstreams.connections', 'counter', 'connections')]
        expected_record_1 = MetricRecord('stream.upstreams.connections', 'counter', 0, self.plugin.instance_id,
                                         {'stream.upstream.name' : 'postgresql_backends',
                                          'stream.upstream.peer.name' : '10.0.0.22:15431', 'nginx.version' : '1.21.3'})
        expected_record_2 = MetricRecord('stream.upstreams.connections', 'counter', 0, self.plugin.instance_id,
                                         {'stream.upstream.name' : 'postgresql_backends',
                                          'stream.upstream.peer.name' : '10.0.0.23:15431', 'nginx.version' : '1.21.3'})

        expected_record_3 = MetricRecord('stream.upstreams.connections', 'counter', 88905, self.plugin.instance_id,
                                         {'stream.upstream.name' : 'dns_udp_backends',
                                          'stream.upstream.peer.name' : '10.0.3.31:53', 'nginx.version' : '1.21.3'})
        expected_record_4 = MetricRecord('stream.upstreams.connections', 'counter', 44453, self.plugin.instance_id,
                                         {'stream.upstream.name' : 'dns_udp_backends',
                                          'stream.upstream.peer.name' : '10.0.0.33:53', 'nginx.version' : '1.21.3'})

        expected_records = [expected_record_1, expected_record_2, expected_record_3, expected_record_4]

        self.plugin._emit_stream_upstreams_peer_metrics(metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_stream_upstream_active(self):
        metrics = [MetricDefinition('stream.upstreams.active', 'counter', 'active')]
        expected_record_1 = MetricRecord('stream.upstreams.active', 'counter', 0, self.plugin.instance_id,
                                         {'stream.upstream.name' : 'postgresql_backends',
                                          'stream.upstream.peer.name' : '10.0.0.22:15431', 'nginx.version' : '1.21.3'})
        expected_record_2 = MetricRecord('stream.upstreams.active', 'counter', 0, self.plugin.instance_id,
                                         {'stream.upstream.name' : 'postgresql_backends',
                                          'stream.upstream.peer.name' : '10.0.0.23:15431', 'nginx.version' : '1.21.3'})

        expected_record_3 = MetricRecord('stream.upstreams.active', 'counter', 0, self.plugin.instance_id,
                                         {'stream.upstream.name' : 'dns_udp_backends',
                                          'stream.upstream.peer.name' : '10.0.3.31:53', 'nginx.version' : '1.21.3'})
        expected_record_4 = MetricRecord('stream.upstreams.active', 'counter', 0, self.plugin.instance_id,
                                         {'stream.upstream.name' : 'dns_udp_backends',
                                          'stream.upstream.peer.name' : '10.0.0.33:53', 'nginx.version' : '1.21.3'})

        expected_records = [expected_record_1, expected_record_2, expected_record_3, expected_record_4]

        self.plugin._emit_stream_upstreams_peer_metrics(metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_stream_upstream_connections_max(self):
        metrics = [MetricDefinition('stream.upstreams.connections.max', 'counter', 'max_conns')]
        expected_record_1 = MetricRecord('stream.upstreams.connections.max', 'counter', 42, self.plugin.instance_id,
                                         {'stream.upstream.name' : 'postgresql_backends',
                                          'stream.upstream.peer.name' : '10.0.0.22:15431', 'nginx.version' : '1.21.3'})

        expected_records = [expected_record_1]

        self.plugin._emit_stream_upstreams_peer_metrics(metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_stream_upstream_fails(self):
        metrics = [MetricDefinition('stream.upstreams.fails', 'counter', 'fails')]
        expected_record_1 = MetricRecord('stream.upstreams.fails', 'counter', 0, self.plugin.instance_id,
                                         {'stream.upstream.name' : 'postgresql_backends',
                                          'stream.upstream.peer.name' : '10.0.0.22:15431', 'nginx.version' : '1.21.3'})
        expected_record_2 = MetricRecord('stream.upstreams.fails', 'counter', 0, self.plugin.instance_id,
                                         {'stream.upstream.name' : 'postgresql_backends',
                                          'stream.upstream.peer.name' : '10.0.0.23:15431', 'nginx.version' : '1.21.3'})

        expected_record_3 = MetricRecord('stream.upstreams.fails', 'counter', 0, self.plugin.instance_id,
                                         {'stream.upstream.name' : 'dns_udp_backends',
                                          'stream.upstream.peer.name' : '10.0.3.31:53', 'nginx.version' : '1.21.3'})
        expected_record_4 = MetricRecord('stream.upstreams.fails', 'counter', 0, self.plugin.instance_id,
                                         {'stream.upstream.name' : 'dns_udp_backends',
                                          'stream.upstream.peer.name' : '10.0.0.33:53', 'nginx.version' : '1.21.3'})

        expected_records = [expected_record_1, expected_record_2, expected_record_3, expected_record_4]

        self.plugin._emit_stream_upstreams_peer_metrics(metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_stream_upstream_unavailable(self):
        metrics = [MetricDefinition('stream.upstreams.unavailable', 'counter', 'unavail')]
        expected_record_1 = MetricRecord('stream.upstreams.unavailable', 'counter', 0, self.plugin.instance_id,
                                         {'stream.upstream.name' : 'postgresql_backends',
                                          'stream.upstream.peer.name' : '10.0.0.22:15431', 'nginx.version' : '1.21.3'})
        expected_record_2 = MetricRecord('stream.upstreams.unavailable', 'counter', 0, self.plugin.instance_id,
                                         {'stream.upstream.name' : 'postgresql_backends',
                                          'stream.upstream.peer.name' : '10.0.0.23:15431', 'nginx.version' : '1.21.3'})

        expected_record_3 = MetricRecord('stream.upstreams.unavailable', 'counter', 0, self.plugin.instance_id,
                                         {'stream.upstream.name' : 'dns_udp_backends',
                                          'stream.upstream.peer.name' : '10.0.3.31:53', 'nginx.version' : '1.21.3'})
        expected_record_4 = MetricRecord('stream.upstreams.unavailable', 'counter', 0, self.plugin.instance_id,
                                         {'stream.upstream.name' : 'dns_udp_backends',
                                          'stream.upstream.peer.name' : '10.0.0.33:53', 'nginx.version' : '1.21.3'})

        expected_records = [expected_record_1, expected_record_2, expected_record_3, expected_record_4]

        self.plugin._emit_stream_upstreams_peer_metrics(metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_stream_upstream_health_check_checks(self):
        instance_id = self.plugin.instance_id
        metrics = [MetricDefinition('stream.upstreams.health.checks.checks', 'counter', 'health_checks.checks')]
        expected_record_1 = MetricRecord('stream.upstreams.health.checks.checks', 'counter', 113163, instance_id,
                                         {'stream.upstream.name' : 'postgresql_backends',
                                          'stream.upstream.peer.name' : '10.0.0.22:15431', 'nginx.version' : '1.21.3'})
        expected_record_2 = MetricRecord('stream.upstreams.health.checks.checks', 'counter', 113163, instance_id,
                                         {'stream.upstream.name' : 'postgresql_backends',
                                          'stream.upstream.peer.name' : '10.0.0.23:15431', 'nginx.version' : '1.21.3'})

        expected_record_3 = MetricRecord('stream.upstreams.health.checks.checks', 'counter', 113162, instance_id,
                                         {'stream.upstream.name' : 'dns_udp_backends',
                                          'stream.upstream.peer.name' : '10.0.3.31:53', 'nginx.version' : '1.21.3'})
        expected_record_4 = MetricRecord('stream.upstreams.health.checks.checks', 'counter', 113150, instance_id,
                                         {'stream.upstream.name' : 'dns_udp_backends',
                                          'stream.upstream.peer.name' : '10.0.0.33:53', 'nginx.version' : '1.21.3'})

        expected_records = [expected_record_1, expected_record_2, expected_record_3, expected_record_4]

        self.plugin._emit_stream_upstreams_peer_metrics(metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_stream_upstream_health_check_fails(self):
        metrics = [MetricDefinition('stream.upstreams.health.checks.fails', 'counter', 'health_checks.fails')]
        expected_record_1 = MetricRecord('stream.upstreams.health.checks.fails', 'counter', 0, self.plugin.instance_id,
                                         {'stream.upstream.name' : 'postgresql_backends',
                                          'stream.upstream.peer.name' : '10.0.0.22:15431', 'nginx.version' : '1.21.3'})
        expected_record_2 = MetricRecord('stream.upstreams.health.checks.fails', 'counter', 0, self.plugin.instance_id,
                                         {'stream.upstream.name' : 'postgresql_backends',
                                          'stream.upstream.peer.name' : '10.0.0.23:15431', 'nginx.version' : '1.21.3'})

        expected_record_3 = MetricRecord('stream.upstreams.health.checks.fails', 'counter', 0, self.plugin.instance_id,
                                         {'stream.upstream.name' : 'dns_udp_backends',
                                          'stream.upstream.peer.name' : '10.0.3.31:53', 'nginx.version' : '1.21.3'})
        expected_record_4 = MetricRecord('stream.upstreams.health.checks.fails', 'counter', 0, self.plugin.instance_id,
                                         {'stream.upstream.name' : 'dns_udp_backends',
                                          'stream.upstream.peer.name' : '10.0.0.33:53', 'nginx.version' : '1.21.3'})

        expected_records = [expected_record_1, expected_record_2, expected_record_3, expected_record_4]

        self.plugin._emit_stream_upstreams_peer_metrics(metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_stream_upstream_health_check_unhealthy(self):
        instance_id = self.plugin.instance_id
        metrics = [MetricDefinition('stream.upstreams.health.checks.unhealthy', 'counter', 'health_checks.unhealthy')]
        expected_record_1 = MetricRecord('stream.upstreams.health.checks.unhealthy', 'counter', 0, instance_id,
                                         {'stream.upstream.name' : 'postgresql_backends',
                                          'stream.upstream.peer.name' : '10.0.0.22:15431', 'nginx.version' : '1.21.3'})
        expected_record_2 = MetricRecord('stream.upstreams.health.checks.unhealthy', 'counter', 0, instance_id,
                                         {'stream.upstream.name' : 'postgresql_backends',
                                          'stream.upstream.peer.name' : '10.0.0.23:15431', 'nginx.version' : '1.21.3'})

        expected_record_3 = MetricRecord('stream.upstreams.health.checks.unhealthy', 'counter', 0, instance_id,
                                         {'stream.upstream.name' : 'dns_udp_backends',
                                          'stream.upstream.peer.name' : '10.0.3.31:53', 'nginx.version' : '1.21.3'})
        expected_record_4 = MetricRecord('stream.upstreams.health.checks.unhealthy', 'counter', 0, instance_id,
                                         {'stream.upstream.name' : 'dns_udp_backends',
                                          'stream.upstream.peer.name' : '10.0.0.33:53', 'nginx.version' : '1.21.3'})

        expected_records = [expected_record_1, expected_record_2, expected_record_3, expected_record_4]

        self.plugin._emit_stream_upstreams_peer_metrics(metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_stream_upstream_response_time(self):
        instance_id = self.plugin.instance_id
        metrics = [MetricDefinition('stream.upstreams.response.time', 'gauge', 'response_time'),]
        expected_record_1 = MetricRecord('stream.upstreams.response.time', 'gauge', 7, instance_id,
                                         {'stream.upstream.name' : 'dns_udp_backends',
                                          'stream.upstream.peer.name' : '10.0.3.31:53', 'nginx.version' : '1.21.3'})
        expected_record_2 = MetricRecord('stream.upstreams.response.time', 'gauge', 10, instance_id,
                                         {'stream.upstream.name' : 'dns_udp_backends',
                                          'stream.upstream.peer.name' : '10.0.0.33:53', 'nginx.version' : '1.21.3'})

        expected_records = [expected_record_1, expected_record_2]

        self.plugin._emit_stream_upstreams_peer_metrics(metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_stream_upstream_downtime(self):
        instance_id = self.plugin.instance_id
        metrics = [MetricDefinition('stream.upstreams.downtime', 'counter', 'downtime')]
        expected_record_1 = MetricRecord('stream.upstreams.downtime', 'counter', 0, instance_id,
                                         {'stream.upstream.name' : 'postgresql_backends',
                                          'stream.upstream.peer.name' : '10.0.0.22:15431', 'nginx.version' : '1.21.3'})
        expected_record_2 = MetricRecord('stream.upstreams.downtime', 'counter', 0, instance_id,
                                         {'stream.upstream.name' : 'postgresql_backends',
                                          'stream.upstream.peer.name' : '10.0.0.23:15431', 'nginx.version' : '1.21.3'})

        expected_record_3 = MetricRecord('stream.upstreams.downtime', 'counter', 0, instance_id,
                                         {'stream.upstream.name' : 'dns_udp_backends',
                                          'stream.upstream.peer.name' : '10.0.3.31:53', 'nginx.version' : '1.21.3'})
        expected_record_4 = MetricRecord('stream.upstreams.downtime', 'counter', 0, instance_id,
                                         {'stream.upstream.name' : 'dns_udp_backends',
                                          'stream.upstream.peer.name' : '10.0.0.33:53', 'nginx.version' : '1.21.3'})

        expected_records = [expected_record_1, expected_record_2, expected_record_3, expected_record_4]

        self.plugin._emit_stream_upstreams_peer_metrics(metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_stream_upstream_bytes_received(self):
        instance_id = self.plugin.instance_id
        metrics = [MetricDefinition('stream.upstreams.bytes.received', 'counter', 'received')]
        expected_record_1 = MetricRecord('stream.upstreams.bytes.received', 'counter', 0, instance_id,
                                         {'stream.upstream.name' : 'postgresql_backends',
                                          'stream.upstream.peer.name' : '10.0.0.22:15431', 'nginx.version' : '1.21.3'})
        expected_record_2 = MetricRecord('stream.upstreams.bytes.received', 'counter', 0, instance_id,
                                         {'stream.upstream.name' : 'postgresql_backends',
                                          'stream.upstream.peer.name' : '10.0.0.23:15431', 'nginx.version' : '1.21.3'})

        expected_record_3 = MetricRecord('stream.upstreams.bytes.received', 'counter', 10701561, instance_id,
                                         {'stream.upstream.name' : 'dns_udp_backends',
                                          'stream.upstream.peer.name' : '10.0.3.31:53', 'nginx.version' : '1.21.3'})
        expected_record_4 = MetricRecord('stream.upstreams.bytes.received', 'counter', 2696239, instance_id,
                                         {'stream.upstream.name' : 'dns_udp_backends',
                                          'stream.upstream.peer.name' : '10.0.0.33:53', 'nginx.version' : '1.21.3'})

        expected_records = [expected_record_1, expected_record_2, expected_record_3, expected_record_4]

        self.plugin._emit_stream_upstreams_peer_metrics(metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_stream_upstream_bytes_sent(self):
        instance_id = self.plugin.instance_id
        metrics = [MetricDefinition('stream.upstreams.bytes.sent', 'counter', 'sent')]
        expected_record_1 = MetricRecord('stream.upstreams.bytes.sent', 'counter', 0, instance_id,
                                         {'stream.upstream.name' : 'postgresql_backends',
                                          'stream.upstream.peer.name' : '10.0.0.22:15431', 'nginx.version' : '1.21.3'})
        expected_record_2 = MetricRecord('stream.upstreams.bytes.sent', 'counter', 0, instance_id,
                                         {'stream.upstream.name' : 'postgresql_backends',
                                          'stream.upstream.peer.name' : '10.0.0.23:15431', 'nginx.version' : '1.21.3'})

        expected_record_3 = MetricRecord('stream.upstreams.bytes.sent', 'counter', 2801893, instance_id,
                                         {'stream.upstream.name' : 'dns_udp_backends',
                                          'stream.upstream.peer.name' : '10.0.3.31:53', 'nginx.version' : '1.21.3'})
        expected_record_4 = MetricRecord('stream.upstreams.bytes.sent', 'counter', 1360319, instance_id,
                                         {'stream.upstream.name' : 'dns_udp_backends',
                                          'stream.upstream.peer.name' : '10.0.0.33:53', 'nginx.version' : '1.21.3'})

        expected_records = [expected_record_1, expected_record_2, expected_record_3, expected_record_4]

        self.plugin._emit_stream_upstreams_peer_metrics(metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_stream_upstream_zombies(self):
        instance_id = self.plugin.instance_id
        metrics = [MetricDefinition('stream.upstreams.zombies', 'counter', 'zombies')]
        expected_record_1 = MetricRecord('stream.upstreams.zombies', 'counter', 0, instance_id,
                                         {'stream.upstream.name' : 'postgresql_backends', 'nginx.version' : '1.21.3'})
        expected_record_2 = MetricRecord('stream.upstreams.zombies', 'counter', 0, instance_id,
                                         {'stream.upstream.name' : 'dns_udp_backends', 'nginx.version' : '1.21.3'})

        expected_records = [expected_record_1, expected_record_2]

        self.plugin._emit_stream_upstreams_metrics(metrics, self.mock_sink)

        self.assertEquals(len(expected_records), len(self.mock_sink.captured_records))
        self._verify_records_captured(expected_records)

    def test_processes_respawned(self):
        metrics = [MetricDefinition('processes.respawned', 'counter', 'respawned')]
        expected_record = MetricRecord('processes.respawned', 'counter', 0, self.plugin.instance_id,
                                       {'nginx.version' : '1.21.3'})

        self.plugin._emit_processes_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

    def test_emit_with_extra_dimensions(self):
        extra_dim_key = self._random_string()
        extra_dim_value = self._random_string()

        self.plugin.global_dimensions[extra_dim_key] = extra_dim_value

        metrics = [MetricDefinition('connections.accepted', 'counter', 'accepted')]
        expected_record = MetricRecord('connections.accepted', 'counter', 18717986, self.plugin.instance_id,
                                       {'nginx.version' : '1.21.3', extra_dim_key : extra_dim_value})

        self.plugin._emit_connection_metrics(metrics, self.mock_sink)

        self.assertEquals(1, len(self.mock_sink.captured_records))
        self._validate_single_record(expected_record, self.mock_sink.captured_records[0])

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
        metric_names.extend(self._extract_metric_names_from_definitions(DEFAULT_SSL_METRICS))
        metric_names.extend(self._extract_metric_names_from_definitions(DEFAULT_REQUESTS_METRICS))
        metric_names.extend(self._extract_metric_names_from_definitions(DEFAULT_SERVER_ZONE_METRICS))
        metric_names.extend(self._extract_metric_names_from_definitions(DEFAULT_UPSTREAM_METRICS))
        metric_names.extend(self._extract_metric_names_from_definitions(DEFAULT_CACHE_METRICS))

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

    def _build_mock_nginx_agent(self):
        mock_nginx_agent = Mock()

        status_json = self._read_test_resource_json('resources/status_response.json')
        status_caches_json = self._read_test_resource_json('resources/status_caches.json')
        status_server_zones_json = self._read_test_resource_json('resources/status_server_zones.json')
        status_upstreams_json = self._read_test_resource_json('resources/status_upstreams.json')
        status_stream_upstreams_json = self._read_test_resource_json('resources/status_stream_upstreams.json')
        status_stream_server_zones_json = self._read_test_resource_json('resources/status_stream_server_zones.json')
        status_connections_json = self._read_test_resource_json('resources/status_connections.json')
        status_requests_json = self._read_test_resource_json('resources/status_requests.json')
        status_ssl_json = self._read_test_resource_json('resources/status_ssl.json')
        status_slabs_json = self._read_test_resource_json('resources/status_slabs.json')
        processes_json = self._read_test_resource_json('resources/status_processes.json')

        mock_nginx_agent.get_status = MagicMock(return_value=status_json)
        mock_nginx_agent.get_caches = MagicMock(return_value=status_caches_json)
        mock_nginx_agent.get_server_zones = MagicMock(return_value=status_server_zones_json)
        mock_nginx_agent.get_upstreams = MagicMock(return_value=status_upstreams_json)
        mock_nginx_agent.get_stream_upstreams = MagicMock(return_value=status_stream_upstreams_json)
        mock_nginx_agent.get_stream_server_zones = MagicMock(return_value=status_stream_server_zones_json)
        mock_nginx_agent.get_connections = MagicMock(return_value=status_connections_json)
        mock_nginx_agent.get_requests = MagicMock(return_value=status_requests_json)
        mock_nginx_agent.get_ssl = MagicMock(return_value=status_ssl_json)
        mock_nginx_agent.get_slabs = MagicMock(return_value=status_slabs_json)
        mock_nginx_agent.get_processes = MagicMock(return_value=processes_json)

        mock_nginx_agent.get_nginx_version = MagicMock(return_value='1.21.3')
        mock_nginx_agent.get_nginx_address = MagicMock(return_value='18.193.151.235')

        return mock_nginx_agent

    def _validate_single_record(self, expected_record, actual_record):
        self.assertIsNotNone(actual_record)
        self.assertEquals(expected_record.name, actual_record.name)
        self.assertEquals(expected_record.type, actual_record.type)
        self.assertEquals(expected_record.value, actual_record.value)
        self.assertEquals(expected_record.instance_id, actual_record.instance_id)
        self.assertDictEqual(expected_record.dimensions, actual_record.dimensions)
        self.assertIsNotNone(actual_record.timestamp)

    def _verify_records_captured(self, expected_records):
        for expected_record in expected_records:
            self.assertIsNotNone(next((record for record in self.mock_sink.captured_records\
                if self._compare_records(expected_record, record)), None),
                                 'Captured records does not contain: {} captured records: {}'
                                 .format(expected_record.to_string(),
                                         [record.to_string() for record in self.mock_sink.captured_records]))

    def _compare_records(self, expected_record, actual_record):
        try:
            self._validate_single_record(expected_record, actual_record)
            return True
        except Exception:
            pass
        return False

    def _mocked_requests_get(self, *args, **kwargs):
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code

            def json(self):
                return self.json_data

        return MockResponse([1, 2, 3, 4, 5, 6, 7], 200)


class MockMetricSink(object):
    def __init__(self):
        self.captured_records = []

    def emit(self, metric_record):
        self.captured_records.append(metric_record)
