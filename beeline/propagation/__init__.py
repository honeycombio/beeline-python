import six
from abc import ABCMeta, abstractmethod
import beeline


class PropagationContext(object):
    '''
    PropagationContext represents information that can either be read from, or
    propagated via standard trace propagation headers such as X-Honeycomb-Trace
    and W3C headers. http_trace_parser_hooks generate this from requests, and
    http_trace_propagation_hooks use this to generate a set of headers for
    outbound HTTP requests.
    '''

    def __init__(self, trace_id, parent_id, trace_fields={}, dataset=None):
        self.trace_id = trace_id
        self.parent_id = parent_id
        self.trace_fields = trace_fields
        self.dataset = dataset


@six.add_metaclass(ABCMeta)
class Request(object):
    '''
    beeline.propagation.Request is an abstract class that defines the interface that should
    be used by middleware to pass request information into http_trace_parser_hooks. It should
    at a minimum contain the equivalent of HTTP headers, and optionally include other HTTP
    information such as method, schema, host, path, and query. The `middleware_request` method
    returns a middleware-specific request object or equivalent that can be used by custom hooks
    to extract additional information to be added to the trace or propagated.
    '''

    @abstractmethod
    def header(self, key):
        """
        Get the value associated with the specified key, transformed as necessary for the
        transport and middleware.
        """
        pass

    @abstractmethod
    def method(self):
        """
        For HTTP requests, the HTTP method (GET, PUT, etc.) of the request.
        """
        pass

    @abstractmethod
    def scheme(self):
        """
        For HTTP requests, the scheme (http, https, etc.)
        """
        pass

    @abstractmethod
    def host(self):
        """
        For HTTP requests, the host part of the URL (e.g. www.honeycomb.io, api.honeycomb.io:80)
        """
        pass

    @abstractmethod
    def path(self):
        """
        For HTTP requests, the path part of the URL (e.g. /1/event/)
        """
        pass

    @abstractmethod
    def query(self):
        """
        For HTTP requests, the query part of the URL (e.g. key1=value1&key2=value2)
        """
        pass

    @abstractmethod
    def middleware_request(self):
        """
        The middleware-specific source of request data (for middleware-specific custom hooks)
        """
        pass


class DictRequest(Request):
    '''
    Basic dictionary request that just takes in a dictionary of headers, and a dictionary
    of request properties. Primarily for testing.
    '''

    def __init__(self, headers, props={}):
        self._headers = headers
        self._props = props
        self._keymap = {k.lower(): k for k in self._headers.keys()}

    def header(self, key):
        lookup_key = key.lower()
        if lookup_key not in self._keymap:
            return None
        lookup_key = self._keymap[lookup_key]
        return self._headers[lookup_key]

    def method(self):
        return self._props['method']

    def scheme(self):
        return self._props['scheme']

    def host(self):
        return self._props['host']

    def path(self):
        return self._props['path']

    def query(self):
        return self._props['query']

    def middleware_request(self):
        return {
            'headers': self._headers,
            'props': self._props
        }
