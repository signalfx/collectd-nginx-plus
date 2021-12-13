# Reference base image
FROM quay.io/signalfuse/sf-collectd-integration-base:latest

# Set the required environment variables
ENV COLLECTD_HOSTNAME nginx-plus-test
ENV SF_INGEST_HOST https://ingest.signalfx.com
ENV SF_API_TOKEN XXXXXXXXXXXXXXXXXXXXXX

# Clone the plugin repo
COPY collectd-nginx-plus /opt/collectd-nginx-plus

# Add the plugin configuration
ADD collectd-nginx-plus/docker/collectd/20-nginx-plus.conf /etc/collectd.d/managed_config/

# Install pip
RUN apt-get update
RUN apt-get install python2.7 -y
RUN wget -P ~/.local/lib https://bootstrap.pypa.io/pip/2.7/get-pip.py
RUN python2.7 ~/.local/lib/get-pip.py

# Install the Python dependencies
RUN python2.7 -m pip install -r /opt/collectd-nginx-plus/install_requirements.txt

# Add the simple server that will keep the container alive
ADD collectd-nginx-plus/docker/collectd/20-server.py /opt/setup/scripts
RUN chmod +x /opt/setup/scripts/20-server.py

# Install the keepalive server Python dependencies
ADD collectd-nginx-plus/docker/collectd/requirements.txt ./
RUN python2.7 -m pip install -r requirements.txt

# Expose a port for the keepalive server
EXPOSE 5000
