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
        return ','.join(['='.join(pair) for pair in dimensions.items()])

# Server configueration flags
STATUS_HOST = 'StatusHost'
STATUS_PORT = 'StatusPort'
DEBUG_LOG_LEVEL = 'DebugLogLevel'
USERNAME = 'Username'
PASSWORD = 'Password'
DIMENSION = 'Dimension'

# Metric group configuration flags
SERVER_ZONE = 'ServerZone'
MEMORY_ZONE = 'MemoryZone'
UPSTREAM = 'Upstream'
CACHE = 'Cache'
STREAM_SERVER_ZONE = 'StreamServerZone'
STREAM_UPSTREAM = 'StreamUpstream'

# Metric groups
DEFAULT_CONNECTION_METRICS = [
    MetricDefinition('connections.accepted', 'counter', 'accepted'),
    MetricDefinition('connections.dropped', 'counter', 'dropped'),
    MetricDefinition('connections.idle', 'counter', 'idle')
]

DEFAULT_SSL_METRICS = [
    MetricDefinition('ssl.handshakes.successful', 'counter', 'handshakes'),
    MetricDefinition('ssl.handshakes.failed', 'counter', 'handshakes_failed')
]

DEFAULT_REQUESTS_METRICS = [
    MetricDefinition('requests.total', 'counter', 'total'),
    MetricDefinition('requests.current', 'counter', 'current')
]

DEFAULT_SERVER_ZONE_METRICS = [
    MetricDefinition('server.zone.requests', 'counter', 'requests')
]

DEFAULT_UPSTREAM_METRICS = [
    MetricDefinition('upstreams.requests', 'counter', 'requests')
]

DEFAULT_STREAM_SERVER_ZONE_METRICS = [
    MetricDefinition('stream.server.zone.connections', 'counter', 'connections')
]

DEFAULT_STREAM_UPSTREAM_METRICS = [
    MetricDefinition('stream.upstreams.connections', 'counter', 'connections')
]

SERVER_ZONE_METRICS = [
    MetricDefinition('server.zone.processing', 'counter', 'processing'),
    MetricDefinition('server.zone.discarded', 'counter', 'discarded'),
    MetricDefinition('server.zone.responses.total', 'counter', 'responses.total'),
    MetricDefinition('server.zone.responses.1xx', 'counter', 'responses.1xx'),
    MetricDefinition('server.zone.responses.2xx', 'counter', 'responses.2xx'),
    MetricDefinition('server.zone.responses.3xx', 'counter', 'responses.3xx'),
    MetricDefinition('server.zone.responses.4xx', 'counter', 'responses.4xx'),
    MetricDefinition('server.zone.responses.5xx', 'counter', 'responses.5xx'),
    MetricDefinition('server.zone.bytes.received', 'counter', 'received'),
    MetricDefinition('server.zone.bytes.sent', 'counter', 'sent')
]

MEMORY_ZONE_METRICS = [
    MetricDefinition('zone.pages.used', 'counter', 'pages.used'),
    MetricDefinition('zone.pages.free', 'counter', 'pages.free')
]

UPSTREAM_METRICS = [
    MetricDefinition('upstreams.active', 'counter', 'active'),
    MetricDefinition('upstreams.responses.total', 'counter', 'responses.total'),
    MetricDefinition('upstreams.responses.1xx', 'counter', 'responses.1xx'),
    MetricDefinition('upstreams.responses.2xx', 'counter', 'responses.2xx'),
    MetricDefinition('upstreams.responses.3xx', 'counter', 'responses.3xx'),
    MetricDefinition('upstreams.responses.4xx', 'counter', 'responses.4xx'),
    MetricDefinition('upstreams.responses.5xx', 'counter', 'responses.5xx'),
    MetricDefinition('upstreams.fails', 'counter', 'fails'),
    MetricDefinition('upstreams.unavailable', 'counter', 'unavail'),
    MetricDefinition('upstreams.health.checks.checks', 'counter', 'health_checks.checks'),
    MetricDefinition('upstreams.health.checks.fails', 'counter', 'health_checks.fails'),
    MetricDefinition('upstreams.health.checks.unhealthy', 'counter', 'health_checks.unhealthy')
]

CACHE_METRICS = [
    MetricDefinition('caches.size', 'counter', 'size'),
    MetricDefinition('caches.size.max', 'counter', 'max_size'),
    MetricDefinition('caches.hits', 'counter', 'hit.responses'),
    MetricDefinition('caches.misses', 'counter', 'miss.responses')
]

STREAM_SERVER_ZONE_METRICS = [
    MetricDefinition('stream.server.zone.processing', 'counter', 'processing'),
    MetricDefinition('stream.server.zone.sessions.2xx', 'counter', 'sessions.2xx'),
    MetricDefinition('stream.server.zone.sessions.4xx', 'counter', 'sessions.4xx'),
    MetricDefinition('stream.server.zone.sessions.5xx', 'counter', 'sessions.5xx'),
    MetricDefinition('stream.server.zone.received', 'counter', 'received'),
    MetricDefinition('stream.server.zone.sent', 'counter', 'sent'),
    MetricDefinition('stream.server.zone.discarded', 'counter', 'discarded')
]

