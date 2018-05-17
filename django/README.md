# django beeline

## local development

Ensure you have the required dependencies:

```bash
pip install --user setuptools libhoney
```

Run setuptools to install locally:

```bash
$ python setup.py install -f
```

You should see the module in your local pip:

```bash
$ pip list | grep django-beeline
django-beeline         0.0.1
```

Test that it is installed:

```python
from django_beeline import Middleware
```
