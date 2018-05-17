from setuptools import setup

setup(
      python_requires='>=3',
      name='django-beeline',
      version='0.0.1',
      description='Honeycomb Integration for Django',
      url='https://github.com/honeycombio/beeline-python',
      author='Honeycomb.io',
      author_email='feedback@honeycomb.io',
      license='Apache',
      packages=['django_beeline'],
      install_requires=[
          'libhoney',
      ],
      tests_require=[
        'mock',
      ],
      zip_safe=False
)
