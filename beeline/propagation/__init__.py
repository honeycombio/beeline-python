from abc import ABC, abstractmethod
import beeline


class PropagationContext(object):
    def __init__(self, trace_id, parent_id, trace_fields={}):
        # FIXME: Better name for context
        self.trace_id = trace_id
        self.parent_id = parent_id
        self.trace_fields = trace_fields


class Request(ABC):
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
