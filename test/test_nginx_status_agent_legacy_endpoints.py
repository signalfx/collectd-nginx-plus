#!/usr/bin/env python
import random
import string
from sys import api_version
from unittest import TestCase
from requests import HTTPError
from mock import Mock, patch, MagicMock
from plugin.nginx_plus_collectd import NginxStatusAgent, DEFAULT_API_VERSION

class NginxStatusAgentTest(TestCase):
    @patch('requests.get')
    def setUp(self, mock_requests_get):
        mock_requests_get.side_effect = _mocked_requests_get

        self.status_host = _random_string()
        self.status_port = _random_int()
        self.base_status_url = 'http://{}:{}/status'.format(self.status_host, str(self.status_port))

        self.agent = NginxStatusAgent(self.status_host, self.status_port)

    @patch('requests.get')
    def test_return_json_on_ok_status(self, mock_requests_get):
        expected_response = {'foo' : 'bar'}

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response

        mock_requests_get.return_value = mock_response

        actual_response = self.agent._send_get('http://demo.nginx.com/status')
        self.assertDictEqual(expected_response, actual_response)

    @patch('requests.get')
    def test_none_return_on_bad_status(self, mock_requests_get):
        mock_response = Mock()
        mock_response.status_code = 500

        mock_requests_get.return_value = mock_response

        response = self.agent._send_get('http://demo.nginx.com/status')
        self.assertIsNone(response)

    @patch('requests.get')
    def test_none_on_exception(self, mock_requests_get):
        mock_requests_get.side_effect = HTTPError('Thrown from test_none_on_exception')

        response = self.agent._send_get('http://demo.nginx.com/status')
        self.assertIsNone(response)

    @patch('requests.get')
    def test_get_status(self, mock_requests_get):
        self.agent.get_status()
        mock_requests_get.assert_called_with(self.base_status_url, auth=None)

    @patch('requests.get')
    def test_get_connections(self, mock_requests_get):
        expected_url = '{}/connections'.format(self.base_status_url)

        self.agent.get_connections()
        mock_requests_get.assert_called_with(expected_url, auth=None)

    @patch('requests.get')
    def test_get_requests(self, mock_requests_get):
        expected_url = '{}/requests'.format(self.base_status_url)

        self.agent.get_requests()
        mock_requests_get.assert_called_with(expected_url, auth=None)

    @patch('requests.get')
    def test_get_ssl(self, mock_requests_get):
        expected_url = '{}/ssl'.format(self.base_status_url)

        self.agent.get_ssl()
        mock_requests_get.assert_called_with(expected_url, auth=None)

    @patch('requests.get')
    def test_get_slabs(self, mock_requests_get):
        expected_url = '{}/slabs'.format(self.base_status_url)

        self.agent.get_slabs()
        mock_requests_get.assert_called_with(expected_url, auth=None)

    @patch('requests.get')
    def test_get_nginx_version(self, mock_requests_get):
        expected_url = '{}/nginx_version'.format(self.base_status_url)

        self.agent.get_nginx_version()
        mock_requests_get.assert_called_with(expected_url, auth=None)

    @patch('requests.get')
    def test_get_nginx_address(self, mock_requests_get):
        expected_url = '{}/address'.format(self.base_status_url)

        self.agent.get_nginx_address()
        mock_requests_get.assert_called_with(expected_url, auth=None)

    @patch('requests.get')
    def test_get_caches(self, mock_requests_get):
        expected_url = '{}/caches'.format(self.base_status_url)

        self.agent.get_caches()
        mock_requests_get.assert_called_with(expected_url, auth=None)

    @patch('requests.get')
    def test_get_server_zones(self, mock_requests_get):
        expected_url = '{}/server_zones'.format(self.base_status_url)

        self.agent.get_server_zones()
        mock_requests_get.assert_called_with(expected_url, auth=None)

    @patch('requests.get')
    def test_get_upstreams(self, mock_requests_get):
        expected_url = '{}/upstreams'.format(self.base_status_url)

        self.agent.get_upstreams()
        mock_requests_get.assert_called_with(expected_url, auth=None)

    @patch('requests.get')
    def test_get_stream_server_zones(self, mock_requests_get):
        expected_url = '{}/stream/server_zones'.format(self.base_status_url)

        self.agent.get_stream_server_zones()
        mock_requests_get.assert_called_with(expected_url, auth=None)

    @patch('requests.get')
    def test_get_stream_upstreams(self, mock_requests_get):
        expected_url = '{}/stream/upstreams'.format(self.base_status_url)

        self.agent.get_stream_upstreams()
        mock_requests_get.assert_called_with(expected_url, auth=None)

    @patch('requests.get')
    def test_get_status_with_auth(self, mock_requests_get):
        mock_requests_get.side_effect = _mocked_requests_get

        username = _random_string()
        password = _random_string()
        auth_tuple = (username, password)

        auth_agent = NginxStatusAgent(self.status_host, self.status_port, username, password)

        auth_agent.get_status()
        mock_requests_get.assert_called_with(self.base_status_url, auth=auth_tuple)

    @patch('requests.get')
    def test_get_processes(self, mock_requests_get):
        expected_url = '{}/processes'.format(self.base_status_url)

        self.agent.get_processes()
        mock_requests_get.assert_called_with(expected_url, auth=None)

    @patch('requests.get')
    def test_non_default_api_base_path(self, mock_requests_get):
        mock_requests_get.side_effect = _mocked_requests_get

        agent = NginxStatusAgent(self.status_host, self.status_port, api_base_path='/test/status')
        self.assertEquals(agent.api_version, None)
        self.assertEquals(agent.api_base_path, '/test/status')

    @patch('requests.get')
    def test_default_api_base_path(self, mock_requests_get):
        mock_requests_get.side_effect = _mocked_requests_get

        agent = NginxStatusAgent(self.status_host, self.status_port)
        self.assertEquals(agent.api_version, None)
        self.assertEquals(agent.api_base_path, '/status')

    @patch('requests.get')
    def test_invalid_api_base_path_initialization(self, mock_requests_get):
        mock_requests_get.side_effect = _mocked_requests_get
        expected_base_path_url = "http://{}:{}invalid/status".format(self.status_host, self.status_port)

        agent = NginxStatusAgent(self.status_host, self.status_port, api_base_path='invalid/status')
        agent._initialize_legacy_api_urls()
        self.assertEquals(agent.base_status_url, expected_base_path_url)

    @patch('requests.get')
    def test_invalid_api_base_path(self, mock_requests_get):
        mock_requests_get.side_effect = _mocked_requests_get

        with self.assertRaises(RuntimeError) as runtime_error:
            NginxStatusAgent(self.status_host, self.status_port, api_base_path='/invalid')
        self.assertEquals(runtime_error.exception.message, "Failed to detect the Nginx-plus API type (versioned or legacy), please check your input configuration.")

    @patch('requests.get')
    def test_get_api_version(self, mock_requests_get):
        mock_requests_get.side_effect = _mocked_requests_get
        self.agent.api_base_path = None

        api_version = self.agent._get_api_version()
        self.assertEquals(None, api_version)

    @patch('requests.get')
    def test_initialize_legacy_api_url(self, mock_requests_get):
        mock_requests_get.side_effect = _mocked_requests_get
        self.nginx_version_url = '{}/nginx_version'.format(self.base_status_url)
        self.address_url = '{}/address'.format(self.base_status_url)
        self.caches_url = '{}/caches'.format(self.base_status_url)
        self.server_zones_url = '{}/server_zones'.format(self.base_status_url)
        self.upstreams_url = '{}/upstreams'.format(self.base_status_url)
        self.stream_upstream_url = '{}/stream/upstreams'.format(self.base_status_url)
        self.stream_server_zones_url = '{}/stream/server_zones'.format(self.base_status_url)
        self.connections_url = '{}/connections'.format(self.base_status_url)
        self.requests_url = '{}/requests'.format(self.base_status_url)
        self.ssl_url = '{}/ssl'.format(self.base_status_url)
        self.slabs_url = '{}/slabs'.format(self.base_status_url)
        self.processes_url = '{}/processes'.format(self.base_status_url)

        self.agent._initialize_legacy_api_urls()
        self.assertEquals(self.nginx_version_url, self.agent.nginx_version_url)
        self.assertEquals(self.address_url, self.agent.address_url)
        self.assertEquals(self.caches_url, self.agent.caches_url)
        self.assertEquals(self.server_zones_url, self.agent.server_zones_url)
        self.assertEquals(self.upstreams_url, self.agent.upstreams_url)
        self.assertEquals(self.stream_upstream_url, self.agent.stream_upstream_url)
        self.assertEquals(self.stream_server_zones_url, self.agent.stream_server_zones_url)
        self.assertEquals(self.connections_url, self.agent.connections_url)
        self.assertEquals(self.requests_url, self.agent.requests_url)
        self.assertEquals(self.ssl_url, self.agent.ssl_url)
        self.assertEquals(self.slabs_url, self.agent.slabs_url)
        self.assertEquals(self.processes_url, self.agent.processes_url)

def _random_string(length=8):
    return ''.join(random.choice(string.lowercase) for i in range(length))

def _random_int(start=0, stop=100000):
    return random.randint(start, stop)

def _mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    if '/{}'.format(DEFAULT_API_VERSION) in args[0]:
        return MockResponse(None, 404)

    if '/status' in args[0]:
        return MockResponse(None, 200)

    return MockResponse(None, 404)
