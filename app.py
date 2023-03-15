from typing import Any

import dash_bootstrap_components as bootstrap
from dash import Dash, html, Output, Input, ctx, State
from dash.exceptions import PreventUpdate

import pages.customer_profile
import pages.customers_list
from components.dict_form import FormState

app = Dash(__name__, external_stylesheets=[bootstrap.themes.FLATLY])
app.config.suppress_callback_exceptions = True


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

    __row_selection_enabled = 'single'
    __row_selection_disabled = False

    @staticmethod
    @app.callback(
        Output(id_body_container, 'children'),
        Output(pages.customers_list.Controller.id_customers_data_table, 'row_selectable'),
        inputs=dict(selected_dog_ids=Input(pages.customers_list.Controller.id_customers_data_table, 'selected_row_ids'),
                    new_customer_clicks=Input(id_new_customer_link, 'n_clicks'),
                    customer_form_state=State(pages.customer_profile.Controller.id_overall_form_state, 'data')),
        prevent_initial_callback=True)
    def on_selected_customer_changed(selected_dog_ids: list, new_customer_clicks: int,
                                     customer_form_state: FormState) -> (html.Div, str):
        triggered_id = ctx.triggered_id
        if triggered_id is None:
            raise PreventUpdate
        # TODO check current state with user
        if triggered_id == pages.customers_list.Controller.id_customers_data_table:
            assert len(selected_dog_ids) == 1
            return pages.customer_profile.layout(dog_id=selected_dog_ids[0]), Controller.__row_selection_enabled
        elif triggered_id == Controller.id_new_customer_link:
            return pages.customer_profile.layout(dog_id=None), Controller.__row_selection_disabled


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
                pages.customers_list.layout(),
                id='MainPageCustomerList',
                class_name='m-1',
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
                        pages.customer_profile.layout(dog_id=None)
                    ],
                    id=Controller.id_body_container,
                ),
                class_name='my-2',
            )
        ),
    ],
    fluid=True)

if __name__ == '__main__':
    app.run(debug=True)
