import sys
from setuptools import setup, find_packages

setup(
    python_requires='>=2.7',
    name='honeycomb-beeline',
    version='1.4.0',
    description='Honeycomb library for easy instrumentation',
    url='https://github.com/honeycombio/beeline-python',
    author='Honeycomb.io',
    author_email='feedback@honeycomb.io',
    license='Apache',
    packages=find_packages(),
    install_requires=[
        'libhoney>=1.6.0',
        'wrapt',
    ],
    tests_require=[
        'mock',
        'flask',
        'django<2; python_version == "2.7"',
        'django>=2; python_version >= "3.0"',
    ],
    test_suite='beeline',
    zip_safe=False
)
