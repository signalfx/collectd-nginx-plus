#!/usr/bin/env python
import os
import sys
import time
import logging
import requests
from requests.exceptions import RequestException

class MetricDefinition(object):
    '''
    Struct for information needed to build a metric.

    Constructor Arguements:
        name: The name of the metric
        metric_type: The kind of metric, e.g. guage or counter
        scoped_object_key: A "." delineated path to the desired value
                            within the object its expected to be extracted from
    '''
    def __init__(self, name, metric_type, scoped_object_key):
        self.name = name
        self.type = metric_type
        self.scoped_object_key = scoped_object_key

class MetricEmitter(object):
    '''
    Encapsulates a function to build metrics and the definitions of metrics
    that should be built.

    Constructor Arguements:
        emit_func: The function used to build and emit metrics from the NGINX+
                    status JSON. The function is expected to accept the arguements:
                        * A list of MetricDefinitions
                        * An instance of MetricSink

        metrics: A list of MetricDefinition, the metrics to be built and emitted by emit_func
    '''
    def __init__(self, emit_func, metrics):
        self.emit_func = emit_func
        self.metrics = metrics

    def emit(self, sink):
        '''
        Build and emit metrics with the encapsulated function and metric definitions.
        '''
        self.emit_func(self.metrics, sink)

class MetricRecord(object):
    '''
    Struct for all information needed to emit a single collectd metric.
    MetricSink is the expected consumer of instances of this class.
    '''
    TO_STRING_FORMAT = '[name={},type={},value={},instance_id={},dimensions={},timestamp={}]'

    def __init__(self, name, metric_type, value, instance_id, dimensions=None, timestamp=None):
        self.name = name
        self.type = metric_type
        self.value = value
        self.instance_id = instance_id
        self.dimensions = dimensions or {}
        self.timestamp = timestamp or time.time()

    def to_string(self):
        return MetricRecord.TO_STRING_FORMAT.format(self.name, self.type, self.value,\
            self.instance_id, self.dimensions, self.timestamp)

class MetricSink(object):
    '''
    Responsible for transforming and dispatching a MetricRecord via collectd.
    '''
    def emit(self, metric_record):
        '''
        Construct a single collectd Values instance from the given MetricRecord
        and dispatch.
        '''
        emit_value = collectd.Values()

        emit_value.time = metric_record.timestamp
        emit_value.plugin = 'nginx-plus'
        emit_value.values = [metric_record.value]
        emit_value.type = metric_record.type
        emit_value.type_instance = metric_record.name
        emit_value.plugin_instance = metric_record.instance_id
        emit_value.plugin_instance += '[{}]'.format(self._format_dimensions(metric_record.dimensions))

        # With some versions of CollectD, a dummy metadata map must to be added
        # to each value for it to be correctly serialized to JSON by the
        # write_http plugin. See
        # https://github.com/collectd/collectd/issues/716
        emit_value.meta = {'true': 'true'}

        emit_value.dispatch()

    def _format_dimensions(self, dimensions):
        '''
        Formats a dictionary of key/value pairs as a comma-delimited list of key=value tokens.
        This was copied from docker-collectd-plugin.
        '''
        return ','.join(['='.join((key.replace('.', '_'), value)) for key, value in dimensions.iteritems()])

# Server configuration flags
STATUS_HOST = 'StatusHost'
STATUS_PORT = 'StatusPort'
DEBUG_LOG_LEVEL = 'DebugLogLevel'
USERNAME = 'Username'
PASSWORD = 'Password'
DIMENSION = 'Dimension'
DIMENSIONS = 'Dimensions' # Not publicly facing, used to support neo-agent auto-generated configs
API_VERSION = 'APIVersion'
API_BASE_PATH = 'APIBasePath'

# Metric group configuration flags
SERVER_ZONE = 'ServerZone'
MEMORY_ZONE = 'MemoryZone'
UPSTREAM = 'Upstream'
CACHE = 'Cache'
STREAM_SERVER_ZONE = 'StreamServerZone'
STREAM_UPSTREAM = 'StreamUpstream'
PROCESSES = 'Processes'

# Constants
DEFAULT_API_VERSION = 1

# Metric groups
DEFAULT_CONNECTION_METRICS = [
    MetricDefinition('connections.accepted', 'counter', 'accepted'),
    MetricDefinition('connections.dropped', 'counter', 'dropped'),
    MetricDefinition('connections.idle', 'gauge', 'idle'),
    MetricDefinition('connections.active', 'gauge', 'active')
]

DEFAULT_SSL_METRICS = [
    MetricDefinition('ssl.handshakes.successful', 'counter', 'handshakes'),
    MetricDefinition('ssl.handshakes.failed', 'counter', 'handshakes_failed'),
    MetricDefinition('ssl.sessions.reuses', 'counter', 'session_reuses')
]

DEFAULT_REQUESTS_METRICS = [
    MetricDefinition('requests.total', 'counter', 'total'),
    MetricDefinition('requests.current', 'gauge', 'current')
]

DEFAULT_SERVER_ZONE_METRICS = [
    MetricDefinition('server.zone.requests', 'counter', 'requests'),
    MetricDefinition('server.zone.responses.1xx', 'counter', 'responses.1xx'),
    MetricDefinition('server.zone.responses.2xx', 'counter', 'responses.2xx'),
    MetricDefinition('server.zone.responses.3xx', 'counter', 'responses.3xx'),
    MetricDefinition('server.zone.responses.4xx', 'counter', 'responses.4xx'),
    MetricDefinition('server.zone.responses.5xx', 'counter', 'responses.5xx'),
    MetricDefinition('server.zone.responses.total', 'counter', 'responses.total'),
    MetricDefinition('server.zone.bytes.received', 'counter', 'received'),
    MetricDefinition('server.zone.bytes.sent', 'counter', 'sent')
]

