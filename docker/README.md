# Local Docker Environment

The content of this directory enables the creation of a local NGINX Plus environment capable of generating default
metrics. The environment is created via [Docker Compose](https://docs.docker.com/compose/).

The environment is composed of a single NGINX Plus container, four proxied server containers, a client container
and a collectd container running the plugin.
The NGINX Plus container has two server zones and two upstream groups containing two servers. Each server zone proxies
to an upstream group. Each server zone also has a cache. The NGINX Plus container maps port 80 to a random host port.
The `status` endpoint is available on port 80. The status endpoint is protected by username:password. The username is
`user1` and the password `test`.

Two of the four server containers return random status codes with random amounts of response time
(between 0 and 500 ms.). The other two will randomly return a 200 or 400 status code with the same response time bounds
as their peers. The list of status codes to select from as well as the min and max response times can be changed in the
`docker-compose.yml` via the environment variables for each container.

The client container will send a request to each NGINX Plus port that is proxying to the server containers. By default
the client sends five requests per second. The requests per second can be changed in the `docker-compose.yml` via
the container environment variables.

The collectd container will be configured to only report the default metrics. Before building the container, add
your API token to `collectd/Dockerfile` as the `SF_API_TOKEN` environment variable.

## Prerequisites

Both Docker and Docker Compose must be installed, documentation for the
[former](https://docs.docker.com/engine/installation/), the [latter](https://docs.docker.com/compose/install/).

To build the NGINX Plus image the repository certificate and key are required. Before building,
copy the certificate to `nginx-plus-server/nginx-repo.crt` and the key to `nginx-plus-server/nginx-repo.key`.
Another option is to change the paths to the certificate and key files in lines 12 and 13 of
`nginx-plus-server/Dockerfile`.

## Run with the legacy NGINX Plus API

Current `nginx-plus-server/Dockerfile` is configured to run the NGINX+ with the newer type of API. In order to run
the NGINX+ with the legacy type of API, make the following changes:

1. In `nginx-plus-server/nginx.conf` use `/status.html` instead of `/dashboard.html`
2. Make the following changes in `nginx-plus-server/nginx.conf`:
    * Replace the `api` directive with the `status` directive
    * Update the API base path (`/test/api`) with some other base path (optional)
3. Update the `collectd/20-nginx-plus.conf` with the valid configuration.

## Starting the Environment

Running `docker-compose up -d --build` will build the Docker images and start the containers.

## Tearing Down the Environment

Running `docker-compose down` will stop all the containers.
