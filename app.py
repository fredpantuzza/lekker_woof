import logging
from typing import Any

import dash_bootstrap_components as bootstrap
from dash import callback, Dash, dcc, html, Input, Output

from components import page_callback
from components.page_callback import Pages
from controls import utils
from controls.types import user_message_to_callback_output, UserMessage
from pages import customer_list, customer_profile, subscription_profile, training_list, training_profile

app = Dash(__name__, external_stylesheets=[bootstrap.themes.FLATLY], suppress_callback_exceptions=True)

logger = logging.getLogger(__name__)


class Ids:
    @classmethod
    def element(cls, component: Any) -> dict:
        return {
            'page': 'main_page',
            'component': component
        }


class Controller:
    id_body_container = Ids.element('BodyContainer')
    id_user_message = Ids.element('ToastUserMessage')

    @staticmethod
    @callback(
        output=dict(
            user_message=Output(id_user_message, 'children'),
            user_message_header=Output(id_user_message, 'header'),
            user_message_icon=Output(id_user_message, 'icon'),
            user_message_color=Output(id_user_message, 'color'),
            user_message_open=Output(id_user_message, 'is_open'),
        ),
        inputs=dict(
            user_message=Input(page_callback.id_user_message_store, 'data'),
        ),
        prevent_initial_call=True)
    def show_user_message(user_message: UserMessage) -> dict:
        return user_message_to_callback_output(user_message)

    @staticmethod
    @callback(
        Output(id_body_container, 'children'),
        inputs=dict(
            url_pathname=Input(page_callback.id_location, 'pathname'),
        ),
        prevent_initial_call=True)
    def main_callback(url_pathname: str) -> Any:
        logger.debug(f'Loading page: {url_pathname}')
        # TODO confirm with user before leaving modified form.
        if url_pathname == Pages.customers_list_path:
            return customer_list.layout()

        if url_pathname == Pages.new_customer_path:
            return customer_profile.layout(dog_id=None)

        if url_pathname == Pages.training_list_path:
            return training_list.layout()

        # Parametrized pages
        url_params = utils.url_path_to_param_dict(url_pathname)
        # TODO check single element
        if Pages.training_profile_path_param.value in url_params:
            training_id = url_params[Pages.training_profile_path_param.value]
            return training_profile.layout(training_id=training_id)

        if Pages.customer_profile_path_param.value in url_params:
            dog_id = url_params[Pages.customer_profile_path_param.value]
            return customer_profile.layout(dog_id=dog_id)

        if Pages.subscription_profile_path_param.value in url_params:
            subscription_id = url_params[Pages.subscription_profile_path_param.value]
            return subscription_profile.layout(subscription_id=subscription_id)

        logger.error(f'Unexpected URL params: {url_params}')
        return html.Div('Something just went terribly wrong!')


app.layout = bootstrap.Container(
    [
        dcc.Location(id=page_callback.id_location),
        bootstrap.NavbarSimple(
            [
                bootstrap.NavItem(bootstrap.NavLink('Trainings', href=Pages.training_list_path)),
                bootstrap.NavItem(bootstrap.NavLink('Customers', href=Pages.customers_list_path)),
                bootstrap.NavItem(bootstrap.NavLink('New customer', href=Pages.new_customer_path)),
            ],
            brand='Lekker Woof',
            color='primary',
            dark=True
        ),
        bootstrap.Row(
            bootstrap.Col(
                bootstrap.Toast(
                    '', id=Controller.id_user_message,
                    is_open=False, dismissable=True, color='primary',
                    className='position-fixed top-0 end-0 m-3 zx-toast')
            )
        ),
        dcc.Store(
            id=page_callback.id_user_message_store
        ),
        bootstrap.Row(
            bootstrap.Col(
                customer_list.layout(),
                id=Controller.id_body_container,
                class_name='mx-auto',
            )
        ),
    ],
    fluid=True,
    className='p-0 m-0')


def run():
    app.run(debug=True)
