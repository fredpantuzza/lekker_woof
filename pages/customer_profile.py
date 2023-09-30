import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

import dash_bootstrap_components as bootstrap
import pandas as pd
from bidict import bidict
from dash import callback, Input, Output, html, MATCH, State, ALL
from dash.dash_table import DataTable
from dash.exceptions import PreventUpdate

from components.dict_form import DictFormAIO, DataStore as FormData, FieldType, Ids as FormIds
from components.page_callback import page_callback, Action, CallbackData
from controls.data_provider import DataProvider
from controls.types import Customer, UserMessage

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Sex(str, Enum):
    MALE = 'Male'
    FEMALE = 'Female'


@dataclass
class DogProfile:
    subscriptions: pd.DataFrame
    individual_classes: pd.DataFrame


@dataclass
class CustomerProfile:
    customer: Customer
    dog_profile_by_id: dict[int, DogProfile]

    def get_dog_profile(self, dog_id: int) -> DogProfile:
        return self.dog_profile_by_id[dog_id] if dog_id in self.dog_profile_by_id \
            else DogProfile(subscriptions=pd.DataFrame(), individual_classes=pd.DataFrame())


class Ids:
    @classmethod
    def element(cls, component_type: Any, index: Any = '') -> dict:
        return {
            'page': 'customer_profile',
            'component': component_type,
            'index': index
        }

    @classmethod
    def dog_subscriptions_table(cls, dog_id: Any = '') -> dict:
        return cls.element('DataTable', f'DogSubscriptions-{dog_id}')


