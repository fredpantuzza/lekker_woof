import logging
from typing import Any, Optional

import dash_bootstrap_components as bootstrap
import pandas as pd
from dash import callback, Input, Output, html, State
from dash.exceptions import PreventUpdate

from components.dict_form import DictFormAIO, DataStore as FormData, FieldType, Ids as FormIds
from components.page_callback import page_callback, Action, CallbackData
from controls.data_provider import DataProvider
from controls.types import UserMessage

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Ids:
    @classmethod
    def element(cls, component_type: Any, index: Any = '') -> dict:
        return {
            'page': 'training_profile',
            'component': component_type,
            'index': index
        }


class Controller:
    training_data_fields_config = {
        'training_id': {'label': 'ID', 'type': FieldType.STORE},
        'name': {'label': 'Name', 'type': FieldType.TEXT, 'required': True},
        'price': {'label': 'Price', 'type': FieldType.NUMBER, 'input_label_left': '€', 'required': True},
        'classes_online': {'label': 'Online classes', 'type': FieldType.NUMBER},
        'classes_in_person': {'label': 'In-person classes', 'type': FieldType.NUMBER},
        'created_timestamp': {'label': 'Registration date', 'type': FieldType.STORE}
    }

    id_main_container = Ids.element('Container')
    id_reset_button = Ids.element('Button', 'reset-training')
    id_save_button = Ids.element('Button', 'save-training')
    id_training_data_form = 'TrainingDataForm'

    @staticmethod
    def get_training_by_id(training_id: int) -> pd.DataFrame:
        data_provider = DataProvider()
        return data_provider.get_training_by_id(training_id=training_id)

    @staticmethod
    @callback(
        Output(id_main_container, 'children'),
        inputs=dict(
            reset_button_clicks=Input(id_reset_button, 'n_clicks'),
            training_data_json=State(FormIds.form_data_store(id_training_data_form), 'data'),
        ),
        prevent_initial_call=True
    )
    def reset_data(reset_button_clicks: int, training_data_json: str):
        if not reset_button_clicks:
            raise PreventUpdate
        training_data = FormData.from_json(training_data_json)
        training_id = training_data.get_field_value('training_id')
        assert training_id is not None
        return make_layout(training_id)

    @staticmethod
    @page_callback(
        action=Action.SHOW_USER_MESSAGE,
        inputs=dict(
            save_button_clicks=Input(id_save_button, 'n_clicks'),
            training_data_json=State(FormIds.form_data_store(id_training_data_form), 'data'),
        )
    )
    def save_training(save_button_clicks: int, training_data_json: str) -> CallbackData:
        if not save_button_clicks:
            raise PreventUpdate

        logger.info('Saving training...')
        logger.debug(f'training_data={training_data_json}')

        data_provider = DataProvider()
        try:
            training_data = FormData.from_json(training_data_json)
            logger.info(f'Validating training data: {training_data.data}')
            training_data.validate()
            if training_data.is_insertion:
                training_id = data_provider.insert_training(training_data.data)
            else:
                training_id = training_data.data['training_id']
                data_provider.update_training(training_data.data)
            logger.info(f'Saved training {training_id}')

            data_provider.commit()
            return CallbackData(
                user_message=UserMessage(message='Training saved successfully', header='Success', type='success'))
        except RuntimeError as e:
            data_provider.rollback()
            return CallbackData(
                user_message=UserMessage(message=f'Error saving training: {e}', header='Error', type='danger'))


def make_layout(training_id: Optional[int]) -> list:
    training_df, is_insertion = (pd.DataFrame(), True) \
        if training_id is None \
        else (Controller.get_training_by_id(training_id=training_id), False)

    trainings = training_df.to_dict('records')
    if len(trainings) != 1:
        raise ValueError(f'Expected 1 and only 1 training, but found {len(trainings)} for id {training_id}')
    training = trainings[0]

    row_training_data = bootstrap.Row(
        bootstrap.Col(
            html.Div(
                DictFormAIO(
                    data=training,
                    fields_config=Controller.training_data_fields_config,
                    is_insertion=is_insertion,
                    form_id=Controller.id_training_data_form),
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
    children = [row_training_data, row_buttons]
    return children


def layout(training_id: Optional[int]) -> html.Div:
    return html.Div(
        bootstrap.Container(
            make_layout(training_id),
            id=Controller.id_main_container,
            class_name='my-2',
        )
    )