STREAM_UPSTREAM_METRICS = [
    MetricDefinition('stream.upstreams.active', 'counter', 'active'),
    MetricDefinition('stream.upstreams.connections.max', 'counter', 'max_conns'),
    MetricDefinition('stream.upstreams.bytes.sent', 'counter', 'sent'),
    MetricDefinition('stream.upstreams.bytes.received', 'counter', 'received'),
    MetricDefinition('stream.upstreams.fails', 'counter', 'fails'),
    MetricDefinition('stream.upstreams.unavailable', 'counter', 'unavail'),
    MetricDefinition('stream.upstreams.health.checks.checks', 'counter', 'health_checks.checks'),
    MetricDefinition('stream.upstreams.health.checks.fails', 'counter', 'health_checks.fails'),
    MetricDefinition('stream.upstreams.health.checks.unhealthy', 'counter', 'health_checks.unhealthy')
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
            self._instance_id = self.nginx_agent.get_nginx_address()
        return self._instance_id

    def config_callback(self, conf):
        '''
        Configure the plugin with the configuration provided by collectd.
        '''
        LOGGER.info('Starting plugin configuration')

        status_host = None
        status_port = None
        username = None
        password = None

        # Iterate the configueration values, pickup the status endpoint info
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
            elif node.key == DIMENSION and len(node.values) == 2:
                self.global_dimensions[node.values[0]] = node.values[1]
            elif self._check_bool_config_enabled(node, DEBUG_LOG_LEVEL):
                log_handler.debug = self._str_to_bool(node.values[0])
            elif self._check_bool_config_enabled(node, CACHE):
                self._log_emitter_group_enabled(CACHE)
                self.emitters.append(MetricEmitter(self._emit_cache_metrics, CACHE_METRICS))
            elif self._check_bool_config_enabled(node, UPSTREAM):
                self._log_emitter_group_enabled(UPSTREAM)
                self.emitters.append(MetricEmitter(self._emit_upstreams_metrics, UPSTREAM_METRICS))
            elif self._check_bool_config_enabled(node, MEMORY_ZONE):
                self._log_emitter_group_enabled(MEMORY_ZONE)
                self.emitters.append(MetricEmitter(self._emit_memory_zone_metrics, MEMORY_ZONE_METRICS))
            elif self._check_bool_config_enabled(node, SERVER_ZONE):
                self._log_emitter_group_enabled(SERVER_ZONE)
                self.emitters.append(MetricEmitter(self._emit_server_zone_metrics, SERVER_ZONE_METRICS))
            elif self._check_bool_config_enabled(node, STREAM_UPSTREAM):
                self._log_emitter_group_enabled(STREAM_UPSTREAM)
                self.emitters.append(MetricEmitter(self._emit_stream_upstreams_metrics, STREAM_UPSTREAM_METRICS))
            elif self._check_bool_config_enabled(node, STREAM_SERVER_ZONE):
                self._log_emitter_group_enabled(STREAM_SERVER_ZONE)
                self.emitters.append(MetricEmitter(self._emit_stream_server_zone_metrics, STREAM_SERVER_ZONE_METRICS))

        # Default metric emitters
        self.emitters.append(MetricEmitter(self._emit_connection_metrics, DEFAULT_CONNECTION_METRICS))
        self.emitters.append(MetricEmitter(self._emit_ssl_metrics, DEFAULT_SSL_METRICS))
        self.emitters.append(MetricEmitter(self._emit_requests_metrics, DEFAULT_REQUESTS_METRICS))
        self.emitters.append(MetricEmitter(self._emit_server_zone_metrics, DEFAULT_SERVER_ZONE_METRICS))
        self.emitters.append(MetricEmitter(self._emit_upstreams_metrics, DEFAULT_UPSTREAM_METRICS))
        self.emitters.append(MetricEmitter(self._emit_stream_server_zone_metrics, DEFAULT_STREAM_SERVER_ZONE_METRICS))
        self.emitters.append(MetricEmitter(self._emit_stream_upstreams_metrics, DEFAULT_STREAM_UPSTREAM_METRICS))

        self.sink = MetricSink()
        self.nginx_agent = NginxStatusAgent(status_host, status_port, username, password)

        LOGGER.debug('Finished configuration. Will read status from %s:%s', status_host, status_port)

    def read_callback(self):
        '''
        Called to emit the actual metrics.
        Called once per interval (see Interval configuration option of collectd).
        If an exception is thrown the plugin will be skipped for an
        increasing amount of time until it returns to normal.
        '''
        LOGGER.debug('Starting read')

        if not self.instance_id:
            LOGGER.warning('Skipping read, instance id is not set')
            return

        self._reload_ephemerial_global_dimensions()

        for emitter in self.emitters:
            emitter.emit(self.sink)

    def _emit_connection_metrics(self, metrics, sink):
        '''
        Extract and emit the connection metrics.
        '''
        LOGGER.debug('Emitting connection metrics')

        status_json = self.nginx_agent.get_connections()
        self._fetch_and_emit_metrics(status_json, metrics, sink)

    def _emit_ssl_metrics(self, metrics, sink):
        '''
        Extract and emit the ssl metrics.
        '''
        LOGGER.debug('Emitting ssl metrics')

        status_json = self.nginx_agent.get_ssl()
        self._fetch_and_emit_metrics(status_json, metrics, sink)

    def _emit_requests_metrics(self, metrics, sink):
        '''
        Extract and emit the requests metrics.
        '''
        LOGGER.debug('Emitting requests metrics')

        status_json = self.nginx_agent.get_requests()
        self._fetch_and_emit_metrics(status_json, metrics, sink)

    def _emit_server_zone_metrics(self, metrics, sink):
        '''
        Extract and emit the server-zone metrics.
        '''
        LOGGER.debug('Emitting server-zone metrics')

        server_zones_obj = self.nginx_agent.get_server_zones()
        self._build_container_keyed_metrics(server_zones_obj, 'server.zone.name', metrics, sink)

    def _emit_upstreams_metrics(self, metrics, sink):
        '''
        Extract and emit the upstreams metrics.
        '''
        LOGGER.debug('Emitting upstreams metrics')

        upstreams_obj = self.nginx_agent.get_upstreams()
        self._build_container_keyed_peer_metrics(upstreams_obj, 'upstream.name', 'upstream.peer.name', metrics, sink)

    def _emit_stream_server_zone_metrics(self, metrics, sink):
        '''
        Extract and emit the stream-server-zone metrics.
        '''
        LOGGER.debug('Emitting stream-server-zone metrics')

        server_zones_obj = self.nginx_agent.get_stream_server_zones()
        self._build_container_keyed_metrics(server_zones_obj, 'stream.server.zone.name', metrics, sink)

    def _emit_stream_upstreams_metrics(self, metrics, sink):
        '''
        Extract and emit the stream-upstream metrics.
        '''
        LOGGER.debug('Emitting stream-upstreams metrics')

        upstreams_obj = self.nginx_agent.get_stream_upstreams()
        self._build_container_keyed_peer_metrics(upstreams_obj, 'stream.upstream.name', 'stream.upstream.peer.name',\
            metrics, sink)

    def _emit_memory_zone_metrics(self, metrics, sink):
        '''
        Extract and emit the memory zone metrics.
        '''
        LOGGER.debug('Emitting memory-zone metrics')

        slab_obj = self.nginx_agent.get_slabs()
        self._build_container_keyed_metrics(slab_obj, 'memory.zone.name', metrics, sink)

    def _emit_cache_metrics(self, metrics, sink):
        '''
        Extract and emit the cache metrics.
        '''
        LOGGER.debug('Emitting cache metrics')

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

    def _reload_ephemerial_global_dimensions(self):
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
    def __init__(self, status_host=None, status_port=None, username=None, password=None):
        self.status_host = status_host or 'localhost'
        self.status_port = status_port or 8080
        self.auth_tuple = (username, password) if username or password else None

        self.base_status_url = 'http://{}:{}/status'.format(self.status_host, str(self.status_port))
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
        return self._send_get(self.nginx_version_url)

    def get_nginx_address(self):
        '''
        Fetch the address of the nginx+ instance.
        Note, this will only return the value, not a dict.
        '''
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
    cli_status_host = sys.argv[1] if len(sys.argv) > 1 else 'demo.nginx.com'
    cli_status_port = sys.argv[2] if len(sys.argv) > 2 else 80

    collectd = CollectdMock()

    mock_config_ip_child = CollectdConfigChildMock(STATUS_HOST, [cli_status_host])
    mock_config_port_child = CollectdConfigChildMock(STATUS_PORT, [cli_status_port])
    mock_config_debug_log_level = CollectdConfigChildMock(DEBUG_LOG_LEVEL, ['true'])

    mock_config_username = CollectdConfigChildMock(USERNAME, ['user1'])
    mock_config_password = CollectdConfigChildMock(PASSWORD, ['test'])

    mock_config_dimension = CollectdConfigChildMock(DIMENSION, ['foo', 'bar'])

    # Setup the mock config to enable all metric groups
    mock_config_server_zone_child = CollectdConfigChildMock(SERVER_ZONE, ['true'])
    mock_config_memory_zone_child = CollectdConfigChildMock(MEMORY_ZONE, ['true'])
    mock_config_upstream_child = CollectdConfigChildMock(UPSTREAM, ['true'])
    mock_config_cache_child = CollectdConfigChildMock(CACHE, ['true'])
    mock_config_stream_server_zone_child = CollectdConfigChildMock(STREAM_SERVER_ZONE, ['true'])
    mock_config_stream_upstream_child = CollectdConfigChildMock(STREAM_UPSTREAM, ['true'])

    mock_config = CollectdConfigMock([mock_config_ip_child,
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
                                      mock_config_dimension])

    plugin = NginxPlusPlugin()
    plugin.config_callback(mock_config)

    while True:
        plugin.read_callback()
        time.sleep(5)
else:
    import collectd

    plugin = NginxPlusPlugin()

    collectd.register_config(plugin.config_callback)
    collectd.register_read(plugin.read_callback)
