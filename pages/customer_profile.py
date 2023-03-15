import logging
from enum import Enum
from typing import Any, Optional

import dash_bootstrap_components as bootstrap
from bidict import bidict
from dash import callback, State, Input, Output, ALL, html, dcc
from dash.exceptions import PreventUpdate

from components.dict_form import DictFormAIO, DataStore as FormData, FormState, FieldType, Ids as FormIds
from controls.data_provider import DataProvider
from controls.types import Customer


class Sex(str, Enum):
    MALE = 'Male'
    FEMALE = 'Female'


class Ids:
    @classmethod
    def element(cls, component_type: Any, index: Any = '') -> dict:
        return {
            'page': 'customer_profile',
            'component': component_type,
            'index': index
        }

    @classmethod
    def customer_state(cls, customer_id: Any) -> dict:
        return cls.element('CustomerFormState', index=customer_id)


class Controller:
    customer_data_fields_config = {
        'customer_id': {'label': 'ID', 'type': FieldType.STORE},
        'address': {'label': 'Address', 'type': FieldType.TEXT},
        'balance_in_eur': {'label': 'Cash balance', 'type': FieldType.TEXT},  # TODO format currency
        'customer_notes': {'label': 'Notes', 'type': FieldType.TEXTAREA},
        'customer_created_timestamp': {'label': 'Registration date', 'type': FieldType.STORE}
    }

    dog_fields_config = {
        'dog_id': {'label': 'ID', 'type': FieldType.TEXT, 'readonly': True},
        'dog_name': {'label': 'Name', 'type': FieldType.TEXT},
        'birth_date': {'label': 'Birth date', 'type': FieldType.DATE},
        'is_male': {'label': 'Sex', 'type': FieldType.RADIO,
                    'display_value_converter_bidict': bidict({1: Sex.MALE, 0: Sex.FEMALE}),
                    'options': [sex for sex in Sex]},
        'breed': {'label': 'Breed', 'type': FieldType.TEXT},
        'dog_created_timestamp': {'label': 'Registration date', 'type': FieldType.TEXT, 'readonly': True},
        'dog_notes': {'label': 'Notes', 'type': FieldType.TEXTAREA}
    }

    person_fields_config = {
        'person_id': {'label': 'ID', 'type': FieldType.STORE},
        'person_name': {'label': 'Customer name', 'type': FieldType.TEXT},
        'phone1': {'label': 'Phone', 'type': FieldType.TEXT},  # TODO type for phone? Mask?
        'phone2': {'label': 'Phone (2)', 'type': FieldType.TEXT},
        'email_address': {'label': 'E-mail', 'type': FieldType.TEXT},  # TODO type for email
        'person_created_timestamp': {'label': 'Registration date', 'type': FieldType.STORE}
    }

    id_overall_form_state = 'CustomerFormState'
    id_customer_data_form = 'CustomerDataForm'
    id_dog_form = 'DogForm'
    id_dogs_tabs = Ids.element('Tabs', 'dogs')
    id_add_dog_tab = 'add-dog-tab'
    id_person_form = 'PersonForm'
    id_persons_tabs = Ids.element('Tabs', 'persons')
    id_save_button = Ids.element('Button', 'save-customer')
    id_user_message_container = Ids.element('Container', 'user-message')

    __last_new_dog_id = 0
    __last_new_person_id = 0

    __default_dog_name = 'New Doggo'

    __logger = logging.getLogger(__name__)

    @staticmethod
    def get_customer_by_dog_id(dog_id: int) -> Customer:
        data_provider = DataProvider()
        return data_provider.get_customer_by_dog_id(dog_id=dog_id)

    @staticmethod
    @callback(Output(id_overall_form_state, 'data'),
              inputs=dict(
                  customer_data_form_data_json=Input(FormIds.form_data_store(form_id=id_customer_data_form), 'data'),
                  dogs_form_data_json=Input(FormIds.form_data_store(form_id=id_dog_form, form_index=ALL), 'data'),
                  persons_form_data_json=Input(FormIds.form_data_store(form_id=id_person_form, form_index=ALL), 'data')
              ))
    def compute_overall_form_state(customer_data_form_data_json: str, dogs_form_data_json: list[str],
                                   persons_form_data_json: list[str]) -> FormState:
        customer_data_form_data = FormData.from_json(customer_data_form_data_json)
        dogs_form_data = [FormData.from_json(data_json) for data_json in dogs_form_data_json]
        persons_form_data = [FormData.from_json(data_json) for data_json in persons_form_data_json]

        # Initialize with customer_data state, which will only be INSERTED if a new customer altogether
        overall_form_state = customer_data_form_data.state
        for form_data in dogs_form_data + persons_form_data:
            if overall_form_state == FormState.INSERTED or overall_form_state == FormState.UPDATED:
                # there's no getting away from these states atm
                continue
            assert overall_form_state == FormState.UNCHANGED
            if form_data.state == FormState.UPDATED or form_data.state == FormState.INSERTED:
                # even when new dog or person is inserted, the customer as a whole is being updated
                overall_form_state = FormState.UPDATED

        return overall_form_state

    @staticmethod
    @callback(Output(id_dogs_tabs, 'children'),
              Output(id_dogs_tabs, 'active_tab'),
              inputs=dict(active_tab=Input(id_dogs_tabs, 'active_tab'),
                          dogs_tabs=Input(id_dogs_tabs, 'children')))
    def on_active_tab_changed(active_tab: str, dogs_tabs: list[bootstrap.Tab]) -> tuple[list[bootstrap.Tab], str]:
        if not dogs_tabs:
            raise PreventUpdate
        if active_tab == 'None':
            # make sure there's always a dog selected
            assert len(dogs_tabs) > 0
            return dogs_tabs, dogs_tabs[0]['props']['tab_id']

        if active_tab == Controller.id_add_dog_tab:
            return Controller.__handle_new_dog_tab_clicked(dogs_tabs)
        else:
            raise PreventUpdate

    @staticmethod
    def __handle_new_dog_tab_clicked(dogs_tabs: list[bootstrap.Tab]) -> tuple:
        new_dog_tab = Controller.make_dog_tab(dog=None, initial_form_state=FormState.INSERTED)
        dogs_tabs.insert(len(dogs_tabs) - 1, new_dog_tab)
        return dogs_tabs, new_dog_tab.tab_id

    @classmethod
    def make_dog_tab(cls, dog: Optional[dict], initial_form_state: FormState = FormState.UNCHANGED) -> bootstrap.Tab:
        dog = dog or {
            'dog_id': cls.__generate_new_dog_id(),
            'dog_name': cls.__default_dog_name,
        }
        # TODO update label when name is changed
        return bootstrap.Tab(
            id=Ids.element('DogTab', dog['dog_id']),
            className='p-3 border border-top-0 border-secondary',
            label=dog['dog_name'],
            tab_id=str(dog['dog_id']),
            children=DictFormAIO(
                data=dog,
                fields_config=cls.dog_fields_config,
                initial_form_state=initial_form_state,
                form_id=cls.id_dog_form,
                form_index=dog['dog_id']))

    @classmethod
    def make_person_panel(cls, person: Optional[dict],
                          initial_form_state: FormState = FormState.UNCHANGED) -> html.Div:
        if person is None:
            person = {
                'person_id': cls.__generate_new_person_id(),
            }
        return html.Div(
            id=Ids.element('PersonContainer', person['person_id']),
            className='mt-2 p-3 border border-secondary',
            children=DictFormAIO(
                data=person,
                fields_config=Controller.person_fields_config,
                initial_form_state=initial_form_state,
                form_id=Controller.id_person_form,
                form_index=person['person_id']))

    @staticmethod
    @callback(Output(id_user_message_container, 'children'),
              inputs=dict(save_button_clicks=Input(id_save_button, 'n_clicks'),
                          customer_data_json=State(FormIds.form_data_store(id_customer_data_form), 'data'),
                          dogs_json=State(FormIds.form_data_store(id_dog_form, ALL), 'data'),
                          persons_json=State(FormIds.form_data_store(id_person_form, ALL), 'data')),
              prevent_initial_callback=True)
    def save_customer(save_button_clicks: int, customer_data_json: str, dogs_json: str, persons_json: str):
        if not save_button_clicks:
            raise PreventUpdate

        Controller.__logger.info(
            f'Saving customer: customer_data={customer_data_json} dogs={dogs_json} persons={persons_json}')

        data_provider = DataProvider()

        # TODO try/catch
        customer_data = FormData.from_json(customer_data_json)
        if customer_data.state == FormState.INSERTED:
            customer_id = data_provider.insert_customer(customer_data.data)
        elif customer_data.state == FormState.UPDATED:
            customer_id = customer_data.data['customer_id']
            data_provider.update_customer(customer_data.data)

        for dog_json in dogs_json:
            dog = FormData.from_json(dog_json)
            if dog.state == FormState.INSERTED:
                data_provider.insert_dog(dog.data, customer_id=customer_id)
            elif dog.state == FormState.UPDATED:
                data_provider.update_dog(dog.data)

        for person_json in persons_json:
            person = FormData.from_json(person_json)
            if person.state == FormState.INSERTED:
                data_provider.insert_person(person.data, customer_id=customer_id)
            elif person.state == FormState.UPDATED:
                data_provider.update_person(person.data)

        data_provider.commit()

        # TODO reset state
        # TODO update list of customers and select new one
        # TODO show success message (or error)

        return f'clicked={save_button_clicks} ' \
               f'customer_data={customer_data_json} ' \
               f'dogs={dogs_json} ' \
               f'persons={persons_json}'

    @classmethod
    def __generate_new_dog_id(cls) -> str:
        cls.__last_new_dog_id += 1
        return f'N{cls.__last_new_dog_id}'

    @classmethod
    def __generate_new_person_id(cls) -> str:
        cls.__last_new_person_id += 1
        return f'N{cls.__last_new_person_id}'