DEFAULT_UPSTREAM_METRICS = [
    MetricDefinition('upstreams.requests', 'counter', 'requests'),
    MetricDefinition('upstreams.responses.1xx', 'counter', 'responses.1xx'),
    MetricDefinition('upstreams.responses.2xx', 'counter', 'responses.2xx'),
    MetricDefinition('upstreams.responses.3xx', 'counter', 'responses.3xx'),
    MetricDefinition('upstreams.responses.4xx', 'counter', 'responses.4xx'),
    MetricDefinition('upstreams.responses.5xx', 'counter', 'responses.5xx'),
    MetricDefinition('upstreams.responses.total', 'counter', 'responses.total'),
    MetricDefinition('upstreams.downtime', 'counter', 'downtime'),
    MetricDefinition('upstreams.response.time', 'gauge', 'response_time'),
    MetricDefinition('upstreams.bytes.received', 'counter', 'received'),
    MetricDefinition('upstreams.bytes.sent', 'counter', 'sent')
]

DEFAULT_CACHE_METRICS = [
    MetricDefinition('caches.size', 'gauge', 'size'),
    MetricDefinition('caches.size.max', 'gauge', 'max_size')
]

SERVER_ZONE_METRICS = [
    MetricDefinition('server.zone.processing', 'counter', 'processing'),
    MetricDefinition('server.zone.discarded', 'counter', 'discarded')
]

MEMORY_ZONE_METRICS = [
    MetricDefinition('zone.pages.used', 'counter', 'pages.used'),
    MetricDefinition('zone.pages.free', 'counter', 'pages.free')
]

# Metrics taken from the top-level upstream object (the peers container)
UPSTREAM_METRICS = [
    MetricDefinition('upstreams.keepalive', 'gauge', 'keepalive'),
    MetricDefinition('upstreams.zombies', 'gauge', 'zombies')
]

# Metrics taken from each upstream peer
UPSTREAM_PEER_METRICS = [
    MetricDefinition('upstreams.active', 'counter', 'active'),
    MetricDefinition('upstreams.fails', 'counter', 'fails'),
    MetricDefinition('upstreams.unavailable', 'counter', 'unavail'),
    MetricDefinition('upstreams.health.checks.checks', 'counter', 'health_checks.checks'),
    MetricDefinition('upstreams.health.checks.fails', 'counter', 'health_checks.fails'),
    MetricDefinition('upstreams.health.checks.unhealthy', 'counter', 'health_checks.unhealthy'),
    MetricDefinition('upstreams.header.time', 'gauge', 'header_time')
]

CACHE_METRICS = [
    MetricDefinition('caches.hit.responses', 'counter', 'hit.responses'),
    MetricDefinition('caches.miss.responses', 'counter', 'miss.responses'),
    MetricDefinition('caches.stale.responses', 'counter', 'stale.responses'),
    MetricDefinition('caches.updating.responses', 'counter', 'updating.responses'),
    MetricDefinition('caches.revalidated.responses', 'counter', 'revalidated.responses'),
    MetricDefinition('caches.expired.responses', 'counter', 'expired.responses'),
    MetricDefinition('caches.bypass.responses', 'counter', 'bypass.responses'),
    MetricDefinition('caches.hit.bytes', 'counter', 'hit.bytes'),
    MetricDefinition('caches.miss.bytes', 'counter', 'miss.bytes'),
    MetricDefinition('caches.stale.bytes', 'counter', 'stale.bytes'),
    MetricDefinition('caches.updating.bytes', 'counter', 'updating.bytes'),
    MetricDefinition('caches.revalidated.bytes', 'counter', 'revalidated.bytes'),
    MetricDefinition('caches.expired.bytes', 'counter', 'expired.bytes'),
    MetricDefinition('caches.bypass.bytes', 'counter', 'bypass.bytes'),
    MetricDefinition('caches.miss.responses.written', 'counter', 'miss.responses_written'),
    MetricDefinition('caches.miss.bytes.written', 'counter', 'miss.bytes_written'),
    MetricDefinition('caches.expired.responses.written', 'counter', 'expired.responses_written'),
    MetricDefinition('caches.expired.bytes.written', 'counter', 'expired.bytes_written'),
    MetricDefinition('caches.bypass.responses.written', 'counter', 'bypass.responses_written'),
    MetricDefinition('caches.bypass.bytes.written', 'counter', 'miss.bytes_written')
]

STREAM_SERVER_ZONE_METRICS = [
    MetricDefinition('stream.server.zone.connections', 'counter', 'connections'),
    MetricDefinition('stream.server.zone.processing', 'counter', 'processing'),
    MetricDefinition('stream.server.zone.sessions.2xx', 'counter', 'sessions.2xx'),
    MetricDefinition('stream.server.zone.sessions.4xx', 'counter', 'sessions.4xx'),
    MetricDefinition('stream.server.zone.sessions.5xx', 'counter', 'sessions.5xx'),
    MetricDefinition('stream.server.zone.received', 'counter', 'received'),
    MetricDefinition('stream.server.zone.sent', 'counter', 'sent'),
    MetricDefinition('stream.server.zone.discarded', 'counter', 'discarded')
]

