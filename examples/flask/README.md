# example flask app

## Download or Build

First, [create and activate a virtual environment](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#creating-a-virtual-environment):

```bash
python3 -m venv env

source env/bin/activate
```

Then install the dependencies:

```bash
python3 -m pip install .
```

Run the application:

```bash
flask run
```

The server will start listening on port 5000:

```bash
$ curl localhost:5000
Hello World
```

Check out results in Honeycomb! To [deactivate the virtual environment](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/#leaving-the-virtual-environment):

```bash
deactivate
```
