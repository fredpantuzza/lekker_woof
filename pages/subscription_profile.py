import logging
from datetime import datetime
from typing import Any, Optional

import dash_bootstrap_components as bootstrap
import pandas as pd
from dash import callback, html, Input, Output, State
from dash.exceptions import PreventUpdate

from components.dict_form import DataStore as FormData, DictFormAIO, FieldType, Ids as FormIds
from components.page_callback import Action, CallbackData, page_callback
from controls import consts, utils
from controls.data_provider import DataProvider
from controls.types import UserMessage

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Ids:
    @classmethod
    def element(cls, component_type: Any, index: Any = '') -> dict:
        return {
            'page': 'subscription_profile',
            'component': component_type,
            'index': index
        }


class Controller:
    subscription_data_fields_config = {
        'subscription_id': {'label': 'ID', 'type': FieldType.STORE},
        'dog_name': {'label': 'Dog', 'type': FieldType.TEXT, 'readonly': True},
        'training_id': {'label': 'Training', 'type': FieldType.SELECT, 'required': True},
        'actual_price': {'label': 'Current price', 'type': FieldType.NUMBER, 'input_label_left': '€', 'readonly': True},
        'new_price': {'label': 'New price', 'type': FieldType.NUMBER, 'input_label_left': '€', 'required': True},
        'notes': {'label': 'Notes', 'type': FieldType.TEXTAREA},
    }

    id_main_container = Ids.element('Container')
    id_reset_button = Ids.element('Button', 'reset-subscription')
    id_save_button = Ids.element('Button', 'save-subscription')
    id_subscription_data_form = 'SubscriptionDataForm'

    def __init__(self):
        self.__data_provider = DataProvider()

    def get_subscription_by_id(self, subscription_id: int) -> pd.DataFrame:
        return self.__data_provider.get_subscription_by_id(subscription_id=subscription_id)

    def get_classes_by_subscription_id(self, subscription_id: int) -> pd.DataFrame:
        return self.__data_provider.get_classes_by_subscription_id(subscription_id=subscription_id)

    def get_training_options(self) -> list[dict]:
        trainings_df = self.__data_provider.get_all_trainings()
        trainings: pd.Series = trainings_df.apply(lambda row: {
            'label': f'{row["name"]} (€ {row["price"]:.2f})',
            'value': row["training_id"],
        }, axis=1)
        return trainings.to_list()

    @staticmethod
    @callback(
        Output(id_main_container, 'children'),
        inputs=dict(
            reset_button_clicks=Input(id_reset_button, 'n_clicks'),
            subscription_data_json=State(FormIds.form_data_store(id_subscription_data_form), 'data'),
        ),
        prevent_initial_call=True
    )
    def reset_data(reset_button_clicks: int, subscription_data_json: str):
        if not reset_button_clicks:
            raise PreventUpdate
        subscription_data = FormData.from_json(subscription_data_json)
        subscription_id = subscription_data.get_field_value('subscription_id')
        assert subscription_id is not None
        return make_layout(subscription_id)

    @staticmethod
    @page_callback(
        action=Action.SHOW_USER_MESSAGE,
        inputs=dict(
            save_button_clicks=Input(id_save_button, 'n_clicks'),
            subscription_data_json=State(FormIds.form_data_store(id_subscription_data_form), 'data'),
        )
    )
    def save_subscription(save_button_clicks: int, subscription_data_json: str) -> CallbackData:
        if not save_button_clicks:
            raise PreventUpdate

        logger.info('Saving subscription...')
        logger.debug(f'subscription_data={subscription_data_json}')

        # TODO current price (readonly) vs new price, update customer balance
        data_provider = DataProvider()
        try:
            subscription_data = FormData.from_json(subscription_data_json)
            logger.info(f'Validating subscription data: {subscription_data.data}')
            subscription_data.validate()
            if subscription_data.is_insertion:
                subscription_id = data_provider.insert_subscription(subscription_data.data)
            else:
                subscription_id = subscription_data.data['subscription_id']
                data_provider.update_subscription(subscription_data.data)
            logger.info(f'Saved subscription {subscription_id}')

            data_provider.commit()
            return CallbackData(
                user_message=UserMessage(message='Subscription saved successfully', header='Success', type='success'))
        except RuntimeError as e:
            data_provider.rollback()
            return CallbackData(
                user_message=UserMessage(message=f'Error saving subscription: {e}', header='Error', type='danger'))


def make_layout(subscription_id: Optional[int]) -> list:
    control = Controller()
    subscription_df, is_insertion = (pd.DataFrame(), True) \
        if subscription_id is None \
        else (control.get_subscription_by_id(subscription_id=subscription_id), False)

    subscription = utils.get_single_row_as_dict(subscription_df)
    subscription['new_price'] = subscription['actual_price']

    training_options = control.get_training_options()
    form_data_fields = control.subscription_data_fields_config.copy()
    form_data_fields['training_id']['options'] = training_options
    # TODO onChange, automatically set new price (client-side pls)

    classes_df = control.get_classes_by_subscription_id(subscription_id=subscription_id)
    classes = classes_df.to_dict('records')

    row_subscription_data = bootstrap.Row(
        bootstrap.Col(
            html.Div(
                DictFormAIO(
                    data=subscription,
                    fields_config=form_data_fields,
                    is_insertion=is_insertion,
                    form_id=Controller.id_subscription_data_form),
                className='mt-2 p-3 border border-secondary'
            )
        )
    )
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

    classes_accordion_items = []
    for dog_class in classes:
        class_date_dt = datetime.strptime(dog_class['class_date'], '%Y-%m-%d')
        class_date_str = class_date_dt.strftime(consts.date_format)
        kind = 'Online' if bool(dog_class['is_online']) else 'In person'
        # TODO update notes and delete class
        accordion_item = bootstrap.AccordionItem(
            bootstrap.Textarea(
                dog_class['notes'],
                className='dog-class-notes',
            ),
            title=f'{kind} on {class_date_str}',
            className='dog-class'
        )
        classes_accordion_items.append(accordion_item)
    row_classes = bootstrap.Row(
        bootstrap.Col(
            [
                html.H5('Classes', className='mt-4'),
                bootstrap.Accordion(
                    classes_accordion_items,
                    start_collapsed=True,
                    className='dog-classes'),
            ],
        )
    )

    children = [row_subscription_data, row_buttons, row_classes]
    return children


def layout(subscription_id: Optional[int]) -> html.Div:
    return html.Div(
        bootstrap.Container(
            make_layout(subscription_id),
            id=Controller.id_main_container,
            class_name='my-2 page-subscription-profile',
        )
    )
