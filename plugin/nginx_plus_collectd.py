#!/usr/bin/env python
import os
import sys
import time
import logging
import requests

class MetricDefinition:
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

class MetricEmitter:
    '''
    Encapsulates a function to build metrics and the definitions of metrics
    that should be built.

    Constructor Arguements:
        emit_func: The function used to build and emit metrics from the NGINX+
                    status JSON. The function is expected to accept the arguements:
                        * The NGINX+ status JSON
                        * A list of MetricDefinitions
                        * An instance of MetricSink

        metrics: A list of MetricDefinition, the metrics to be built and emitted by emit_func
    '''
    def __init__(self, emit_func, metrics):
        self.emit_func = emit_func
        self.metrics = metrics

    def emit(self, status_json, sink):
        '''
        Build and emit metrics with the encapsulated function and metric definitions
        along with the given status JSON and sink.
        '''
        self.emit_func(status_json, self.metrics, sink)

class MetricRecord:
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

class MetricSink:
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
        emit_value.plugin_instance += '[{}]'.format(metric_record.dimensions)

        # With some versions of CollectD, a dummy metadata map must to be added
        # to each value for it to be correctly serialized to JSON by the
        # write_http plugin. See
        # https://github.com/collectd/collectd/issues/716
        emit_value.meta = {'true': 'true'}

        emit_value.dispatch()

# Server configueration flags
STATUS_HOST = 'StatusHost'
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
    MetricDefinition('connections.accepted', 'counter', 'connections.accepted'),
    MetricDefinition('connections.dropped', 'counter', 'connections.dropped'),
    MetricDefinition('connections.idle', 'counter', 'connections.idle'),
    MetricDefinition('ssl.handshakes.successful', 'counter', 'ssl.handshakes.handshakes'),
    MetricDefinition('ssl.handshakes.failed', 'counter', 'ssl.handshakes.handshakes_failed'),
    MetricDefinition('requests.total', 'counter', 'requests.total'),
    MetricDefinition('requests.current', 'counter', 'requests.current'),
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