# Metrics taken from each strea-upstream object (the peers container)
STREAM_UPSTREAM_METRICS = [
    MetricDefinition('stream.upstreams.zombies', 'gauge', 'zombies')
]

# Metrics take from each stream-upstream peer
STREAM_UPSTREAM_PEER_METRICS = [
    MetricDefinition('stream.upstreams.connections', 'counter', 'connections'),
    MetricDefinition('stream.upstreams.active', 'counter', 'active'),
    MetricDefinition('stream.upstreams.connections.max', 'counter', 'max_conns'),
    MetricDefinition('stream.upstreams.bytes.sent', 'counter', 'sent'),
    MetricDefinition('stream.upstreams.bytes.received', 'counter', 'received'),
    MetricDefinition('stream.upstreams.fails', 'counter', 'fails'),
    MetricDefinition('stream.upstreams.unavailable', 'counter', 'unavail'),
    MetricDefinition('stream.upstreams.health.checks.checks', 'counter', 'health_checks.checks'),
    MetricDefinition('stream.upstreams.health.checks.fails', 'counter', 'health_checks.fails'),
    MetricDefinition('stream.upstreams.health.checks.unhealthy', 'counter', 'health_checks.unhealthy'),
    MetricDefinition('stream.upstreams.response.time', 'gauge', 'response_time'),
    MetricDefinition('stream.upstreams.downtime', 'counter', 'downtime')
]

PROCESSES_METRICS = [
    MetricDefinition('processes.respawned', 'counter', 'respawned'),
]

