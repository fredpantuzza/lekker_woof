import logging
from typing import Any

import dash
import dash_bootstrap_components as bootstrap
from dash import Dash, Output, Input, ctx, callback, dcc
from dash.exceptions import PreventUpdate

from components import page_callback
from components.page_callback import Action, CallbackData
from controls.types import UserMessage, user_message_to_callback_output
from pages import training_profile, customer_list, customer_profile, training_list, subscription_profile

app = Dash(__name__, external_stylesheets=[bootstrap.themes.FLATLY], suppress_callback_exceptions=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Ids:
    @classmethod
    def element(cls, component: Any) -> dict:
        return {
            'page': 'main_page',
            'component': component
        }


class Controller:
    id_body_container = Ids.element('BodyContainer')
    id_training_list_link = Ids.element('TrainingListLink')
    id_customers_list_link = Ids.element('CustomersListLink')
    id_new_customer_link = Ids.element('NewCustomerLink')
    id_user_message = Ids.element('ToastUserMessage')

    @staticmethod
    @callback(
        output=dict(
            body=Output(id_body_container, 'children'),
            user_message=Output(id_user_message, 'children'),
            user_message_header=Output(id_user_message, 'header'),
            user_message_icon=Output(id_user_message, 'icon'),
            user_message_color=Output(id_user_message, 'color'),
            user_message_open=Output(id_user_message, 'is_open'),
        ),
        inputs=dict(
            customers_list_clicks=Input(id_customers_list_link, 'n_clicks'),
            new_customer_clicks=Input(id_new_customer_link, 'n_clicks'),
            training_list_clicks=Input(id_training_list_link, 'n_clicks'),
            callback_data=Input(page_callback.id_page_callback_store, 'data'),
        ),
        prevent_initial_call=True)
    def main_callback(
            customers_list_clicks: int, new_customer_clicks: int, training_list_clicks: int,
            callback_data: CallbackData) -> dict:
        # TODO confirm with user before leaving modified form.
        triggered_id = ctx.triggered_id
        if triggered_id is None:
            raise PreventUpdate
        logger.debug(f'main_callback triggered by {triggered_id}')

        output = dict(
            body=dash.no_update,
            user_message=dash.no_update,
            user_message_header=dash.no_update,
            user_message_icon=dash.no_update,
            user_message_color=dash.no_update,
            user_message_open=dash.no_update,
        )

        if triggered_id == Controller.id_customers_list_link:
            output['body'] = customer_list.layout()

        elif triggered_id == Controller.id_new_customer_link:
            output['body'] = customer_profile.layout(dog_id=None)

        elif triggered_id == Controller.id_training_list_link:
            output['body'] = training_list.layout()

        elif triggered_id == page_callback.id_page_callback_store:
            if callback_data is None:
                raise PreventUpdate('Initial callback')
            action = callback_data['action']
            if action == Action.SHOW_USER_MESSAGE:
                assert 'user_message' in callback_data
                user_message: UserMessage = callback_data['user_message']
                output.update(**user_message_to_callback_output(user_message))
            elif action == Action.OPEN_CUSTOMER:
                assert 'entity_id' in callback_data
                output['body'] = customer_profile.layout(dog_id=callback_data['entity_id'])
            elif action == Action.OPEN_TRAINING:
                assert 'entity_id' in callback_data
                output['body'] = training_profile.layout(training_id=callback_data['entity_id'])
            elif action == Action.OPEN_SUBSCRIPTION:
                assert 'entity_id' in callback_data
                output['body'] = subscription_profile.layout(subscription_id=callback_data['entity_id'])
            else:
                assert False, f'Unexpected action {action.name}'

        return output


app.layout = bootstrap.Container(
    [
        bootstrap.NavbarSimple(
            [
                bootstrap.NavItem(bootstrap.NavLink('Trainings', id=Controller.id_training_list_link, href='#')),
                bootstrap.NavItem(bootstrap.NavLink('Customers', id=Controller.id_customers_list_link, href='#')),
                bootstrap.NavItem(bootstrap.NavLink('New customer', id=Controller.id_new_customer_link, href='#')),
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
            id=page_callback.id_page_callback_store
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

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    app.run(debug=True)
