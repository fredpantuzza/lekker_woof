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


class UserMessage:
    def __init__(self, message: str, header: str, type: str):
        self.message = message
        self.header = header
        self.icon = 'success' if type == 'success' else 'danger'
        self.color = 'success' if type == 'success' else 'danger'

    def to_callback_output(self) -> dict:
        return dict(
            user_message=self.message,
            user_message_header=self.header,
            user_message_icon=self.icon,
            user_message_color=self.color,
            user_message_open=True,
        )