class NginxPlusPlugin(object):
    '''
    Collectd plugin for reporting metrics from a single NGINX+ instance.
    '''
    def __init__(self):
        self.nginx_agent = None
        self.sink = None
        self.emitters = []
        self.global_dimensions = {}

        self._instance_id = None

    @property
    def instance_id(self):
        if not self._instance_id:
            nginx_ip = self.nginx_agent.get_nginx_address()
            if nginx_ip:
                self._instance_id = '{}:{}'.format(nginx_ip, str(self.nginx_agent.status_port))
        return self._instance_id

    def configure(self, conf):
        '''
        Configure the plugin with the configuration provided by collectd.
        '''
        LOGGER.info('Starting plugin configuration')

        status_host = None
        status_port = None
        username = None
        password = None
        api_version = None
        api_base_path = None

        # Iterate the configuration values, pickup the status endpoint info
        # and create any specified opt-in metric emitters
        for node in conf.children:
            if node.key == STATUS_HOST:
                status_host = node.values[0]
            elif node.key == STATUS_PORT:
                status_port = node.values[0]
            elif node.key == USERNAME:
                username = node.values[0]
            elif node.key == PASSWORD:
                password = node.values[0]
            elif node.key == API_VERSION:
                err_msg = "{err}, please provide a valid positive integer value for the APIVersion"
                try:
                    api_version = int(node.values[0])

                    if api_version < 0:
                        raise ValueError("Invalid value found: {}".format(node.values[0]))
                except Exception as e:
                    raise type(e)(err_msg.format(err=e))
            elif node.key == API_BASE_PATH:
                    api_base_path = node.values[0]
            elif node.key == DIMENSIONS:
                # The DIMENSIONS configuration property used to include dimensions represented as single string
                # in the format: key_1=value-1,key_2=value_2
                # We need this alternative path for specifying dimensions to support the auto-generated plugin
                # configurations from neo-agent.
                # The single DIMENSION configuration entries are easier for humans to work with and is the documented
                # format for specifying additional dimensions
                self.global_dimensions.update(self._dimensions_str_to_dict(node.values[0]))
            elif node.key == DIMENSION and len(node.values) == 2:
                self.global_dimensions[node.values[0]] = node.values[1]
            elif self._check_bool_config_enabled(node, DEBUG_LOG_LEVEL):
                log_handler.debug = self._str_to_bool(node.values[0])
            elif self._check_bool_config_enabled(node, CACHE):
                self._log_emitter_group_enabled(CACHE)
                self.emitters.append(MetricEmitter(self._emit_cache_metrics, CACHE_METRICS))
            elif self._check_bool_config_enabled(node, PROCESSES):
                self._log_emitter_group_enabled(PROCESSES)
                self.emitters.append(MetricEmitter(self._emit_processes_metrics, PROCESSES_METRICS))
            elif self._check_bool_config_enabled(node, UPSTREAM):
                self._log_emitter_group_enabled(UPSTREAM)
                self.emitters.append(MetricEmitter(self._emit_upstreams_metrics, UPSTREAM_METRICS))
                self.emitters.append(MetricEmitter(self._emit_upstreams_peer_metrics, UPSTREAM_PEER_METRICS))
            elif self._check_bool_config_enabled(node, MEMORY_ZONE):
                self._log_emitter_group_enabled(MEMORY_ZONE)
                self.emitters.append(MetricEmitter(self._emit_memory_zone_metrics, MEMORY_ZONE_METRICS))
            elif self._check_bool_config_enabled(node, SERVER_ZONE):
                self._log_emitter_group_enabled(SERVER_ZONE)
                self.emitters.append(MetricEmitter(self._emit_server_zone_metrics, SERVER_ZONE_METRICS))
            elif self._check_bool_config_enabled(node, STREAM_UPSTREAM):
                self._log_emitter_group_enabled(STREAM_UPSTREAM)
                self.emitters.append(MetricEmitter(self._emit_stream_upstreams_metrics, STREAM_UPSTREAM_METRICS))
                self.emitters.append(MetricEmitter(self._emit_stream_upstreams_peer_metrics,\
                                                   STREAM_UPSTREAM_PEER_METRICS))
            elif self._check_bool_config_enabled(node, STREAM_SERVER_ZONE):
                self._log_emitter_group_enabled(STREAM_SERVER_ZONE)
                self.emitters.append(MetricEmitter(self._emit_stream_server_zone_metrics, STREAM_SERVER_ZONE_METRICS))

        # Default metric emitters
        self.emitters.append(MetricEmitter(self._emit_connection_metrics, DEFAULT_CONNECTION_METRICS))
        self.emitters.append(MetricEmitter(self._emit_ssl_metrics, DEFAULT_SSL_METRICS))
        self.emitters.append(MetricEmitter(self._emit_requests_metrics, DEFAULT_REQUESTS_METRICS))
        self.emitters.append(MetricEmitter(self._emit_server_zone_metrics, DEFAULT_SERVER_ZONE_METRICS))
        self.emitters.append(MetricEmitter(self._emit_upstreams_peer_metrics, DEFAULT_UPSTREAM_METRICS))
        self.emitters.append(MetricEmitter(self._emit_cache_metrics, DEFAULT_CACHE_METRICS))

        self.sink = MetricSink()
        self.nginx_agent = NginxStatusAgent(status_host, status_port, username, password, api_version, api_base_path)

        LOGGER.debug('Finished configuration. Will read status from %s:%s', status_host, status_port)

    def read(self):
        '''
        Called to emit the actual metrics.
        Called once per interval (see Interval configuration option of collectd).
        If an exception is thrown the plugin will be skipped for an
        increasing amount of time until it returns to normal.
        '''
        if not self.instance_id:
            LOGGER.warning('Skipping read, instance id is not set')
            return

        LOGGER.debug('Instance %s starting read', self.instance_id)

        self.nginx_agent.validate_nginx_version()

        self._reload_ephemeral_global_dimensions()

        for emitter in self.emitters:
            emitter.emit(self.sink)

    def _emit_connection_metrics(self, metrics, sink):
        '''
        Extract and emit the connection metrics.
        '''
        LOGGER.debug('Emitting connection metrics, instance: %s', self.instance_id)

        status_json = self.nginx_agent.get_connections()
        self._fetch_and_emit_metrics(status_json, metrics, sink)

    def _emit_ssl_metrics(self, metrics, sink):
        '''
        Extract and emit the ssl metrics.
        '''
        LOGGER.debug('Emitting ssl metrics, instance: %s', self.instance_id)

        status_json = self.nginx_agent.get_ssl()
        self._fetch_and_emit_metrics(status_json, metrics, sink)

    def _emit_requests_metrics(self, metrics, sink):
        '''
        Extract and emit the requests metrics.
        '''
        LOGGER.debug('Emitting requests metrics, instance: %s', self.instance_id)

        status_json = self.nginx_agent.get_requests()
        self._fetch_and_emit_metrics(status_json, metrics, sink)

    def _emit_processes_metrics(self, metrics, sink):
        '''
        Extract and emit the processes metrics.
        '''
        LOGGER.debug('Emitting processes metrics, instance: %s', self.instance_id)

        status_json = self.nginx_agent.get_processes()
        self._fetch_and_emit_metrics(status_json, metrics, sink)

    def _emit_server_zone_metrics(self, metrics, sink):
        '''
        Extract and emit the server-zone metrics.
        '''
        LOGGER.debug('Emitting server-zone metrics, instance: %s', self.instance_id)

        server_zones_obj = self.nginx_agent.get_server_zones()
        self._build_container_keyed_metrics(server_zones_obj, 'server.zone.name', metrics, sink)

    def _emit_upstreams_metrics(self, metrics, sink):
        '''
        Extract and emit the upstreams metrics.
        '''
        LOGGER.debug('Emitting upstreams metrics, instance: %s', self.instance_id)

        upstreams_obj = self.nginx_agent.get_upstreams()
        self._build_container_keyed_metrics(upstreams_obj, 'upstream.name', metrics, sink)

    def _emit_upstreams_peer_metrics(self, metrics, sink):
        '''
        Extract and emit the upstreams peer metrics.
        '''
        LOGGER.debug('Emitting upstreams peer metrics, instance: %s', self.instance_id)

        upstreams_obj = self.nginx_agent.get_upstreams()
        self._build_container_keyed_peer_metrics(upstreams_obj, 'upstream.name', 'upstream.peer.name', metrics, sink)

    def _emit_stream_server_zone_metrics(self, metrics, sink):
        '''
        Extract and emit the stream-server-zone metrics.
        '''
        LOGGER.debug('Emitting stream-server-zone metrics, instance: %s', self.instance_id)

        server_zones_obj = self.nginx_agent.get_stream_server_zones()
        self._build_container_keyed_metrics(server_zones_obj, 'stream.server.zone.name', metrics, sink)

    def _emit_stream_upstreams_metrics(self, metrics, sink):
        '''
        Extract and emit the stream-upstream metrics.
        '''
        LOGGER.debug('Emitting stream-upstreams metrics, instance: %s', self.instance_id)

        upstreams_obj = self.nginx_agent.get_stream_upstreams()
        self._build_container_keyed_metrics(upstreams_obj, 'stream.upstream.name', metrics, sink)

    def _emit_stream_upstreams_peer_metrics(self, metrics, sink):
        '''
        Extract and emit the stream-upstream peer metrics.
        '''
        LOGGER.debug('Emitting stream-upstreams peer metrics, instance: %s', self.instance_id)

        upstreams_obj = self.nginx_agent.get_stream_upstreams()
        self._build_container_keyed_peer_metrics(upstreams_obj, 'stream.upstream.name', 'stream.upstream.peer.name',\
            metrics, sink)

    def _emit_memory_zone_metrics(self, metrics, sink):
        '''
        Extract and emit the memory zone metrics.
        '''
        LOGGER.debug('Emitting memory-zone metrics, instance: %s', self.instance_id)

        slab_obj = self.nginx_agent.get_slabs()
        self._build_container_keyed_metrics(slab_obj, 'memory.zone.name', metrics, sink)

    def _emit_cache_metrics(self, metrics, sink):
        '''
        Extract and emit the cache metrics.
        '''
        LOGGER.debug('Emitting cache metrics, instance: %s', self.instance_id)

        cache_obj = self.nginx_agent.get_caches()
        self._build_container_keyed_metrics(cache_obj, 'cache.name', metrics, sink)

    def _build_container_keyed_metrics(self, containers_obj, container_dim_name, metrics, sink):
        '''
        Build metrics with a single dimension: the name of the top level object.

        Multiple metric groups (server zone, cache, etc.) are given in the format:
        {
            ...
            "my_server_zone_name" : {
                "value" : 87
            }
            ...
        }

        In the above example, the dimension value would be "my_server_zone_name".

        Example:
            Args:
                containers_obj: the above object
                container_dim_name: "server.zone.name"
                metrics: [MetricDefinition('server.zone.value', 'counter', 'value')]

            Produces:
                MetricRecord('server.zone.value', 'counter', 87, self.instance_id,
                    {'server.zone.name' : 'my_server_zone_name'})
        '''
        if containers_obj:
            for container_name, container in containers_obj.iteritems():
                dimensions = {container_dim_name : container_name}
                self._fetch_and_emit_metrics(container, metrics, sink, dimensions)

    def _build_container_keyed_peer_metrics(self, containers_obj, container_dim_name, peer_dim_name, metrics, sink):
        '''
        Build metrics with two dimensions: name of the top level object and the name of each constituent object (peer).

        Upstream metrics are given in the format:
        {
            ...
            "my_upstream_name" : {
                "peers" : [
                    {
                        "name" : "foo",
                        "value" : 5
                    },
                    {
                        "name" : "bar",
                        "value" : 27
                    }
                ]
            }
            ...
        }
        The "container" name in the above example is "my_upstream_name" and the "peer"
        names are "foo" and "bar".

        This method builds metrics that are scoped to a single peer, but should
        include the container name as a dimension.

        Example:
            Args:
                containers_obj: the above object
                container_dim_name: "upstream.name"
                peer_dim_name: "upstream.peer.name"
                metrics: [MetricDefinition('upstreams.value', 'counter', 'value')]

            Produces:
                MetricRecord('upstreams.value', 'counter', 5, self.instance_id,
                    {'upstream.name' : 'my_upstream_name', 'upstream.peer.name' : 'foo'})

                MetricRecord('upstreams.value', 'counter', 27, self.instance_id,
                    {'upstream.name' : 'my_upstream_name'', 'upstream.peer.name' : 'bar'})
        '''
        if containers_obj:
            # Each key in the container object is the name of the container
            for container_name, container in containers_obj.iteritems():
                # Each container is has multiple peer servers, this is where the metric values are pulled from
                for peer in container['peers']:
                    # Get the dimensions from each peer server
                    dimensions = {container_dim_name : container_name, peer_dim_name : _reduce_to_path(peer, 'name')}
                    self._fetch_and_emit_metrics(peer, metrics, sink, dimensions)

    def _fetch_and_emit_metrics(self, scoped_obj, metrics, sink, dimensions=None):
        '''
        For each metric the value is extracted from the given object and emitted
        with the specified dimensions using the given sink. The current time will
        be passed in on the emit.

        Any global dimensions will be applied to the given dimensions.
        '''
        for metric in metrics:
            value = _reduce_to_path(scoped_obj, metric.scoped_object_key)
            if value is not None:
                updated_dims = dimensions.copy() if dimensions else {}
                updated_dims.update(self.global_dimensions)
                sink.emit(MetricRecord(metric.name, metric.type, value, self.instance_id, updated_dims, time.time()))

    def _reload_ephemeral_global_dimensions(self):
        '''
        Reload any global dimensions that have the potential to change after configuration.
        '''
        # Anticipate the nginx instance being upgraded between reads
        self.global_dimensions['nginx.version'] = self.nginx_agent.get_nginx_version()

    def _check_bool_config_enabled(self, config_node, key):
        '''
        Convenience method to check if a collectd Config node contains the given
        key and if that key's value is a True bool.
        '''
        return config_node.key == key and self._str_to_bool(config_node.values[0])

    def _dimensions_str_to_dict(self, dimensions_str):
        dimensions = {}
        for key_pair in dimensions_str.split(','):
            key_pair_split = key_pair.split('=')
            if len(key_pair_split) == 2:
                dimensions[key_pair_split[0]] = key_pair_split[1]
            else:
                LOGGER.warning('Malformed dimension key=value pair: %s', key_pair)
        return dimensions

    def _str_to_bool(self, value):
        '''
        Python 2.x does not have a casting mechanism for booleans.  The built in
        bool() will return true for any string with a length greater than 0.  It
        does not cast a string with the text "true" or "false" to the
        corresponding bool value.  This method is a casting function.  It is
        insensitive to case and leading/trailing spaces.  An Exception is raised
        if a cast can not be made.

        This was copied from docker-collectd-plugin.py
        '''
        value = str(value).strip().lower()
        if value == 'true':
            return True
        elif value == 'false':
            return False
        else:
            raise ValueError('Unable to cast value (%s) to boolean' % value)

    def _log_emitter_group_enabled(self, emitter_group):
        LOGGER.debug('%s enabled, adding emitters', emitter_group)

