import json


class Get:
    def __init__(self, parent):
        self.parent: Cache = parent

    def __getattribute__(self, key):
        parent: Cache = super().__getattribute__("parent")
        if key in parent.data.keys():
            _get_item = super().__getattribute__("_get_item")
            return lambda: _get_item(key)
        return super().__getattribute__(key)

    def _get_item(self, key):
        return self.parent.data.get(key)


class Set:
    def __init__(self, parent):
        self.parent: Cache = parent

    def __getattribute__(self, key):
        if key in super().__getattribute__("__dict__"):
            return super().__getattribute__(key)
        _set_item = super().__getattribute__("_set_item")
        return lambda value: _set_item(key, value)

    def _set_item(self, key, value):
        self.parent._data[key] = value


class Cache:
    _data = {}

    def __init__(self):
        self.get: Get = Get(self)
        self.set: Set = Set(self)

    @property
    def data(self):
        return self._data

    def __str__(self):
        return json.dumps(self._data, indent=4)
