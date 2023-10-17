import functools
from enum import Enum
from typing import Any, Callable, TypedDict

from dash import callback, Output

from controls.types import UserMessage

id_location = 'global_location'
id_user_message_store = 'user_message_store'


class Pages(str, Enum):
    training_list_path = '/trainings'
    customers_list_path = '/customers'
    new_customer_path = '/new_customer_path'

    training_profile_path_param = 'training'
    customer_profile_path_param = 'customer'
    subscription_profile_path_param = 'subscription'


class MultiPageCallbackData(TypedDict, total=False):
    user_message: UserMessage
    page_param_value: Any


def change_page_callback(new_page: Pages, *args, **kwargs):
    def decorator(callback_function: Callable[[...], MultiPageCallbackData]):
        @functools.wraps(callback_function)
        @callback(
            Output(id_location, 'pathname', allow_duplicate=True),
            Output(id_user_message_store, 'data', allow_duplicate=True),
            prevent_initial_call=True, *args, **kwargs)
        def app_callback_wrapper(*func_args, **func_kwargs) -> tuple[str, UserMessage]:
            # Call the original callback function with the Output object
            result = callback_function(*func_args, **func_kwargs)
            new_page_path = new_page.value
            if 'page_param_value' in result:
                page_param_value = result['page_param_value']
                new_page_path = f'/{new_page_path}/{page_param_value}'
            user_message = result.get('user_message')
            return new_page_path, user_message

        return app_callback_wrapper

    return decorator


def user_message_callback(*args, **kwargs):
    def decorator(callback_function: Callable[[...], UserMessage]):
        @functools.wraps(callback_function)
        @callback(
            Output(id_user_message_store, 'data', allow_duplicate=True),
            prevent_initial_call=True, *args, **kwargs)
        def app_callback_wrapper(*func_args, **func_kwargs) -> UserMessage:
            # Call the original callback function with the Output object
            result = callback_function(*func_args, **func_kwargs)
            return result

        return app_callback_wrapper

    return decorator
