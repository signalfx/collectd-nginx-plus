#!/usr/bin/env python
import time
import requests

class MetricDefinition:
    def __init__(self, name, metric_type, scoped_object_key):
        self.name = name
        self.metric_type = metric_type
        self.scoped_object_key = scoped_object_key

class MetricEmitter:
    def __init__(self, emit_func, metrics):
        self.emit_func = emit_func
        self.metrics = metrics

    def emit(self, status_json, sink):
        self.emit_func(status_json, self.metrics, sink)

class MetricRecord:
    TO_STRING_FORMAT = 'metric_name={},metric_type={},metric_value={},instance_id={},dimensions={},timestamp={}'

    def __init__(self, metric_name, metric_type, metric_value, instance_id, dimensions=None, timestamp=None):
        self.metric_name = metric_name
        self.metric_type = metric_type
        self.metric_value = metric_value
        self.instance_id = instance_id
        self.dimensions = dimensions or {}
        self.timestamp = timestamp or time.time()

    def to_string(self):
        return TO_STRING_FORMAT.format(self.metric_name, self.metric_type, self.metric_value, self.instance_id, self.dimensions, self.timestamp)

class MetricSink:
    def emit(self, metric_record):
        emit_value = collectd.Values()

        emit_value.time = metric_record.timestamp
        emit_value.plugin = 'nginx-plus'
        emit_value.values = metric_record.metric_value
        emit_value.point_type = metric_record.metric_name
        emit_value.plugin_instance = metric_record.instance_id
        emit_value.plugin_instance += '[{dimensions}]'.format(dimensions=metric_record.dimensions)

        # With some versions of CollectD, a dummy metadata map must to be added
        # to each value for it to be correctly serialized to JSON by the
        # write_http plugin. See
        # https://github.com/collectd/collectd/issues/716
        emit_value.meta = {'true': 'true'}

        emit_value.dispatch()

# Server configueration flags
STATUS_IP = 'StatusIp'
STATUS_PORT = 'StatusPort'

# Metric group configuration flags
SERVER_ZONE = 'ServerZone'
MEMORY_ZONE = 'MemoryZone'
UPSTREAM = 'Upstream'
CACHE = 'Cache'
STREAM_SERVER_ZONE = 'StreamServerZone'
STREAM_UPSTREAM = 'StreamUpstream'

# Metric groups
DEFAULT_CONNECTION_METRICS = [
    MetricDefinition('connections.accepted', 'guage', 'connections.accepted'),
    MetricDefinition('connections.dropped', 'guage', 'connections.dropped'),
    MetricDefinition('connections.idle', 'guage', 'connections.idle'),
    MetricDefinition('connections.failed', 'guage', 'connections.failed'),
    MetricDefinition('ssl.handshakes.successful', 'guage', 'ssl.handshakes.successful'),
    MetricDefinition('ssl.handshakes.failed', 'guage', 'ssl.handshakes.failed'),
    MetricDefinition('requests.total', 'guage', 'requests.total'),
    MetricDefinition('requests.current', 'guage', 'requests.current'),
]

DEFAULT_SERVER_ZONE_METRICS = [
    MetricDefinition('server.zone.requests', 'guage', 'requests')
]

DEFAULT_UPSTREAM_METRICS = [
    MetricDefinition('upstream.requests', 'guage', 'requests')
]

DEFAULT_STREAM_SERVER_ZONE_METRICS = [
    MetricDefinition('stream.server.zone.connections', 'guage', 'connections')
]

DEFAULT_STREAM_UPSTEAM_METRICS = [
    MetricDefinition('stream.upstreams.requests', 'guage', 'requests')
]

SERVER_ZONE_METRICS = []

MEMORY_ZONE_METRICS = []

UPSTREAM_METRICS = []

CACHE_METRICS = []

STREAM_SERVER_ZONE_METRICS = []

STREAM_UPSTREAM_METRICS = []

