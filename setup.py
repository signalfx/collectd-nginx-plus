#!/usr/bin/env python
from setuptools import setup, find_packages

setup(name='nginx-plus-collectd',
    version='0.0.0',
    description='Collectd plugin to report NGINX Plus metrics',
    author='Matt Tieman',
    author_email='mtieman@signalfx.com',
    url='https://github.com/signalfx/collectd-nginx-plus',
    packages=find_packages(exclude=['test*']),
    include_package_data=True,
    zip_safe=False,
    scripts=['plugin/nginx-plus-collectd.py'],
    install_requires=[]
)