class Controller:
    customer_data_fields_config = {
        'customer_id': {'label': 'ID', 'type': FieldType.STORE},
        'address': {'label': 'Address', 'type': FieldType.TEXT},
        'balance_in_eur': {'label': 'Cash balance', 'type': FieldType.NUMBER, 'input_label_left': '€',
                           'required': True},
        'customer_notes': {'label': 'Notes', 'type': FieldType.TEXTAREA},
        'customer_created_timestamp': {'label': 'Registration date', 'type': FieldType.STORE}
    }

    # TODO break down address fields, one more email, notes to Short description of dog's behaviour, deactivate
    # TODO add cost per km 0.4 2x. Can we use maps distance API?
    # TODO long-term countability

    dog_fields_config = {
        'dog_id': {'label': 'ID', 'type': FieldType.TEXT, 'readonly': True},
        'dog_name': {'label': 'Name', 'type': FieldType.TEXT, 'required': True},
        'birth_date': {'label': 'Birth date', 'type': FieldType.DATE},
        'is_male': {'label': 'Sex', 'type': FieldType.RADIO,
                    'display_value_converter_bidict': bidict({1: Sex.MALE, 0: Sex.FEMALE}),
                    'options': [sex for sex in Sex], 'required': True},
        'breed': {'label': 'Breed', 'type': FieldType.TEXT, 'required': True},  # TODO dropdown
        'dog_created_timestamp': {'label': 'Registration date', 'type': FieldType.TEXT, 'readonly': True},
        'dog_notes': {'label': 'Notes', 'type': FieldType.TEXTAREA}
    }

    person_fields_config = {
        'person_id': {'label': 'ID', 'type': FieldType.STORE},
        'person_name': {'label': 'Customer name', 'type': FieldType.TEXT, 'required': True},
        'phone1': {'label': 'Phone', 'type': FieldType.TEXT},  # TODO type for phone? Mask?
        'phone2': {'label': 'Phone (2)', 'type': FieldType.TEXT},
        'email_address': {'label': 'E-mail', 'type': FieldType.EMAIL, 'required': True},
        'person_created_timestamp': {'label': 'Registration date', 'type': FieldType.STORE}
    }

    dog_subscriptions_columns = [
        {'id': 'training_name', 'name': 'Training'},
        {'id': 'training_price', 'name': 'Reg. price', 'type': 'numeric'},
        {'id': 'actual_price', 'name': 'Paid', 'type': 'numeric'},
        {'id': 'total_classes_online', 'name': '# Online', 'type': 'numeric'},
        {'id': 'taken_classes_online', 'name': '# Taken', 'type': 'numeric'},
        {'id': 'total_classes_in_person', 'name': '# In person', 'type': 'numeric'},
        {'id': 'taken_classes_in_person', 'name': '# Taken', 'type': 'numeric'},
        {'id': 'created_timestamp', 'name': 'Created on', 'type': 'datetime'},
    ]

    id_main_container = Ids.element('Container')
    id_dogs_tabs = Ids.element('Tabs', 'Dogs')
    id_persons_tabs = Ids.element('Tabs', 'persons')
    id_reset_button = Ids.element('Button', 'reset-customer')
    id_save_button = Ids.element('Button', 'save-customer')
    id_customer_data_form = 'CustomerForm'
    id_dog_form = 'DogForm'
    id_person_form = 'PersonForm'
    tab_id_add_dog_tab = 'AddDog'

    # Dog validation components
    __dog_forms_filter = dict(form_id=id_dog_form, form_index=MATCH)
    __id_field_dog_name = FormIds.field_element(field_type=FieldType.TEXT, field_name='dog_name', **__dog_forms_filter)
    __id_feedback_dog_name = FormIds.field_feedback(field_name='dog_name', **__dog_forms_filter)
    __id_field_breed = FormIds.field_element(field_type=FieldType.TEXT, field_name='breed', **__dog_forms_filter)
    __id_feedback_breed = FormIds.field_feedback(field_name='breed', **__dog_forms_filter)

    # Person validation components
    __person_forms_filter = dict(form_id=id_person_form, form_index=MATCH)
    __id_field_person_name = FormIds.field_element(field_type=FieldType.TEXT, field_name='person_name',
                                                   **__person_forms_filter)
    __id_feedback_person_name = FormIds.field_feedback(field_name='person_name', **__person_forms_filter)
    __id_field_email_address = FormIds.field_element(field_type=FieldType.EMAIL, field_name='email_address',
                                                     **__person_forms_filter)
    __id_feedback_email_address = FormIds.field_feedback(field_name='email_address', **__person_forms_filter)

    __last_new_dog_id = 0
    __last_new_person_id = 0

    __default_dog_name = 'New Doggo'

    @staticmethod
    def __id_dog_field(field_name: str):
        return FormIds.field_element(field_type=FieldType.TEXT, field_name=field_name,
                                     form_id=Controller.id_dog_form, form_index=MATCH)

    @staticmethod
    def get_profile_by_dog_id(dog_id: int) -> CustomerProfile:
        data_provider = DataProvider()
        customer = data_provider.get_customer_by_dog_id(dog_id=dog_id)

        dogs_profiles = {}
        for dog in customer.dogs:
            dog_id = dog['dog_id']
            subscriptions = data_provider.get_subscriptions_by_dog_id(dog_id=dog_id)
            dogs_profiles[dog_id] = DogProfile(
                subscriptions=subscriptions,
                individual_classes=pd.DataFrame(),
            )

        return CustomerProfile(
            customer=customer,
            dog_profile_by_id=dogs_profiles
        )

    @staticmethod
    @callback(
        Output(id_dogs_tabs, 'children'),
        Output(id_dogs_tabs, 'active_tab'),
        inputs=dict(
            active_tab=Input(id_dogs_tabs, 'active_tab'),
            dogs_tabs=Input(id_dogs_tabs, 'children'),
        ),
        prevent_initial_call=True
    )
    def on_active_tab_changed(active_tab: str, dogs_tabs: list[bootstrap.Tab]) -> tuple[list[bootstrap.Tab], str]:
        if not dogs_tabs:
            raise PreventUpdate
        if active_tab == 'None':
            # make sure there's always a dog selected
            assert len(dogs_tabs) > 0
            return dogs_tabs, Controller.__get_tab_id(dogs_tabs[0])

        if active_tab == Controller.tab_id_add_dog_tab:
            return Controller.__add_new_dog_tab(dogs_tabs)
        else:
            raise PreventUpdate

    @staticmethod
    @callback(
        Output(id_main_container, 'children'),
        inputs=dict(
            reset_button_clicks=Input(id_reset_button, 'n_clicks'),
            active_tab=Input(id_dogs_tabs, 'active_tab'),
            dogs_tabs=Input(id_dogs_tabs, 'children'),
        ),
        prevent_initial_call=True
    )
    def reset_data(reset_button_clicks: int, active_tab: str, dogs_tabs: list[bootstrap.Tab]):
        if not reset_button_clicks:
            raise PreventUpdate
        if active_tab == 'None':
            # make sure there's always a dog selected
            assert len(dogs_tabs) > 0
            dog_id = Controller.__get_tab_id(dogs_tabs[0])
        else:
            dog_id = active_tab
        assert dog_id is not None
        return make_layout(int(dog_id))

    @staticmethod
    @page_callback(
        action=Action.SHOW_USER_MESSAGE,
        inputs=dict(
            save_button_clicks=Input(id_save_button, 'n_clicks'),
            customer_data_json=State(FormIds.form_data_store(id_customer_data_form), 'data'),
            dogs_json=State(FormIds.form_data_store(id_dog_form, ALL), 'data'),
            persons_json=State(FormIds.form_data_store(id_person_form, ALL), 'data'),
        )
    )
    def save_customer(save_button_clicks: int, customer_data_json: str, dogs_json: str,
                      persons_json: str) -> CallbackData:
        if not save_button_clicks:
            raise PreventUpdate

        logger.info('Saving customer...')
        logger.debug(f'customer_data={customer_data_json} dogs={dogs_json} persons={persons_json}')

        data_provider = DataProvider()
        try:
            customer_data = FormData.from_json(customer_data_json)
            logger.info(f'Validating customer data: {customer_data.data}')
            customer_data.validate()
            if customer_data.is_insertion:
                customer_id = data_provider.insert_customer(customer_data.data)
            else:
                customer_id = customer_data.data['customer_id']
                data_provider.update_customer(customer_data.data)
            logger.info(f'Saved customer {customer_id}')

            for dog_json in dogs_json:
                dog = FormData.from_json(dog_json)
                logger.info(f'Validating dog: {dog.data}')
                dog.validate()
                if dog.is_insertion:
                    dog_id = data_provider.insert_dog(dog.data, customer_id=customer_id)
                else:
                    dog_id = dog.data['dog_id']
                    data_provider.update_dog(dog.data)
                logger.info(f'Saved dog {dog_id} from customer {customer_id}')

            for person_json in persons_json:
                person = FormData.from_json(person_json)
                logger.info(f'Validating person: {person.data}')
                person.validate()
                if person.is_insertion:
                    person_id = data_provider.insert_person(person.data, customer_id=customer_id)
                else:
                    person_id = person.data['person_id']
                    data_provider.update_person(person.data)
                logger.info(f'Saved person {person_id} from customer {customer_id}')

            data_provider.commit()
            return CallbackData(
                user_message=UserMessage(message='Customer saved successfully', header='Success', type='success'))
        except RuntimeError as e:
            data_provider.rollback()
            return CallbackData(
                user_message=UserMessage(message=f'Error saving customer: {e}', header='Error', type='danger'))

    @classmethod
    def __add_new_dog_tab(cls, dogs_tabs: list[bootstrap.Tab]) -> tuple[list[bootstrap.Tab], str]:
        new_dog_tab = Controller.make_dog_tab(
            dog=cls.__make_new_dog(),
            profile=DogProfile(
                subscriptions=pd.DataFrame(),
                individual_classes=pd.DataFrame(),
            ), is_insertion=True)
        dogs_tabs.insert(len(dogs_tabs) - 1, new_dog_tab)
        new_dog_id = new_dog_tab.tab_id
        return dogs_tabs, new_dog_id

    @staticmethod
    def __get_tab_id(tab: bootstrap.Tab):
        return tab['props']['tab_id']

    @classmethod
    def make_dog_tab(cls, dog: dict, profile: DogProfile, is_insertion: bool) -> bootstrap.Tab:
        # TODO update label when name is changed
        dog_id = dog['dog_id']
        dog_form = DictFormAIO(
            data=dog,
            fields_config=cls.dog_fields_config,
            is_insertion=is_insertion,
            form_id=cls.id_dog_form,
            form_index=dog_id)
        subscriptions_table = cls.make_subscriptions_table(dog_id, profile.subscriptions) \
            if profile.subscriptions is not None and not profile.subscriptions.empty \
            else html.Div('No trainings yet.', className='p-3')
        return bootstrap.Tab(
            [
                dog_form,
                subscriptions_table
            ],
            id=Ids.element('DogTab', dog_id),
            className='p-3 border border-top-0 border-secondary',
            label=dog['dog_name'],
            tab_id=str(dog_id))

    @classmethod
    def make_subscriptions_table(cls, dog_id: int, subscriptions: pd.DataFrame) -> DataTable:
        return DataTable(
            id=Ids.dog_subscriptions_table(dog_id=dog_id),
            data=subscriptions.to_dict('records'),
            columns=Controller.dog_subscriptions_columns,
            editable=False,
            row_deletable=False,
            row_selectable=False,
            filter_action='native',
            filter_options={'case': 'insensitive'},
            sort_action='native',
            style_table={'overflow': 'scroll'},
        )

    @classmethod
    def make_person_panel(cls, person: dict, is_insertion: bool) -> html.Div:
        return html.Div(
            DictFormAIO(
                data=person,
                fields_config=Controller.person_fields_config,
                is_insertion=is_insertion,
                form_id=Controller.id_person_form,
                form_index=person['person_id']),
            id=Ids.element('PersonContainer', person['person_id']),
            className='mt-2 p-3 border border-secondary')

    @staticmethod
    @callback(Output(__id_field_dog_name, 'invalid'), Output(__id_feedback_dog_name, 'children'),
              inputs=dict(dog_name=Input(__id_field_dog_name, 'value')))
    def validate_dog_name(dog_name: str) -> tuple[bool, str]:
        return Controller.__validate_required_field(dog_name)

    @staticmethod
    @callback(Output(__id_field_breed, 'invalid'), Output(__id_feedback_breed, 'children'),
              inputs=dict(dog_breed=Input(__id_field_breed, 'value')))
    def validate_dog_breed(dog_breed: str) -> tuple[bool, str]:
        return Controller.__validate_required_field(dog_breed)

    @staticmethod
    @callback(Output(__id_field_person_name, 'invalid'), Output(__id_feedback_person_name, 'children'),
              inputs=dict(person_name=Input(__id_field_person_name, 'value')))
    def validate_person_name(person_name: str) -> tuple[bool, str]:
        return Controller.__validate_required_field(person_name)

    @staticmethod
    @callback(Output(__id_field_email_address, 'invalid'), Output(__id_feedback_email_address, 'children'),
              inputs=dict(email_address=Input(__id_field_email_address, 'value')))
    def validate_email_address(email_address: str) -> tuple[bool, str]:
        return Controller.__validate_required_field(email_address,
                                                    'Field is required and must be a valid email address')

    @staticmethod
    def __validate_required_field(value: Optional[str], error_message: str = 'Field is required') -> tuple[bool, str]:
        if not value:
            return True, error_message
        return False, ''

    @classmethod
    def make_new_profile(cls) -> CustomerProfile:
        return CustomerProfile(
            customer=Customer(
                customer_data={},
                dogs=[cls.__make_new_dog()],
                persons=[cls.__make_new_person()]
            ),
            dog_profile_by_id={},
        )

    @classmethod
    def __make_new_dog(cls) -> dict:
        return {
            'dog_id': cls.__generate_new_dog_id(),
            'dog_name': cls.__default_dog_name,
        }

    @classmethod
    def __make_new_person(cls) -> dict:
        return {
            'person_id': cls.__generate_new_person_id(),
        }

    @classmethod
    def __generate_new_dog_id(cls) -> str:
        cls.__last_new_dog_id += 1
        return f'N{cls.__last_new_dog_id}'

    @classmethod
    def __generate_new_person_id(cls) -> str:
        cls.__last_new_person_id += 1
        return f'N-{cls.__last_new_person_id}'