class NginxPlusPlugin:
    '''
    Collectd plugin for reporting metrics from a single NGINX+ instance.
    '''
    def __init__(self):
        self.nginx_agent = None
        self.sink = None
        self.emitters = []

        self._instance_id = None

    @property
    def instance_id(self):
        if not self._instance_id:
            status_json = self.nginx_agent.get_status()
            if status_json:
                self._instance_id = _reduce_to_path(status_json, 'address')
        return self._instance_id

    def config_callback(self, conf):
        '''
        Configure the plugin with the configuration provided by collectd.
        '''
        LOGGER.info('Starting plugin configuration')

        status_host = None
        status_port = None

        # Iterate the configueration values, pickup the status endpoint info
        # and create any specified opt-in metric emitters
        for node in conf.children:
            if node.key == STATUS_HOST:
                status_host = node.values[0]
            elif node.key == STATUS_PORT:
                status_port = node.values[0]
            elif self._check_config_metric_group_enabled(node, CACHE):
                self._log_emitter_group_enabled(CACHE)
                self.emitters.append(MetricEmitter(self._emit_cache_metrics, CACHE_METRICS))
            elif self._check_config_metric_group_enabled(node, UPSTREAM):
                self._log_emitter_group_enabled(UPSTREAM)
                self.emitters.append(MetricEmitter(self._emit_upstreams_metrics, UPSTREAM_METRICS))
            elif self._check_config_metric_group_enabled(node, MEMORY_ZONE):
                self._log_emitter_group_enabled(MEMORY_ZONE)
                self.emitters.append(MetricEmitter(self._emit_memory_zone_metrics, MEMORY_ZONE_METRICS))
            elif self._check_config_metric_group_enabled(node, SERVER_ZONE):
                self._log_emitter_group_enabled(SERVER_ZONE)
                self.emitters.append(MetricEmitter(self._emit_server_zone_metrics, SERVER_ZONE_METRICS))
            elif self._check_config_metric_group_enabled(node, STREAM_UPSTREAM):
                self._log_emitter_group_enabled(STREAM_UPSTREAM)
                self.emitters.append(MetricEmitter(self._emit_stream_upstreams_metrics, STREAM_UPSTREAM_METRICS))
            elif self._check_config_metric_group_enabled(node, STREAM_SERVER_ZONE):
                self._log_emitter_group_enabled(STREAM_SERVER_ZONE)
                self.emitters.append(MetricEmitter(self._emit_stream_server_zone_metrics, STREAM_SERVER_ZONE_METRICS))

        # Default metric emitters
        self.emitters.append(MetricEmitter(self._emit_top_level_metrics, DEFAULT_CONNECTION_METRICS))
        self.emitters.append(MetricEmitter(self._emit_server_zone_metrics, DEFAULT_SERVER_ZONE_METRICS))
        self.emitters.append(MetricEmitter(self._emit_upstreams_metrics, DEFAULT_UPSTREAM_METRICS))
        self.emitters.append(MetricEmitter(self._emit_stream_server_zone_metrics, DEFAULT_STREAM_SERVER_ZONE_METRICS))
        self.emitters.append(MetricEmitter(self._emit_stream_upstreams_metrics, DEFAULT_STREAM_UPSTREAM_METRICS))

        self.sink = MetricSink()
        self.nginx_agent = NginxStatusAgent(status_host, status_port)

        LOGGER.debug('Finished configuration. Reading status from {}:{}'.format(status_host, status_port))

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

        status_json = self.nginx_agent.get_status()
        if not status_json:
            LOGGER.warning('Skipping read, failed to retrieve status JSON')
            return

        for emitter in self.emitters:
            emitter.emit(status_json, self.sink)

    def _emit_top_level_metrics(self, status_json, metrics, sink):
        '''
        Extract and emit the top-level metrics from the status JSON.
        '''
        LOGGER.debug('Emitting top-level metrics')

        dimensions = {'nginx.version' : _reduce_to_path(status_json, 'nginx_version')}
        self._fetch_and_emit_metrics(status_json, metrics, dimensions, sink)

    def _emit_server_zone_metrics(self, status_json, metrics, sink):
        '''
        Extract and emit the server-zone metrics from the status JSON.
        '''
        LOGGER.debug('Emitting server-zone metrics')

        server_zones_obj = _reduce_to_path(status_json, 'server_zones')
        self._build_container_keyed_metrics(server_zones_obj, 'server.zone.name', metrics, sink)

    def _emit_upstreams_metrics(self, status_json, metrics, sink):
        '''
        Extract and emit the upstreams metrics from the status JSON.
        '''
        LOGGER.debug('Emitting upstreams metrics')

        upstreams_obj = _reduce_to_path(status_json, 'upstreams')
        self._build_container_keyed_peer_metrics(upstreams_obj, 'upstream.name', 'upstream.peer.name', metrics, sink)

    def _emit_stream_server_zone_metrics(self, status_json, metrics, sink):
        '''
        Extract and emit the stream-server-zone metrics from the status JSON.
        '''
        LOGGER.debug('Emitting stream-server-zone metrics')

        server_zones_obj = _reduce_to_path(status_json, 'stream.server_zones')
        self._build_container_keyed_metrics(server_zones_obj, 'stream.server.zone.name', metrics, sink)

    def _emit_stream_upstreams_metrics(self, status_json, metrics, sink):
        '''
        Extract and emit the stream-upstream metrics from the status JSON.
        '''
        LOGGER.debug('Emitting stream-upstreams metrics')

        upstreams_obj = _reduce_to_path(status_json, 'stream.upstreams')
        self._build_container_keyed_peer_metrics(upstreams_obj, 'stream.upstream.name', 'stream.upstream.peer.name',\
            metrics, sink)

    def _emit_memory_zone_metrics(self, status_json, metrics, sink):
        '''
        Extract and emit the memory zone metrics from the status JSON.
        '''
        LOGGER.debug('Emitting memory-zone metrics')

        slab_obj = _reduce_to_path(status_json, 'slabs')
        self._build_container_keyed_metrics(slab_obj, 'memory.zone.name', metrics, sink)

    def _emit_cache_metrics(self, status_json, metrics, sink):
        '''
        Extract and emit the cache metrics from the status JSON.
        '''
        LOGGER.debug('Emitting cache metrics')

        cache_obj = _reduce_to_path(status_json, 'caches')
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
                self._fetch_and_emit_metrics(container, metrics, dimensions, sink)

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
                    self._fetch_and_emit_metrics(peer, metrics, dimensions, sink)

    def _fetch_and_emit_metrics(self, scoped_obj, metrics, dimensions, sink):
        '''
        For each metric the value is extracted from the given object and emitted
        with the specified dimensions using the given sink. The current time will
        be passed in on the emit.
        '''
        for metric in metrics:
            value = _reduce_to_path(scoped_obj, metric.scoped_object_key)
            if value is not None:
                sink.emit(MetricRecord(metric.name, metric.type, value, self.instance_id, dimensions, time.time()))

    def _check_config_metric_group_enabled(self, config_node, key):
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
        LOGGER.debug('{} enabled, adding emitters'.format(emitter_group))

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
        if type(path) in (str, unicode):
            path = path.split('.')
        return reduce(lambda x, y: x[y], path, obj)
    except:
        return None


