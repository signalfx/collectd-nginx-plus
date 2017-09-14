# Reference base image
FROM quay.io/signalfuse/sf-collectd-integration-base:latest

# Set the required environment variables
ENV COLLECTD_HOSTNAME nginx-plus-test
ENV SF_INGEST_HOST https://ingest.signalfx.com
ENV SF_API_TOKEN XXXXXXXXXXXXXXXXXXXXXX

# Clone the plugin repo
RUN git clone https://github.com/signalfx/collectd-nginx-plus.git /opt/collectd-nginx-plus

# Add the plugin configuration
ADD 20-nginx-plus.conf /etc/collectd.d/managed_config/

# Install pip
RUN apt-get update
RUN apt-get install python-pip python-dev build-essential
RUN pip install --upgrade pip

# Install the Python dependencies
RUN pip install -r /opt/collectd-nginx-plus/install_requirements.txt

# Add the simple server that will keep the container alive
ADD 20-server.py /opt/setup/scripts
RUN chmod +x /opt/setup/scripts/20-server.py

# Install the keepalive server Python dependencies
ADD requirements.txt ./
RUN pip install -r requirements.txt

# Expose a port for the keepalive server
EXPOSE 5000
