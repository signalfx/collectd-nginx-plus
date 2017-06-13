# NGINX Plus Collectd plugin

A [collectd](http://collectd.org) plugin to collect [NGINX Plus](https://www.nginx.com/products/) stats and metrics.
Uses collectd's [Python plugin](http://collectd.org/documentation/manpages/collectd-python.5.shtml).

## Installation

1. Checkout this repository somewhere on your system accessible by collectd.
The suggested location is `/usr/share/collectd/`.
1. Install the Python requirements with `sudo pip install -r install_requirements.txt`
1. Configure the plugin (see below)
1. Restart collectd

## Configuration

Within the plugin's `Module` block plugin-specific configuration options can be given.
The available configuration options are detailed below.

##### Configuration Options

| Property | Description |
|:--------|:-----------|
| StatusHost | IP address or DNS of the NGINX+ instance to retrieve status information from. Defaults to `localhost`. |
| StatusPort | Port the NGINX+ status endpoint can be reached at. Defaults to `8080`. |
| DebugLogLevel | Enable logging at DEBUG level. |
| Username | Username to use for username/password authentication. |
| Password | Password to use for username/password authentication. |
| Dimension | A single additional dimension decorating to each metric. There are two values, the first for the name, the second for the value. |

Example addition to the collectd configuration:

```apache
LoadPlugin python

<Plugin python>
  ModulePath "/usr/share/collectd/collectd-nginx-plus/plugin"
  Import nginx_plus_collectd

  <Module nginx_plus_collectd>
    StatusHost "localhost"
    StatusPort "8080"
    DebugLogLevel true
    Username "user_1"
    Password "my_password"
    Dimension "extra_dimension_name_1" "extra_dimension_value_1"
    Dimension "extra_dimension_name_2" "extra_dimension_value_2"
  </Module>
</Plugin>
```

## Metrics

By default only a subset of the available metrics are published by default. The remaining metrics can be enabled
by opting-in to additional metric groups. The metrics in each group are listed below, along with the dimensions added
to each group. By default all metrics are decorated with the `nginx.version` dimension.

### Default Metrics
These metrics are published by default.

| Metric | Additional Dimensions |
|:-------|:----------|
| connections.accepted | None |
| connections.dropped | None |
| connections.idle | None |
| connections.active | None |
| ssl.handshakes.successful | None |
| ssl.handshakes.failed | None |
| ssl.handshakes.reuses | None |
| requests.total | None |
| requests.current | None |
| server.zone.requests | server.zone.name |
| server.zone.responses.1xx | server.zone.name |
| server.zone.responses.2xx | server.zone.name |
| server.zone.responses.3xx | server.zone.name |
| server.zone.responses.4xx | server.zone.name |
| server.zone.responses.5xx | server.zone.name |
| server.zone.responses.total | server.zone.name |
| server.zone.responses.received | server.zone.name |
| server.zone.bytes.received | server.zone.name |
| server.zone.bytes.sent | server.zone.name |
| caches.size | cache.name |
| caches.size.max | cache.name |
| upstreams.requests | upstream.name, upstream.peer.name |
| upstreams.responses.1xx | upstream.name, upstream.peer.name |
| upstreams.responses.2xx | upstream.name, upstream.peer.name |
| upstreams.responses.3xx | upstream.name, upstream.peer.name |
| upstreams.responses.4xx | upstream.name, upstream.peer.name |
| upstreams.responses.5xx | upstream.name, upstream.peer.name |
| upstreams.responses.total | upstream.name, upstream.peer.name |
| upstreams.downtime | upstream.name, upstream.peer.name |
| upstreams.response.time | upstream.name, upstream.peer.name |
| upstreams.bytes.received | upstream.name, upstream.peer.name |
| upstreams.bytes.sent | upstream.name, upstream.peer.name |

### Server Zone Metrics
All server zone metrics are decorated with dimension `server.zone.name` .
To include these metrics, add `ServerZone true` to the plugin configuration, e.g.
```apache
  <Module nginx_plus_collectd>
    StatusHost "localhost"
    StatusPort "8080"
    ServerZone true
  </Module>
```
##### Metrics
* server.zone.processing
* server.zone.discarded

### Memory Zone Metrics
All memory zone metrics are decorated with dimension `memory.zone.name` .
To include these metrics, add `MemoryZone true` to the plugin configuration, e.g.
```apache
  <Module nginx_plus_collectd>
    StatusHost "localhost"
    StatusPort "8080"
    MemoryZone true
  </Module>
```
##### Metrics
* zone.pages.used
* zone.pages.free

### Upstream Metrics
All upstream metrics are decorated with dimensions `upstream.name` and `upstream.peer.name` .
To include these metrics, add `Upstream true` to the plugin configuration, e.g.
```apache
  <Module nginx_plus_collectd>
    StatusHost "localhost"
    StatusPort "8080"
    Upstream true
  </Module>
```
##### Metrics
* upstreams.active
* upstreams.fails
* upstreams.unavailable
* upstreams.health.checks.checks
* upstreams.health.checks.fails
* upstreams.health.checks.unhealthy
* upstreams.header.time
* upstreams.keepalive
* upstreams.zombies

### Cache Metrics
All cache metrics are decorated with dimension `cache.name` .
To include these metrics, add `Cache true` to the plugin configuration, e.g.
```apache
  <Module nginx_plus_collectd>
    StatusHost "localhost"
    StatusPort "8080"
    Cache true
  </Module>
```
##### Metrics
* caches.hit.responses
* caches.miss.responses
* caches.stale.responses
* caches.updating.responses
* caches.revalidated.responses
* caches.expired.responses
* caches.bypass.responses
* caches.hit.bytes
* caches.miss.bytes
* caches.stale.bytes
* caches.updating.bytes
* caches.revalidated.bytes
* caches.expired.bytes
* caches.bypass.bytes
* caches.miss.responses.written
* caches.expired.responses.written
* caches.bypass.responses.written
* caches.miss.bytes.written
* caches.expired.bytes.written
* caches.bypass.bytes.written

### Stream Server Zone Metrics
All stream server zone metrics are decorated with dimension `stream.server.zone.name` .
To include these metrics, add `StreamServerZone true` to the plugin configuration, e.g.
```apache
  <Module nginx_plus_collectd>
    StatusHost "localhost"
    StatusPort "8080"
    StreamServerZone true
  </Module>
```
##### Metrics
* stream.server.zone.connections
* stream.server.zone.processing
* stream.server.zone.sessions.2xx
* stream.server.zone.sessions.4xx
* stream.server.zone.sessions.5xx
* stream.server.zone.received
* stream.server.zone.sent
* stream.server.zone.discarded

### Stream Upstream Metrics
All stream upstream metrics are decorated with dimensions `stream.upstream.name` and `stream.upstream.peer.name`.
To include these metrics, add `StreamUpstream true` to the plugin configuration, e.g.
```apache
  <Module nginx_plus_collectd>
    StatusHost "localhost"
    StatusPort "8080"
    StreamUpstream true
  </Module>
```
##### Metrics
* stream.upstreams.connections
* stream.upstreams.active
* stream.upstreams.connections.max
* stream.upstreams.bytes.sent
* stream.upstreams.bytes.received
* stream.upstreams.fails
* stream.upstreams.unavailable
* stream.upstreams.health.checks.checks
* stream.upstreams.health.checks.fails
* stream.upstreams.health.checks.unhealthy
* stream.upstreams.response.time
* stream.upstreams.downtime
* stream.upstreams.bytes.received
* stream.upstreams.bytes.sent
* stream.upstreams.zombies

### Processes Metrics
Process metrics only include the default dimensions.
To include these metrics, add `Processes true` to the plugin configuration, e.g.
```apache
  <Module nginx_plus_collectd>
    StatusHost "localhost"
    StatusPort "8080"
    Processes true
  </Module>
```
##### Metrics
* processes.respawned

## Development
Before making changes to the plugin, it is highly recommended first create a virtual Python environment.
This can be done with [virtualenv](https://virtualenv.pypa.io/en/stable/). This helps avoid dependency conflicts,
preserves your global site-packages and helps catch missing dependencies in the pip requirements.txts.

## Dependencies
The dependencies needed for local development (running unit tests, etc.) are contained in `dev_requirements.txt` and
can be installed via pip: `pip install -r dev_requirements.txt`.

## Running Locally
A quick way to run the plugin locally and consume from a rich data source is to configure it to read from the NGINX+
demo: `./nginx_plus_collectd.py 'demo.nginx.com' 80`

## Unit Tests
Running the unit tests is done via a recipe in the `makefile`, the command: `make test`.
The unit tests are run with [nose](http://nose.readthedocs.io/en/latest/) inside a virtual environment managed
by [tox](https://pypi.python.org/pypi/tox). The `test_requirements.txt` contains all the testing dependencies and
is used to pip install everything needed by the tests in the tox environments (tox installs these dependencies).

## Code Hygiene
The `make check` command will run [pylint](https://www.pylint.org/) with standards defined in `pylintrc`. Having a
slight drop in code rating is not a blocker for changes, but a significant drop should be addressed. This is a
measurable way to enforce style and standards.

## Cleanup
Run `make clean` to remove artifacts leftover by tox and pylint.