def layout(dog_id=None) -> html.Div:
    customer, initial_form_state = (Customer(), FormState.INSERTED) if dog_id is None \
        else (Controller.get_customer_by_dog_id(dog_id=dog_id), FormState.UNCHANGED)

    data_storage = [
        dcc.Store(id=Controller.id_overall_form_state)
    ]

    add_dog_tab = bootstrap.Tab(
        'Au Au! New dog in the oven...',
        id=Ids.element('DogTab', Controller.id_add_dog_tab),
        className='p-3 border border-top-0 border-secondary',
        tab_class_name=Controller.id_add_dog_tab,
        label='+',
        tab_id=Controller.id_add_dog_tab)

    row_dogs_tabs = bootstrap.Row(
        bootstrap.Col(
            bootstrap.Tabs(
                [Controller.make_dog_tab(dog, initial_form_state=initial_form_state) for dog in customer.dogs]
                + [add_dog_tab],
                id=Controller.id_dogs_tabs,
                active_tab=str(dog_id)
            )
        ),
    )

    row_customer_data = bootstrap.Row(
        bootstrap.Col(
            html.Div(
                DictFormAIO(
                    data=customer.customer_data,
                    fields_config=Controller.customer_data_fields_config,
                    initial_form_state=initial_form_state,
                    form_id=Controller.id_customer_data_form),
                className='mt-2 p-3 border border-secondary'
            )
        )
    )

    rows_persons = [
        bootstrap.Row(
            bootstrap.Col(
                Controller.make_person_panel(person, initial_form_state=initial_form_state)
            )
        )
        for person in customer.persons
    ]

    row_buttons = bootstrap.Row(
        bootstrap.Col(
            html.Div(
                bootstrap.Button(
                    'Save',
                    id=Controller.id_save_button,
                    className='btn-success'),
                className='d-flex flex-row-reverse mt-2 p-3'
            )
        )
    )

    children = data_storage + [row_dogs_tabs] + rows_persons + [row_customer_data, row_buttons, bootstrap.Row(
        bootstrap.Col(
            html.Div(id=Controller.id_user_message_container)
        ))]

    return html.Div(
        bootstrap.Container(
            children
        )
    )
