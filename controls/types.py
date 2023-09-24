import json
from typing import Dict, List, TypedDict


class Customer:
    def __init__(self, customer_data: Dict = {}, dogs: List[Dict] = [None], persons: List[Dict] = [None]):
        self.customer_data = customer_data
        self.dogs = dogs
        self.persons = persons

    @classmethod
    def from_json(cls, json_str: str):
        customer_dict = json.loads(json_str)
        return cls(**customer_dict)


class UserMessage(TypedDict):
    message: str
    header: str
    type: str


def user_message_to_callback_output(user_message: UserMessage) -> dict:
    icon = 'success' if user_message['type'] == 'success' else 'danger'
    color = 'success' if user_message['type'] == 'success' else 'danger'
    return dict(
        user_message=user_message['message'],
        user_message_header=user_message['header'],
        user_message_icon=icon,
        user_message_color=color,
        user_message_open=True,
    )
