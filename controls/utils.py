import json
from typing import Any, TypeVar

import pandas as pd
from bidict import bidict

_T = TypeVar('_T')


def get_single_row_as_dict(df: pd.DataFrame) -> dict:
    records = df.to_dict('records')
    if len(records) != 1:
        raise ValueError(f'Expected 1 and only 1 record, but found {len(records)}')
    return records[0]


def flatten(ls: list[list[_T]]) -> list[_T]:
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
