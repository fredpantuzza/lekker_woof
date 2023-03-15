import json
from typing import Any, Callable

from bidict import bidict


def flatten(ls: list[list]) -> list:
    return [item for sublist in ls for item in sublist]


class BidictDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, object_hook=self.__object_hook)

    @staticmethod
    def __object_hook(dct) -> Any:
        if '__bidict__' in dct:
            return bidict(dct['data'])
        return dct


class BidictEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, bidict):
            return {'__bidict__': True, 'data': obj._fwdm}
        return super().default(obj)
