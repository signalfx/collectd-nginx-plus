#!/usr/bin/env python
import argparse
import time
import random
from flask import Flask

status_codes = [100, 200, 300, 400, 500]
hit_counter = 0

server = Flask(__name__)

@server.route('/')
def random_response():
    global hit_counter

    hit_counter += 1
    time.sleep(random.randint(min_response_time, max_response_time) / 1000.0)
    return 'Random response: {}'.format(str(hit_counter)), random.choice(status_codes)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--status-codes', '-s', help='Comma separated list of status codes to randomly return')
    parser.add_argument('--min-response-time', '-min', default=0, type=int, help='Minimum response time in milliseconds')
    parser.add_argument('--max-response-time', '-max', default=500, type=int, help='Maximum response time in milliseconds')

    args = parser.parse_args()
    args_codes = args.status_codes
    min_response_time = args.min_response_time
    max_response_time = args.max_response_time

    if args_codes:
        status_codes = [int(code) for code in args_codes.split(',')]
    server.run(host='0.0.0.0')