class NginxPlusPluginManager(object):
    '''
    Class to create, configure and manage instances of NginxPlusPlugin.
    The config and read methods of this class will be registered with collectd,
    proxying to the configure and read methods of the plugin instances it is composed of.
    '''
    def __init__(self):
        self.plugins = []

    def config_callback(self, conf):
        '''
        Create and configure an instance of NginxPlusPlugin.
        The created plugin will be added to the list of plugins
        managed by this instance.
        '''
        plugin = NginxPlusPlugin()
        plugin.configure(conf)

        self.plugins.append(plugin)

    def read_callback(self):
        '''
        Called to emit the actual metrics.
        Called once per interval (see Interval configuration option of collectd)
        on each instance of NginxPlusPlugin managed by this instance.
        If an exception is thrown the plugin will be skipped for an
        increasing amount of time until it returns to normal.
        '''
        for plugin in self.plugins:
            plugin.read()

def _reduce_to_path(obj, path):
    '''
    Traverses the given object down the specified "." delineated, returning the
    value named by the last path segment.
    Example:
        To get "bat" from the below object
            {
                "foo" : {
                    "bar" : {
                        "bat" : "something_important"
                    }
                }
            }
        use the path: "foo.bar.bat"

    If the path is invalid None will be returned.
    Copied from collectd-elasticsearch
    '''
    try:
        if isinstance(path, basestring):
            path = path.split('.')
        return reduce(lambda x, y: x[y], path, obj)
    except Exception:
        sys.exc_clear()
    return None