class NginxStatusAgent:
    '''
    Helper class for interacting with a single NGINX+ instance.
    '''
    def __init__(self, status_host=None, status_port=None):
        self.status_host = status_host or 'localhost'
        self.status_port = status_port or 8080

        self.status_url = 'http://{}:{}/status'.format(self.status_host, str(self.status_port))

    def get_status(self):
        '''
        Fetch the server status JSON.
        '''
        status = None
        try:
            response = requests.get(self.status_url)
            if response.status_code == requests.codes.ok:
                status = response.json()
            else:
                LOGGER.error('Unexpected status code: {}, received when fetching status from {}'\
                    .format(response.status_code, self.status_url))
        except Exception as e:
            LOGGER.exception('Failed to retrieve status from {}. {}'.format(self.status_url, e))
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
        plugin -- name of the plugin (default 'unknown')
        verbose -- enable/disable verbose messages (default False)
    '''

    def __init__(self, plugin='unknown', debug=False):
        '''
        Initializes CollectdLogHandler
        Arguments
            plugin -- string name of the plugin (default 'unknown')
            debug  -- boolean to enable debug level logging, defaults to false
        '''
        self.plugin = plugin
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
                    collectd.error('%s : %s' % (self.plugin, record.msg))
                elif record.levelname == 'WARNING':
                    collectd.warning('%s : %s' % (self.plugin, record.msg))
                elif record.levelname == 'INFO':
                    collectd.info('%s : %s' % (self.plugin, record.msg))
                elif record.levelname == 'DEBUG' and self.debug:
                    collectd.debug('%s : %s' % (self.plugin, record.msg))
        except Exception as e:
            collectd.warning(('{p} [ERROR]: Failed to write log statement due '
                              'to: {e}').format(p=self.plugin, e=e))


class CollectdMock:
    '''
    Mock of the collectd module.

    This is used when running the plugin locally.
    All log messages are printed to stdout.
    The Values() method will return an instance of CollectdValuesMock
    '''
    def __init__(self):
        self.value_mock = CollectdValuesMock

    def debug(self, msg):
        print 'DEBUG: {}'.format(msg)

    def info(self, msg):
        print 'INFO: {}'.format(msg)

    def notice(self, msg):
        print 'NOTICE: {}'.format(msg)

    def warning(self, msg):
        print 'WARN: {}'.format(msg)

    def error(self, msg):
        print 'ERROR: {}'.format(msg)
        sys.exit(1)

    def Values(self):
        return (self.value_mock)()


class CollectdValuesMock:
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

        print 'PUTVAL', identifier, ':'.join(map(str, [int(self.time)] + self.values))

    def __str__(self):
        attrs = []
        for name in dir(self):
            if not name.startswith('_') and name is not 'dispatch':
                attrs.append("{}={}".format(name, getattr(self, name)))
        return "<CollectdValues {}>".format(' '.join(attrs))

class CollectdConfigMock:
    '''
    Mock of the collectd Config class.

    This class is used to configure the plugin when running locally.
    The children field is expected to be a list of CollectdConfigChildMock.
    '''
    def __init__(self, children=None):
        self.children = children or []

class CollectdConfigChildMock:
    '''
    Mock of the collectd Conf child class.

    This class is used to mock key:value pairs normally pulled from the plugin
    configuration file.
    '''
    def __init__(self, key, values):
        self.key = key
        self.values = values


# Set up logging
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
LOGGER.propagate = False
LOGGER.addHandler(CollectdLogHandler('nginx-plus-collectd', False))

if __name__ == '__main__':
    status_host = sys.argv[1] if len(sys.argv) > 1 else 'demo.nginx.com'
    status_port = sys.argv[2] if len(sys.argv) > 2 else 80

    collectd = CollectdMock()

    mock_config_ip_child = CollectdConfigChildMock(STATUS_HOST, [status_host])
    mock_config_port_child = CollectdConfigChildMock(STATUS_PORT, [status_port])

    # Setup the mock config to enable all metric groups
    mock_config_server_zone_child = CollectdConfigChildMock(SERVER_ZONE, ['true'])
    mock_config_memory_zone_child = CollectdConfigChildMock(MEMORY_ZONE, ['true'])
    mock_config_upstream_child = CollectdConfigChildMock(UPSTREAM, ['true'])
    mock_config_cache_child = CollectdConfigChildMock(CACHE, ['true'])
    mock_config_stream_server_zone_child = CollectdConfigChildMock(STREAM_SERVER_ZONE, ['true'])
    mock_config_stream_upstream_child = CollectdConfigChildMock(STREAM_UPSTREAM, ['true'])

    mock_config = CollectdConfigMock([mock_config_ip_child,
                                      mock_config_port_child,
                                      mock_config_server_zone_child,
                                      mock_config_memory_zone_child,
                                      mock_config_upstream_child,
                                      mock_config_cache_child,
                                      mock_config_stream_server_zone_child,
                                      mock_config_stream_upstream_child])

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
