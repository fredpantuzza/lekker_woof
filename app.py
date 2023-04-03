import logging
from typing import Any

import dash_bootstrap_components as bootstrap
from dash import Dash, html, Output, Input, ctx, State, callback, ALL
from dash.exceptions import PreventUpdate

import pages.customer_profile as profile
import pages.customers_list as customer_list
from components.dict_form import Ids as FormIds, DataStore as FormData
from controls.data_provider import DataProvider

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
    id_user_message = Ids.element('ToastUserMessage')

    __row_selection_enabled = 'single'
    __row_selection_disabled = False

    __logger = logging.getLogger(__name__)

    @staticmethod
    @callback(
        Output(id_body_container, 'children'),
        Output(customer_list.Controller.id_customers_data_table, 'row_selectable'),
        inputs=dict(
            selected_dog_ids=Input(customer_list.Controller.id_customers_data_table, 'selected_row_ids'),
            new_customer_clicks=Input(id_new_customer_link, 'n_clicks'),
            customer_form_state=State(profile.Controller.id_store_is_modified, 'data')),
        prevent_initial_callback=True)
    def on_selected_customer_changed(selected_dog_ids: list, new_customer_clicks: int,
                                     is_customer_modified: bool) -> (html.Div, str):
        triggered_id = ctx.triggered_id
        if triggered_id is None:
            raise PreventUpdate
        if is_customer_modified:
            pass  # TODO confirm
            raise PreventUpdate
        if triggered_id == customer_list.Controller.id_customers_data_table:
            assert len(selected_dog_ids) == 1
            return profile.layout(dog_id=selected_dog_ids[0]), Controller.__row_selection_enabled
        elif triggered_id == Controller.id_new_customer_link:
            return profile.layout(dog_id=None), Controller.__row_selection_disabled

    @staticmethod
    @callback(Output(id_user_message, 'children'), Output(id_user_message, 'is_open'),
              inputs=dict(
                  save_button_clicks=Input(profile.Controller.id_save_button, 'n_clicks'),
                  customer_data_json=State(FormIds.form_data_store(profile.Controller.id_customer_data_form), 'data'),
                  dogs_json=State(FormIds.form_data_store(profile.Controller.id_dog_form, ALL), 'data'),
                  persons_json=State(FormIds.form_data_store(profile.Controller.id_person_form, ALL), 'data')),
              prevent_initial_callback=True)
    def save_customer(save_button_clicks: int, customer_data_json: str, dogs_json: str,
                      persons_json: str) -> tuple[str, bool]:
        if not save_button_clicks:
            raise PreventUpdate

        Controller.__logger.info(
            f'Saving customer: customer_data={customer_data_json} dogs={dogs_json} persons={persons_json}')

        def show_user_message(message: str) -> tuple[str, bool]:
            return message, True

        data_provider = DataProvider()
        try:
            customer_data = FormData.from_json(customer_data_json)
            customer_data.validate()
            if customer_data.is_insertion:
                customer_id = data_provider.insert_customer(customer_data.data)
            else:
                customer_id = customer_data.data['customer_id']
                data_provider.update_customer(customer_data.data)

            for dog_json in dogs_json:
                dog = FormData.from_json(dog_json)
                dog.validate()
                if dog.is_insertion:
                    data_provider.insert_dog(dog.data, customer_id=customer_id)
                else:
                    data_provider.update_dog(dog.data)

            for person_json in persons_json:
                person = FormData.from_json(person_json)
                person.validate()
                if person.is_insertion:
                    data_provider.insert_person(person.data, customer_id=customer_id)
                else:
                    data_provider.update_person(person.data)

            data_provider.commit()
            return show_user_message('Saved successfully')
        except RuntimeError as e:
            data_provider.rollback()
            return show_user_message(f'Error saving customer. {e}')

        # TODO reset state
        # TODO update list of customers and select new one


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
        bootstrap.Toast('', id=Controller.id_user_message, is_open=False, dismissable=True),
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
    fluid=True)

if __name__ == '__main__':
    app.run(debug=True)
