from setuptools import setup

setup(
      python_requires='>=2.7',
      name='honeycomb-beeline',
      version='0.0.1',
      description='Honeycomb library for easy instrumentation',
      url='https://github.com/honeycombio/beeline-python',
      author='Honeycomb.io',
      author_email='feedback@honeycomb.io',
      license='Apache',
      packages=['beeline'],
      install_requires=[
          'libhoney',
          'wrapt',
      ],
      tests_require=[
        'mock',
      ],
      test_suite='beeline',
      zip_safe=False
)