class NginxStatusAgent(object):
    '''
    Helper class for interacting with a single NGINX+ instance.
    '''
    def __init__(self, status_host=None, status_port=None, username=None, password=None, api_version=None, api_base_path=None):
        self.status_host = status_host or 'localhost'
        self.status_port = status_port or 8080
        self.auth_tuple = (username, password) if username or password else None
        self.api_version = api_version
        self.api_base_path = api_base_path

        if self.api_version is None:
            detected_api_version = self._get_api_version()
            if detected_api_version is not None:
                self.api_version = detected_api_version

        # set the default path in case of no user input
        if self.api_base_path is None:
            if self.api_version is None:
                self.api_base_path = "/status"
            else:
                self.api_base_path = "/api"

        # initialize the API URLs as per the API type(legacy or newer)
        if self.api_version is None:
            self._initialize_legacy_api_urls()
        else:
            self._initialize_newer_api_urls()

        # save the initial version to detect the version change at run time
        self.nginx_version = self.get_nginx_version()

    def get_status(self):
        '''
        Fetch the status summary for every component.
        '''
        return self._send_get(self.base_status_url)

    def get_connections(self):
        '''
        Fetch the connections status summary.
        '''
        return self._send_get(self.connections_url)

    def get_requests(self):
        '''
        Fetch the requests status summary.
        '''
        return self._send_get(self.requests_url)

    def get_ssl(self):
        '''
        Fetch the ssl status summary.
        '''
        return self._send_get(self.ssl_url)

    def get_slabs(self):
        '''
        Fetch the memory slabs status summary.
        '''
        return self._send_get(self.slabs_url)

    def get_nginx_version(self):
        '''
        Fetch the version of nginx+.
        Note, this will only return the value, not a dict.
        '''
        if self.api_version is not None:
            json_response = self._send_get(self.nginx_metadata_url)
            if isinstance(json_response, dict):
                return json_response.get('version', None)

            LOGGER.error("Unexpected response of type: %s from %s", type(json_response), self.nginx_metadata_url)

            return None

        return self._send_get(self.nginx_version_url)

    def get_nginx_address(self):
        '''
        Fetch the address of the nginx+ instance.
        Note, this will only return the value, not a dict.
        '''
        if self.api_version is not None:
            json_response = self._send_get(self.nginx_metadata_url)
            if isinstance(json_response, dict):
                return json_response.get('address', None)

            LOGGER.error("Unexpected response of type: %s from %s", type(json_response), self.nginx_metadata_url)

            return None

        return self._send_get(self.address_url)

    def get_caches(self):
        '''
        Fetch the caches status summary.
        '''
        return self._send_get(self.caches_url)

    def get_server_zones(self):
        '''
        Fetch the server-zones status summary.
        '''
        return self._send_get(self.server_zones_url)

    def get_upstreams(self):
        '''
        Fetch the upstreams status summary.
        '''
        return self._send_get(self.upstreams_url)

    def get_stream_upstreams(self):
        '''
        Fetch the stream upstreams status summary.
        '''
        return self._send_get(self.stream_upstream_url)

    def get_stream_server_zones(self):
        '''
        Fetch the stream server zones status summary.
        '''
        return self._send_get(self.stream_server_zones_url)

    def get_processes(self):
        '''
        Fetch the processes status summary.
        '''
        return self._send_get(self.processes_url)

    def _get_api_version(self):
        '''
        Determines whether the Nginx-plus plugin has a versioned API or legacy API.
        '''
        newer_api_base_path = self.api_base_path if self.api_base_path is not None else '/api'
        legacy_api_base_path = self.api_base_path if self.api_base_path is not None else '/status'
        base_url = 'http://{}:{}'.format(self.status_host, str(self.status_port))

        try:
            response = requests.get("{}{}/{}".format(base_url, newer_api_base_path, DEFAULT_API_VERSION), auth=self.auth_tuple)
            if response.status_code == requests.codes.ok:
                return DEFAULT_API_VERSION
            else:
                response = requests.get("{}{}".format(base_url, legacy_api_base_path), auth=self.auth_tuple)
                if response.status_code == requests.codes.ok:
                    return None
            raise RuntimeError(
                "Failed to detect the Nginx-plus API type (versioned or legacy), please check your input configuration.")
        except RequestException as e:
            raise RequestException("Failed to detect the Nginx-plus API type (versioned or legacy), due to the error: %s", e)

    def validate_nginx_version(self):
        '''
        Detects the change in the Nginx version and raise an error in case of a version change or unable to get the version
        '''
        cur_nginx_version = self.get_nginx_version()

        if cur_nginx_version is None:
            raise RuntimeError("Unable to get the Nginx version")

        if self.nginx_version != cur_nginx_version:
            raise RuntimeError("Nginx version change detected from {} to {}".format(self.nginx_version, cur_nginx_version))

    def _send_get(self, url):
        '''
        Performs a GET against the given url.
        '''
        status = None
        try:
            response = requests.get(url, auth=self.auth_tuple)
            if response.status_code == requests.codes.ok:
                status = response.json()
            else:
                LOGGER.error('Unexpected status code: %s, received from %s', response.status_code, url)
        except RequestException as e:
            LOGGER.exception('Failed request to %s. %s', self.base_status_url, e)
        return status

    def _initialize_newer_api_urls(self):
        '''
        Initialize the newer API URL
        '''
        self.base_status_url = 'http://{}:{}{}/{}'.format(self.status_host, str(self.status_port), self.api_base_path, str(self.api_version))
        self.nginx_metadata_url = '{}/nginx'.format(self.base_status_url)
        self.caches_url = '{}/http/caches'.format(self.base_status_url)
        self.server_zones_url = '{}/http/server_zones'.format(self.base_status_url)
        self.upstreams_url = '{}/http/upstreams'.format(self.base_status_url)
        self.stream_upstream_url = '{}/stream/upstreams'.format(self.base_status_url)
        self.stream_server_zones_url = '{}/stream/server_zones'.format(self.base_status_url)
        self.connections_url = '{}/connections'.format(self.base_status_url)
        self.requests_url = '{}/http/requests'.format(self.base_status_url)
        self.ssl_url = '{}/ssl'.format(self.base_status_url)
        self.slabs_url = '{}/slabs'.format(self.base_status_url)
        self.processes_url = '{}/processes'.format(self.base_status_url)

    def _initialize_legacy_api_urls(self):
        '''
        Initialize the legacy API URL
        '''
        self.base_status_url = 'http://{}:{}{}'.format(self.status_host, str(self.status_port), self.api_base_path)
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


