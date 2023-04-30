import logging
from typing import Any

import dash
import dash_bootstrap_components as bootstrap
from dash import Dash, html, Output, Input, ctx, State, callback, ALL
from dash.exceptions import PreventUpdate

import pages.customer_profile as profile
import pages.customers_list as customer_list
from components.dict_form import Ids as FormIds
from controls.types import UserMessage

app = Dash(__name__, external_stylesheets=[bootstrap.themes.FLATLY])
app.config.suppress_callback_exceptions = True

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
    id_new_customer_link = Ids.element('NewCustomerLink')
    id_user_message = Ids.element('ToastUserMessage')

    @staticmethod
    @callback(
        output=dict(
            body=Output(id_body_container, 'children'),
            customer_list=Output(customer_list.Controller.id_customers_data_table, 'data'),
            user_message=Output(id_user_message, 'children'),
            user_message_header=Output(id_user_message, 'header'),
            user_message_icon=Output(id_user_message, 'icon'),
            user_message_color=Output(id_user_message, 'color'),
            user_message_open=Output(id_user_message, 'is_open')),
        inputs=dict(
            selected_dog_ids=Input(customer_list.Controller.id_customers_data_table, 'selected_row_ids'),
            new_customer_clicks=Input(id_new_customer_link, 'n_clicks'),
            save_button_clicks=Input(profile.Controller.id_save_button, 'n_clicks'),
            customer_data_json=State(FormIds.form_data_store(profile.Controller.id_customer_data_form), 'data'),
            dogs_json=State(FormIds.form_data_store(profile.Controller.id_dog_form, ALL), 'data'),
            persons_json=State(FormIds.form_data_store(profile.Controller.id_person_form, ALL), 'data')),
        prevent_initial_callback=True)
    def main_callback(
            selected_dog_ids: list, new_customer_clicks: int, save_button_clicks: int, customer_data_json: str,
            dogs_json: str, persons_json: str) -> dict:
        # TODO confirm with user before leaving modified form.
        #  customer_form_state=State(profile.Controller.id_store_is_modified, 'data')
        triggered_id = ctx.triggered_id
        if triggered_id is None:
            raise PreventUpdate
        logger.debug(f'main_callback triggered by {triggered_id}')

        output = dict(
            body=dash.no_update,
            customer_list=dash.no_update,
            user_message=dash.no_update,
            user_message_header=dash.no_update,
            user_message_icon=dash.no_update,
            user_message_color=dash.no_update,
            user_message_open=dash.no_update,
        )

        if triggered_id == customer_list.Controller.id_customers_data_table:
            assert len(selected_dog_ids) == 1
            output['body'] = profile.layout(dog_id=selected_dog_ids[0])

        elif triggered_id == Controller.id_new_customer_link:
            output['body'] = profile.layout(dog_id=None)

        elif triggered_id == profile.Controller.id_save_button:
            save_customer_result = profile.Controller.save_customer(
                customer_data_json=customer_data_json, dogs_json=dogs_json, persons_json=persons_json)
            user_message: UserMessage = save_customer_result['user_message']
            output.update(**user_message.to_callback_output())
            if 'dog_id' in save_customer_result:
                output['body'] = profile.layout(dog_id=save_customer_result['dog_id'])
                output['customer_list'] = customer_list.Controller.load_customers()

        return output


app.layout = bootstrap.Container(
    [
        bootstrap.NavbarSimple(
            [
                bootstrap.NavItem(bootstrap.NavLink('New customer', id=Controller.id_new_customer_link, href='#'))
            ],
            brand='Lekker Woof',
            color='primary',
            dark=True
        ),
        bootstrap.Row(
            bootstrap.Col(
                customer_list.layout(),
                id='MainPageCustomerList',
                class_name='m-1',
            )
        ),
        bootstrap.Row(
            bootstrap.Col(
                bootstrap.Toast(
                    '', id=Controller.id_user_message,
                    is_open=False, dismissable=True, color='primary',
                    className='position-fixed top-0 end-0 m-3 zx-toast')
            )
        ),
        bootstrap.Row(
            bootstrap.Col(
                bootstrap.Container(
                    [
                        html.H4('Welcome back to another beautiful day at work!'),
                        html.P('''
                        Start by creating a new customer below, or select an existing one from the table above to view 
                        and edit its details.
                        '''),
                        profile.layout(dog_id=None)
                    ],
                    id=Controller.id_body_container,
                ),
                class_name='my-2',
            )
        ),
    ],
    fluid=True,
    className='p-0')

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    app.run(debug=True)