def make_layout(dog_id: int) -> list:
    customer_profile, is_insertion = (Controller.make_new_profile(), True) \
        if dog_id is None \
        else (Controller.get_profile_by_dog_id(dog_id=dog_id), False)

    customer = customer_profile.customer

    add_dog_tab = bootstrap.Tab(
        'Au Au! New dog in the oven...',
        id=Ids.element('Tab', Controller.tab_id_add_dog_tab),
        className='p-3 border border-top-0 border-secondary',
        tab_class_name=Controller.tab_id_add_dog_tab,
        label='+',
        tab_id=Controller.tab_id_add_dog_tab)

    dog_tabs = [Controller.make_dog_tab(dog=dog, profile=customer_profile.get_dog_profile(dog_id=dog_id),
                                        is_insertion=is_insertion) for dog in customer.dogs] + \
               [add_dog_tab]

    row_dogs_tabs = bootstrap.Row(
        bootstrap.Col(
            bootstrap.Tabs(
                dog_tabs,
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
                    is_insertion=is_insertion,
                    form_id=Controller.id_customer_data_form),
                className='mt-2 p-3 border border-secondary'
            )
        )
    )
    rows_persons = [
        bootstrap.Row(
            bootstrap.Col(
                Controller.make_person_panel(person, is_insertion=is_insertion)
            )
        )
        for person in customer.persons
    ]
    row_buttons = bootstrap.Row(
        bootstrap.Col(
            html.Div([
                bootstrap.Button(
                    'Reset',
                    id=Controller.id_reset_button,
                    className='btn-reset'),
                bootstrap.Button(
                    'Save',
                    id=Controller.id_save_button,
                    className='btn-success')],
                className='d-flex flex-row-reverse mt-2 gap-3'
            )
        )
    )
    children = [row_dogs_tabs] + rows_persons + [row_customer_data, row_buttons]
    return children


def layout(dog_id=None) -> html.Div:
    return html.Div(
        bootstrap.Container(
            make_layout(dog_id),
            id=Controller.id_main_container,
            class_name='my-2',
        )
    )
