#!/usr/bin/env python
import sys
from unittest import TestCase
from mock import Mock, patch

# Mock out the collectd module
sys.modules['collectd'] = Mock()

from plugin.nginx_plus_collectd import NginxPlusPluginManager, STATUS_HOST, STATUS_PORT

class NginxPlusPluginManagerTest(TestCase):

    def setUp(self):
        self.plugin_manager = NginxPlusPluginManager()

    @patch('requests.get')
    def test_config_callback(self, mock_requests_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [1, 2, 3, 4, 5, 6, 7]

        mock_requests_get.return_value = mock_response

        expected_ip_1 = '192.168.0.0'
        expected_port_1 = '8080'

        expected_ip_2 = '192.168.0.1'
        expected_port_2 = '8081'

        mock_config_ip_child_1 = _build_mock_config_child(STATUS_HOST, expected_ip_1)
        mock_config_port_child_1 = _build_mock_config_child(STATUS_PORT, expected_port_1)

        mock_config_ip_child_2 = _build_mock_config_child(STATUS_HOST, expected_ip_2)
        mock_config_port_child_2 = _build_mock_config_child(STATUS_PORT, expected_port_2)

        mock_config_1 = Mock()
        mock_config_1.children = [mock_config_ip_child_1, mock_config_port_child_1]

        mock_config_2 = Mock()
        mock_config_2.children = [mock_config_ip_child_2, mock_config_port_child_2]

        self.plugin_manager.config_callback(mock_config_1)
        self.plugin_manager.config_callback(mock_config_2)

        self.assertEquals(2, len(self.plugin_manager.plugins))

        plugin_1 = self.plugin_manager.plugins[0]
        actual_ip_1 = plugin_1.nginx_agent.status_host
        actual_port_1 = plugin_1.nginx_agent.status_port
        self.assertEquals(expected_ip_1, actual_ip_1)
        self.assertEquals(expected_port_1, actual_port_1)

        plugin_2 = self.plugin_manager.plugins[1]
        actual_ip_2 = plugin_2.nginx_agent.status_host
        actual_port_2 = plugin_2.nginx_agent.status_port
        self.assertEquals(expected_ip_2, actual_ip_2)
        self.assertEquals(expected_port_2, actual_port_2)

    def test_read_callback(self):
        mock_plugin_1 = Mock()
        mock_plugin_2 = Mock()

        self.plugin_manager.plugins = [mock_plugin_1, mock_plugin_2]
        self.plugin_manager.read_callback()

        mock_plugin_1.read.assert_called()
        mock_plugin_2.read.assert_called()

def _build_mock_config_child(key, value):
    mock_config_child = Mock()
    mock_config_child.key = key
    mock_config_child.values = [value]

    return mock_config_child
