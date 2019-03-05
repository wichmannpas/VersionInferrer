from json import JSONEncoder


class CustomJSONEncoder(JSONEncoder):
    def default(self, o):
        if hasattr(o, 'serialize'):
            return o.serialize()
        if isinstance(o, set):
            return list(o)
        return super().default(o)
