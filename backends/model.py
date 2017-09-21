from abc import ABCMeta


class Model(metaclass=ABCMeta):
    """An abstract superclass of all objects storable in the backend."""

    def __repr__(self) -> str:
        return "<{} '{}'>".format(str(self.__class__.__name__), str(self))
