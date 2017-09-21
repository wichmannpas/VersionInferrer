from abc import abstractmethod, ABCMeta

from backend.model import Model


class Backend(metaclass=ABCMeta):
    """A base class for database backends."""
    @abstractmethod
    def store(self, element: Model) -> bool:
        """
        Insert or update an instance of a Model subclass.

        Returns whether a change has been made.
        """


class BackendException(Exception):
    """An exception occuring in a backend."""