class CollectdLogHandler(logging.Handler):
    '''
    Log handler to forward statements to collectd

    A custom log handler that forwards log messages raised
    at level debug, info, warning, and error
    to collectd's built in logging.  Suppresses extraneous
    info and debug statements using a "verbose" boolean

    Inherits from logging.Handler
    This was copied from docker-collectd-plugin.py

    Arguments
        plugin_name -- name of the plugin (default 'unknown')
        verbose -- enable/disable verbose messages (default False)
    '''

    def __init__(self, plugin_name='unknown', debug=False):
        '''
        Initializes CollectdLogHandler
        Arguments
            plugin_name -- string name of the plugin (default 'unknown')
            debug  -- boolean to enable debug level logging, defaults to false
        '''
        self.plugin_name = plugin_name
        self.debug = debug

        logging.Handler.__init__(self, level=logging.NOTSET)

    def emit(self, record):
        '''
        Emits a log record to the appropriate collectd log function

        Arguments
        record -- str log record to be emitted
        '''
        try:
            if record.msg is not None:
                if record.levelname == 'ERROR':
                    collectd.error(self.format(record))
                elif record.levelname == 'WARNING':
                    collectd.warning(self.format(record))
                elif record.levelname == 'INFO':
                    collectd.info(self.format(record))
                elif record.levelname == 'DEBUG' and self.debug:
                    collectd.debug(self.format(record))
        except Exception as e:
            collectd.warning(('{p} [ERROR]: Failed to write log statement due '
                              'to: {e}').format(p=self.plugin_name, e=e))


class CollectdMock(object):
    '''
    Mock of the collectd module.

    This is used when running the plugin locally.
    All log messages are printed to stdout.
    The Values() method will return an instance of CollectdValuesMock
    '''
    def __init__(self):
        self.value_mock = CollectdValuesMock

    def debug(self, msg):
        print msg

    def info(self, msg):
        print msg

    def notice(self, msg):
        print msg

    def warning(self, msg):
        print msg

    def error(self, msg):
        print msg

    def Values(self):
        return (self.value_mock)()


