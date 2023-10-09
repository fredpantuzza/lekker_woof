import functools
from enum import IntEnum
from typing import TypedDict

from dash import callback, Output

from controls.types import UserMessage

id_page_callback_store = 'page_callback_store'


class Action(IntEnum):
    SHOW_USER_MESSAGE = 1
    OPEN_CUSTOMER = 2
    OPEN_TRAINING = 3
    OPEN_SUBSCRIPTION = 4


# TODO use NotRequired after upgrading to py 3.11
class CallbackData(TypedDict, total=False):
    action: Action
    entity_id: int
    user_message: UserMessage


def page_callback(action: Action, *args, **kwargs):
    def decorator(callback_function):
        @functools.wraps(callback_function)
        @callback(
            Output(id_page_callback_store, 'data', allow_duplicate=True),
            prevent_initial_call=True, *args, **kwargs)
        def app_callback_wrapper(*func_args, **func_kwargs) -> CallbackData:
            # Call the original callback function with the Output object
            result: CallbackData = callback_function(*func_args, **func_kwargs)
            result['action'] = action
            return result

        return app_callback_wrapper

    return decorator
