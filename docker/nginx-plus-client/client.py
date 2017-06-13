#!/usr/bin/env python
import requests
import argparse
import time
from requests.exceptions import RequestException

def start_requests(host, ports, requests_per_sec, timeout_ms):
    urls = _build_urls(host, ports)
    requests_per_sec_range = range(requests_per_sec)
    timeout_sec = timeout_ms / 1000.0

    while True:
        for url in urls:
            for i in requests_per_sec_range:
                print 'GET ' + url
                try:
                    requests.get(url, timeout=timeout_sec)
                except RequestException as e:
                    pass
        time.sleep(1)

def _build_urls(host, ports):
    return ['http://{}:{}'.format(host, str(port)) for port in ports]

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', '-d', required=True, help='URL of the host to make requests to')
    parser.add_argument('--ports', '-p', help='CSV of port host port numbers to make requsets against')
    parser.add_argument('--requests-sec', '-r', default=1, type=int, help='The number of requests to make per second on each host:port url')
    parser.add_argument('--timeout-ms', '-t', default=1000, type=int, help='Request timeout in milliseconds')

    args = parser.parse_args()
    host = args.host
    ports = [int(port) for port in args.ports.split(',')] if args.ports else [80]
    requests_per_sec = args.requests_sec
    timeout_ms = args.timeout_ms

    start_requests(host, ports, requests_per_sec, timeout_ms)
