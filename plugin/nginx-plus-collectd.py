#!/usr/bin/env python
import collectd

class PluginMetric:
    def __init__(self, name, metric_type, path, dimensions=None):
        self.name = name
        self.metric_type = metric_type
        self.path = path
        self.dimensions = dimensions or []

class PluginMetricDimension:
    def __init__(self, name, path=None, default_value=None):
        self.name = name
        self.path = path
        self.default_value = default_value

class PluginMetricGroup:
    def __init__(self, metrics=None, dimensions=None):
        self.metrics = metrics
        self.dimensions = dimensions

# Dimensions used for each metric group
SERVER_DIMENSIONS = [
    PluginMetricDimension('nginx.version', path='nginx_version'),
    PluginMetricDimension('nginx.build', path='nginx_build')
]

SERVER_ZONE_DIMENSIONS = [
    PluginMetricDimension('server.zone.name', path='')
]

UPSTREAM_DIMENSIONS = [
    PluginMetricDimension('upstream.name', path=''),
    PluginMetricDimension('upstream.peer.name', path=''),
    PluginMetricDimension('upstream.peer.server', path='')
]

STREAM_SERVER_ZONE_DIMENSIONS = [
    PluginMetricDimension('stream.server.zone.name', path='')
]

STREAM_UPSTREAM_DIMENSIONS = [
    PluginMetricDimension('stream.upstream.name', path=''),
    PluginMetricDimension('stream.upstream.peer.name', path=''),
    PluginMetricDimension('stream.upstream.peer.server', path='')
]

MEMORY_ZONE_DIMENSIONS = [
    PluginMetricDimension('memory.zone.name', path='')
]

CACHE_DIMENSIONS = [
    PluginMetricDimension('cache.name', path='')
]



class NginxPlusPlugin:
    def init_callback(self):
        '''
        Initialize the plugin.
        This is called only once, when the plugin module is loaded.
        '''
        # TODO

    def config_callback(self, conf):
        '''
        Configure the plugin with the configuration provided by collectd.
        '''
        # TODO

    def read_callback(self):
        '''
        Called to emit the actual metrics.
        Called once per interval (see Interval configuration option of collectd).
        If an exception is thrown the plugin will be skipped for an
        increasing amount of time until it returns to normal.
        '''
        # TODO

class NginxStatusAgent:
    def __init__(self, status_ip='127.0.0.1', status_port=8080):
        self.status_ip = status_ip
        self.status_port = status_port

    def _get_status(self):
        '''
        Fetch the server status JSON.
        '''
        # TODO



if __name__ == 'main':
    plugin = NginxPlusPlugin()

    collectd.register_init(plugin.init_callback)
    collectd.register_config(plugin.config_callback)
    collectd.register_read(plugin.read_callback)