class NginxPlusPlugin:
    def __init__(self):
        self.nginx_agent = None
        self.instance_id = None
        self.sink = None
        self.emitters = []

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
        status_ip = None
        status_port = None

        # Iterate the configueration values, pickup the status endpoint info
        # and creating any specified opt-in metric emitters
        for node in conf.children:
            if node.key == STATUS_IP:
                status_ip = node.values[0]
            elif node.key == STATUS_PORT:
                status_port = node.values[0]
            elif node.key == CACHE:
                self.emitters.append(MetricEmitter(self._emit_cache_metrics, CACHE_METRICS))
            elif node.key == UPSTREAM:
                self.emitters.append(MetricEmitter(self._emit_upsteams_metrics, UPSTREAM_METRICS))
            elif node.key == MEMORY_ZONE:
                self.emitters.append(MetricEmitter(self._emit_memory_zone_metrics, MEMORY_ZONE_METRICS))
            elif node.key == SERVER_ZONE:
                self.emitters.append(MetricEmitter(self._emit_server_zone_metrics, SERVER_ZONE_METRICS))
            elif node.key == STREAM_UPSTREAM:
                self.emitters.append(MetricEmitter(self._emit_stream_upstreams_metric, STREAM_UPSTREAM_METRICS))
            elif node.key == STREAM_SERVER_ZONE:
                self.emitters.append(MetricEmitter(self._emit_stream_server_zone_metrics, STREAM_SERVER_ZONE_METRICS))

        # Default metric emitters
        self.emitters.append(MetricEmitter(self._emit_top_level_metrics, DEFAULT_CONNECTION_METRICS))
        self.emitters.append(MetricEmitter(self._emit_server_zone_metrics, DEFAULT_SERVER_ZONE_METRICS))
        self.emitters.append(MetricEmitter(self._emit_upsteams_metrics, DEFAULT_UPSTREAM_METRICS))
        self.emitters.append(MetricEmitter(self._emit_stream_server_zone_metrics, DEFAULT_STREAM_SERVER_ZONE_METRICS))
        self.emitters.append(MetricEmitter(self._emit_stream_upstreams_metric, DEFAULT_STREAM_UPSTEAM_METRICS))

        self.sink = MetricSink()
        self.nginx_agent = NginxStatusAgent(status_ip, status_port)
        self.instance_id = '{}:{}'.format(status_ip, str(status_port))


    def read_callback(self):
        '''
        Called to emit the actual metrics.
        Called once per interval (see Interval configuration option of collectd).
        If an exception is thrown the plugin will be skipped for an
        increasing amount of time until it returns to normal.
        '''
        status_json = self.nginx_agent.get_status()
        for emitter in self.emitters:
            emitter.emit(status_json, self.sink)


    def _emit_top_level_metrics(self, status_json, metrics, sink):
        dimensions = {'nginx.version' : self._reduce_to_path(status_json, 'nginx_version')}
        self._fetch_and_emit_metrics(status_json, metrics, dimensions, sink)

    def _emit_server_zone_metrics(self, status_json, metrics, sink):
        server_zone_obj = self._reduce_to_path(status_json, 'server_zones')
        if server_zone_obj:
            # Each key in the server_zone object is a server zone name
            for zone_name, server_zone in server_zone_obj.iteritems():
                dimensions = {'server.zone.name' : zone_name}
                self._fetch_and_emit_metrics(server_zone, metrics, dimensions, sink)

    def _emit_upsteams_metrics(self, status_json, metrics, sink):
        upsteams_obj = self._reduce_to_path(status_json, 'upsteams')
        if upsteams_obj:
            # Each key in the upsteams object is an upstream name
            for upsteam_name, upstream in upsteams_obj.iteritems():
                dimensions = {'upstream.name' : zone_name}
                # Each upsteam is composed of peer servers, this is where the metric values are provided
                for peer in upsteam.peers:
                    # Get the dimensions from each peer server
                    dimensions['upstream.peer.name'] = self._reduce_to_path(peer, 'name')
                    self._fetch_and_emit_metrics(peer, metrics, dimensions, sink)

    def _emit_stream_server_zone_metrics(self, status_json, metrics, sink):
        stream_server_zones_obj = self._reduce_to_path(status_json, 'stream.server_zones')
        if stream_server_zones_obj:
            # Each key in the stream.server_zones object is a server zone name
            for zone_name, server_zone in stream_server_zones_obj.iteritems():
                dimensions = {'stream.server.zone.name' : zone_name}
                self._fetch_and_emit_metrics(server_zone, metrics, dimensions, sink)

    def _emit_stream_upstreams_metric(self, status_json, metrics, sink):
        stream_upsteams_obj = self._reduce_to_path(status_json, 'stream.upsteams')
        if stream_upsteams_obj:
            # Each key in the stream.upstreams object is an upstream name
            for upsteam_name, upstream in stream_upsteams_obj.iteritems():
                dimensions = {'stream.upstream.name' : zone_name}
                # Each upsteam is composed of peer servers, this is where the metric values are provided
                for peer in upsteam.peers:
                    # Get the dimensions from each peer server
                    dimensions['stream.upstream.peer.name'] = self._reduce_to_path(peer, 'name')
                    self._fetch_and_emit_metrics(peer, metrics, dimensions, sink)

    def _emit_memory_zone_metrics(self, status_json, metrics, sink):
        slab_obj = self._reduce_to_path(status_json, 'slabs')
        if slab_obj:
            # Each key in the slabs object is a slab name
            for slab_name, slab in slab_obj:
                dimensions = {'memory.zone.name' : slab_name}
                self._fetch_and_emit_metrics(slab, metrics, dimensions, sink)

    def _emit_cache_metrics(self, status_json, metrics, sink):
        cache_obj = self._reduce_to_path(status_json, 'caches')
        if cache_obj:
            # Each key in the caches object is a cache name
            for cache_name, cache in cache_obj:
                dimensions = {'cache.name' : cache_name}
                self._fetch_and_emit_metrics(cache, metrics, dimensions, sink)

    def _fetch_and_emit_metrics(self, scoped_obj, metrics, dimensions, sink):
        for metric in metrics:
            metric_value = self._reduce_to_path(scoped_obj, metric.scoped_object_key)
            if metric_value:
                sink.emit(MetricRecord(metric.name,metric.metric_type, metric_value, self.instance_id, dimensions, time.time()))

    # Copied from collectd-elasticsearch
    def _reduce_to_path(self, obj, path):
        try:
            if type(path) in (str, unicode):
                path = path.split('.')
            return reduce(lambda x, y: x[y], path, obj)
        except:
            return None


class NginxStatusAgent:
    def __init__(self, status_ip=None, status_port=None):
        self.status_ip = status_ip or '127.0.0.1'
        self.status_port = status_port or 8080

        self.status_url = '{}:{}/status'.format(self.status_ip, str(self.status_port))

    def _get_status(self):
        '''
        Fetch the server status JSON.
        '''
        return requests.get(status_url)


if __name__ == 'main':
    plugin = NginxPlusPlugin()

    # TODO
else:
    import collectd

    plugin = NginxPlusPlugin()

    collectd.register_init(plugin.init_callback)
    collectd.register_config(plugin.config_callback)
    collectd.register_read(plugin.read_callback)
