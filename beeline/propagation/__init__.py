import abc
import beeline


class PropagationContext(object):
    def __init__(self, trace_id, parent_id, trace_fields={}):
        # FIXME: Better name for context
        self.trace_id = trace_id
        self.parent_id = parent_id
        self.trace_fields = trace_fields


class PropagationHeaders(object):
    @abc.abstractmethod
    def Get(self, key):
        """
        Get the value associated with the specified key, transformed as necessary for the
        transport and middleware.
        """
        return
