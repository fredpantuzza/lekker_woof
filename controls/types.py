import json
from typing import Dict, List


class Customer:
    def __init__(self, customer_data: Dict = {}, dogs: List[Dict] = [None], persons: List[Dict] = [None]):
        self.customer_data = customer_data
        self.dogs = dogs
        self.persons = persons

    @classmethod
    def from_json(cls, json_str: str):
        customer_dict = json.loads(json_str)
        return cls(**customer_dict)
