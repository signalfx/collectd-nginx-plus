#!/usr/bin/env python
import random
import string
from unittest import TestCase
from requests import HTTPError
from mock import Mock, patch
from plugin.nginx_plus_collectd import NginxStatusAgent

class NginxStatusAgentTest(TestCase):
    def setUp(self):
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
        username = _random_string()
        password = _random_string()
        auth_tuple = (username, password)

        auth_agent = NginxStatusAgent(self.status_host, self.status_port, username, password)

        auth_agent.get_status()
        mock_requests_get.assert_called_with(self.base_status_url, auth=auth_tuple)

def _random_string(length=8):
    return ''.join(random.choice(string.lowercase) for i in range(length))

def _random_int(start=0, stop=100000):
    return random.randint(start, stop)
