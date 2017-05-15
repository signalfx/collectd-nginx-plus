# NGINX Plus CollectD plugin

A [CollectD](http://collectd.org) plugin to collect [NGINX Plus](https://www.nginx.com/products/) stats and metrics. Uses CollectD's [Python plugin](http://collectd.org/documentation/manpages/collectd-python.5.shtml).

### Installing
The plugin module can be downloaded from pypi and the plugin script placed at `/usr/share/collectd/nginx-plus-collectd`
with the below command.
~~~~
pip install nginx-plus-collectd --install-option="--install-scripts=/usr/share/collectd/nginx-plus-collectd"
~~~~