class CollectdValuesMock(object):
    '''
    Mock of the collectd Values class.

    Instanes of this class are returned by CollectdMock, which is used to mock
    collectd when running locally.
    The dispatch() method will print the emitted record to stdout.
    '''
    def dispatch(self):
        if not getattr(self, 'host', None):
            self.host = os.environ.get('COLLECTD_HOSTNAME', 'localhost')

        identifier = '%s/%s' % (self.host, self.plugin)
        if getattr(self, 'plugin_instance', None):
            identifier += '-' + self.plugin_instance
        identifier += '/' + self.type

        if getattr(self, 'type_instance', None):
            identifier += '-' + self.type_instance

        print '[PUTVAL]', identifier, ':'.join(map(str, [int(self.time)] + self.values))

    def __str__(self):
        attrs = []
        for name in dir(self):
            if not name.startswith('_') and name != 'dispatch':
                attrs.append("{}={}".format(name, getattr(self, name)))
        return "<CollectdValues {}>".format(' '.join(attrs))

class CollectdConfigMock(object):
    '''
    Mock of the collectd Config class.

    This class is used to configure the plugin when running locally.
    The children field is expected to be a list of CollectdConfigChildMock.
    '''
    def __init__(self, children=None):
        self.children = children or []

class CollectdConfigChildMock(object):
    '''
    Mock of the collectd Conf child class.

    This class is used to mock key:value pairs normally pulled from the plugin
    configuration file.
    '''
    def __init__(self, key, values):
        self.key = key
        self.values = values


# Set up logging
LOG_FILE_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
LOG_FILE_MESSAGE_FORMAT = '[%(levelname)s] [nginx-plus-collectd] [%(asctime)s UTC]: %(message)s'
formatter = logging.Formatter(fmt=LOG_FILE_MESSAGE_FORMAT, datefmt=LOG_FILE_DATE_FORMAT)
log_handler = CollectdLogHandler('nginx-plus-collectd', False)
log_handler.setFormatter(formatter)
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
LOGGER.propagate = False
LOGGER.addHandler(log_handler)

if __name__ == '__main__':
    kwargs = dict(arg.split('=') for arg in sys.argv[1:])
    cli_status_host = kwargs['host'] if kwargs.get('host', None) else 'demo.nginx.com'
    cli_status_port = kwargs['port'] if kwargs.get('port', None) else 80
    cli_api_version = kwargs.get('api_version', None)
    cli_api_base_path = kwargs.get('api_base_path', None)

    collectd = CollectdMock()

    mock_config_ip_child = CollectdConfigChildMock(STATUS_HOST, [cli_status_host])
    mock_config_port_child = CollectdConfigChildMock(STATUS_PORT, [cli_status_port])
    mock_config_debug_log_level = CollectdConfigChildMock(DEBUG_LOG_LEVEL, ['true'])

    mock_config_username = CollectdConfigChildMock(USERNAME, ['user1'])
    mock_config_password = CollectdConfigChildMock(PASSWORD, ['test'])

    mock_config_dimension = CollectdConfigChildMock(DIMENSION, ['foo', 'bar'])
    mock_config_dimensions = CollectdConfigChildMock(DIMENSIONS, ['bat=baz'])


    # Setup the mock config to enable all metric groups
    mock_config_server_zone_child = CollectdConfigChildMock(SERVER_ZONE, ['true'])
    mock_config_memory_zone_child = CollectdConfigChildMock(MEMORY_ZONE, ['true'])
    mock_config_upstream_child = CollectdConfigChildMock(UPSTREAM, ['true'])
    mock_config_cache_child = CollectdConfigChildMock(CACHE, ['true'])
    mock_config_stream_server_zone_child = CollectdConfigChildMock(STREAM_SERVER_ZONE, ['true'])
    mock_config_stream_upstream_child = CollectdConfigChildMock(STREAM_UPSTREAM, ['true'])
    mock_config_processes_child = CollectdConfigChildMock(PROCESSES, ['true'])

    mock_config_input_list = [mock_config_ip_child,
                                mock_config_port_child,
                                mock_config_debug_log_level,
                                mock_config_server_zone_child,
                                mock_config_memory_zone_child,
                                mock_config_upstream_child,
                                mock_config_cache_child,
                                mock_config_stream_server_zone_child,
                                mock_config_stream_upstream_child,
                                mock_config_username,
                                mock_config_password,
                                mock_config_dimension,
                                mock_config_dimensions,
                                mock_config_processes_child]

    if cli_api_version is not None:
        mock_config_api_version = CollectdConfigChildMock(API_VERSION, [cli_api_version])
        mock_config_input_list.append(mock_config_api_version)

    if cli_api_base_path is not None:
        mock_config_api_base_path = CollectdConfigChildMock(API_BASE_PATH, [cli_api_base_path])
        mock_config_input_list.append(mock_config_api_base_path)

    mock_config = CollectdConfigMock(mock_config_input_list)

    plugin_manager = NginxPlusPluginManager()
    plugin_manager.config_callback(mock_config)

    while True:
        plugin_manager.read_callback()
        time.sleep(5)
else:
    import collectd

    plugin_manager = NginxPlusPluginManager()

    collectd.register_config(plugin_manager.config_callback)
    collectd.register_read(plugin_manager.read_callback)
