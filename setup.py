#!/usr/bin/env python
"""
fds
==========
.. code:: shell
  $ fds block <ip_address>
  $ fds block <country>
"""

from setuptools import find_packages, setup
import os

install_requires = [
    'six',
    'netaddr',
    'cachecontrol',
    'tqdm',
    'cloudflare>=2.7.1'
]
tests_requires = ["pytest", "flake8", "faker"]

with open("README.md", "r") as fh:
    long_description = fh.read()

base_dir = os.path.dirname(__file__)

setup(
    name="fds",
    author="Danila Vershinin",
    author_email="info@getpagespeed.com",
    url="https://github.com/dvershinin/fds",
    description="The go-to FirewallD CLI app",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["tests"]),
    package_data={'fds': ['data/*.json']},
    zip_safe=False,
    license="BSD",
    use_scm_version={
        'write_to': 'fds/__about__.py',
        'write_to_template': '__version__ = "{version}"',
    },
    setup_requires=['setuptools_scm', 'setuptools_scm_git_archive'],
    install_requires=install_requires,
    extras_require={
        "tests": install_requires + tests_requires,
    },
    tests_require=tests_requires,
    include_package_data=True,
    entry_points={"console_scripts": ["fds = fds:main"]},
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Operating System :: OS Independent",
        "Topic :: Software Development",
    ],
)
