import json
import logging
import uuid
from enum import Enum
from typing import Any, Optional

import dash_bootstrap_components as bootstrap
from bidict import bidict
from dash import ctx, dcc, callback, Input, State, Output, MATCH, html, ALL
from dash.development.base_component import Component
from dash.exceptions import PreventUpdate
from dash_bootstrap_components import InputGroupText

from controls.utils import flatten, BidictEncoder, BidictDecoder

logger = logging.getLogger(__name__)


class FieldType(str, Enum):
    STORE = 'STORE'  # Hidden
    TEXT = 'TEXT'
    EMAIL = 'EMAIL'
    NUMBER = 'NUMBER'
    TEXTAREA = 'TEXTAREA'
    DATE = 'DATE'
    RADIO = 'RADIO'


class Ids:
    @staticmethod
    def form_data_store(form_id: Any, form_index: Any = '') -> dict:
        return Ids.field_element(
            field_type=FieldType.STORE,
            field_name='form_data',
            form_id=form_id, form_index=form_index)

    @staticmethod
    def field_feedback(field_name: Any, form_id: Any, form_index: Any = '') -> dict:
        return Ids.field_element(
            field_type='field_feedback',
            field_name=field_name,
            form_id=form_id, form_index=form_index)

    @staticmethod
    def field_element(field_type: Any, field_name: Any, form_id: Any, form_index: Any = '') -> dict:
        """
        :param field_type: param of type @FieldType or str
        :param field_name: name of the field
        :param form_id: id of the form
        :param form_index: additional index to the form_id, if needed.
        :return: dict id
        """
        return dict(
            component='DictFormAIO',
            field_type=field_type,
            field_name=field_name,
            form_id=form_id,
            form_index=form_index,
        )


class DataStore:
    def __init__(self, data: dict, fields_config: dict[str, dict[str, Any]], is_insertion: bool,
                 is_modified: bool = False, validation_state_by_field: dict[str, bool] = {}) -> None:
        self.data = data
        self.fields_config = fields_config
        self.is_insertion = is_insertion
        self.is_modified = is_modified
        self.validation_state_by_field = validation_state_by_field

    @classmethod
    def from_json(cls, json_str: str):
        data_store_dict = json.loads(json_str, cls=BidictDecoder)
        return cls(**data_store_dict)

    def to_json(self) -> str:
        return json.dumps(vars(self), cls=BidictEncoder)

    def validate(self) -> None:
        for field_name in self.fields_config.keys():
            if not self.is_field_valid(field_name):
                raise RuntimeError(f'Some fields contain errors')

    def get_field_value(self, field_name: str) -> Any:
        return self.data[field_name] if field_name in self.data else None

    def is_field_valid(self, field_name: str) -> bool:
        # External validation
        if field_name in self.validation_state_by_field and self.validation_state_by_field[field_name] is False:
            return False
        is_required = self.get_field_config(field_name, 'required', default_value=False)
        field_value = self.get_field_value(field_name)
        if is_required and not field_value:
            return False
        return True

    def get_field_config(self, field_name: str, config: str, default_value: Any) -> Any:
        return self.fields_config[field_name][config] \
            if field_name in self.fields_config and config in self.fields_config[field_name] \
            else default_value

    def is_field_readonly(self, field_name: str) -> bool:
        return self.get_field_config(field_name, 'readonly', default_value=False)

    def get_field_type(self, field_name: str) -> FieldType:
        return FieldType(self.get_field_config(field_name, 'type', default_value=FieldType.TEXT))

    def get_field_label(self, field_name: str) -> str:
        return self.get_field_config(field_name, 'label', default_value=field_name)

    def get_field_input_label_left(self, field_name: str) -> str:
        return self.get_field_config(field_name, 'input_label_left', default_value=None)

    def get_field_display_value_converter(self, field_name: str) -> Optional[bidict]:
        return self.get_field_config(field_name, 'display_value_converter_bidict', default_value=None)

    def get_field_options(self, field_name: str, default: list = []) -> Optional[list]:
        return self.get_field_config(field_name, 'options', default_value=default)


class DictFormAIO(html.Div):
    """
    All-in-one component capable of creating a (boostrap) form for editing a dictionary, where key is the field name.
    The types allowed for the value of the dictionary depend on the field type. The field type and other properties of
    each field must be provided when creating this component. See more on :method:`~dict_form.DictFormAIO.__init__`.

    This component maintains a data store (accessible with :method:`~dict_form.Ids.form_data_store`). See DataStore for
    more details.
    """

    __storage_by_field_type = {
        FieldType.STORE: 'data',
        FieldType.TEXT: 'value',
        FieldType.NUMBER: 'value',
        FieldType.EMAIL: 'value',
        FieldType.TEXTAREA: 'value',
        FieldType.DATE: 'date',
        FieldType.RADIO: 'value',
    }

    # constants
    __default_value_type = FieldType.TEXT

    __all_fields_input_filter = tuple(
        Input(Ids.field_element(field_type=field_type, field_name=ALL, form_id=MATCH, form_index=MATCH), storage)
        for field_type, storage in __storage_by_field_type.items()
        if field_type != FieldType.STORE)

    __all_fields_invalid_filter = tuple(
        Input(Ids.field_element(field_type=field_type, field_name=ALL, form_id=MATCH, form_index=MATCH), 'invalid')
        for field_type, storage in __storage_by_field_type.items()
        if field_type not in [FieldType.STORE, FieldType.DATE, FieldType.RADIO])

    def __init__(self, data: dict, fields_config: dict[str, dict[str, Any]] = {},
                 is_insertion: bool = False, form_id: Optional[str] = None, form_index: Optional[Any] = '',
                 *args, **kwargs):
        """
        :param data: Dict with each key being a field_name in the form.
        :param fields_config: Dict where key is field_name name, and inner dict accepts following values:
          * readonly: behaves as expected. Default=false
          * type: type of the input field_name. Default=text. Values allowed=see @FieldType
          * label: label of the field_name. Default=field_name
          * display_value_converter_bidict: bidict where the primary key is the DB value and the inverse key is the
            display value.
          * options: options for multi-choice fields, like radio. Ignored for all the rest.
        :param is_insertion: Indicate if this form represents a new entity.
        :param form_id: id of the component. If None, it'll be auto-generated.
        :param form_index: optional additional index to the form_id, if needed.
        :return: Div element with the form inside.
        """
        self.form_id = form_id if form_id is not None else str(uuid.uuid4())
        self.form_index = form_index
        self.__data_store = DataStore(data=data, fields_config=fields_config, is_insertion=is_insertion)
        self.__initialize_data_from_fields_config()

        super().__init__(*args, **kwargs, className='dict-form', children=self.__make_form())

    def __initialize_data_from_fields_config(self) -> None:
        """
        Guarantees all field names in field_config are present in DataStore.data.
        """
        for field_name in self.__data_store.fields_config.keys():
            if field_name in self.__data_store.data:
                continue
            self.__data_store.data[field_name] = None

    @staticmethod
    @callback(Output(Ids.form_data_store(form_id=MATCH, form_index=MATCH), 'data'),
              inputs=dict(
                  input_fields=__all_fields_input_filter,
                  input_fields_invalid_state=__all_fields_invalid_filter,
                  form_data_store_json=State(Ids.form_data_store(form_id=MATCH, form_index=MATCH), 'data')),
              prevent_initial_callback=True)
    def __recompute_data_store(input_fields: tuple, input_fields_invalid_state: tuple,
                               form_data_store_json: str) -> str:
        form_data_store = DataStore.from_json(form_data_store_json)

        modified_fields = DictFormAIO.__get_triggered_fields('input_fields')
        if modified_fields:
            return DictFormAIO.__on_field_modified(modified_fields, form_data_store).to_json()

        validated_fields = DictFormAIO.__get_triggered_fields('input_fields_invalid_state')
        if validated_fields:
            return DictFormAIO.__on_field_validated(validated_fields, form_data_store).to_json()

        raise PreventUpdate

    @staticmethod
    def __on_field_modified(fields: list[dict], form_data_store: DataStore) -> DataStore:
        form_data_store.is_modified = True

        # Update data store with new value(s)
        for field in fields:
            field_name = field['id']['field_name']
            field_value = field['value']
            display_value_converter = form_data_store.get_field_display_value_converter(field_name)
            if display_value_converter is not None:
                assert isinstance(display_value_converter, bidict)
                field_value = display_value_converter.inverse[field_value]
            form_data_store.data[field_name] = field_value

        return form_data_store

    @staticmethod
    def __on_field_validated(fields: list[dict], form_data_store: DataStore) -> DataStore:
        for field in fields:
            field_name = field['id']['field_name']
            assert field['property'] == 'invalid'
            field_is_invalid = field['value']
            field_is_valid = True if field_is_invalid is None else not field_is_invalid
            form_data_store.validation_state_by_field[field_name] = field_is_valid
        return form_data_store

    @staticmethod
    def __get_triggered_fields(args_grouping: str) -> list[dict]:
        ctx_input_fields_raw: list[list[dict]] = ctx.args_grouping[args_grouping]
        ctx_input_fields = flatten(ctx_input_fields_raw)
        return [input_field for input_field in ctx_input_fields if input_field['triggered']]

    def __make_form(self) -> bootstrap.Form:
        form_fields = []
        for field_name, _ in self.__data_store.fields_config.items():
            field_value = self.__data_store.data[field_name] if field_name in self.__data_store.data else None
            field_components = self.__make_field_components(field_name=field_name, field_value=field_value)
            form_fields.append(field_components)
        return bootstrap.Form([
            dcc.Store(id=Ids.form_data_store(self.form_id, self.form_index), data=self.__data_store.to_json()),
            html.Div(
                form_fields,
                className='d-inline-flex flex-row justify-content-between flex-wrap w-100'
            )
        ])

    def __make_field_components(self, field_name: str, field_value: Any) -> Component:
        is_hidden = self.__data_store.get_field_type(field_name) == FieldType.STORE

        field_data_component = self.__make_field_data_component(field_name, field_value)
        if is_hidden:
            return field_data_component

        input_group_components = [
            field_data_component,
            bootstrap.FormFeedback('', type='invalid',
                                   id=Ids.field_feedback(field_name, self.form_id, self.form_index)),
        ]

        input_label_left = self.__data_store.get_field_input_label_left(field_name)
        if input_label_left:
            input_group_components.insert(0, InputGroupText(input_label_left))

        return html.Div(
            [
                bootstrap.Label(self.__data_store.get_field_label(field_name)),
                bootstrap.InputGroup(input_group_components),
            ],
            className=f'mb-3 me-3 dict-form-field {field_name}'
        )

    def __make_field_data_component(self, field_name: str, field_value: Any) -> Component:
        field_type = self.__data_store.get_field_type(field_name)
        field_id = Ids.field_element(field_type, field_name, self.form_id, self.form_index)
        is_readonly = self.__data_store.is_field_readonly(field_name)
        field_value_options = self.__data_store.get_field_options(field_name, default=[field_value])
        display_value_converter_bidict = self.__data_store.get_field_display_value_converter(field_name)
        display_value = display_value_converter_bidict[field_value] \
            if display_value_converter_bidict is not None and field_value is not None \
            else field_value
        field_label = self.__data_store.get_field_label(field_name)
        placeholder = f'Enter {field_label.lower()} here...' if not is_readonly else '<NULL>'
        if field_type == FieldType.STORE:
            return dcc.Store(
                id=field_id, data=display_value)
        elif field_type == FieldType.DATE:
            return dcc.DatePickerSingle(
                id=field_id, date=display_value, disabled=is_readonly, placeholder=placeholder,
                className='form-date-picker')
        elif field_type == FieldType.TEXTAREA:
            return bootstrap.Textarea(
                id=field_id, value=DictFormAIO.__value_as_str(display_value), readonly=is_readonly, debounce=True,
                placeholder=placeholder)
        elif field_type == FieldType.RADIO:
            return bootstrap.RadioItems(
                id=field_id, value=display_value, options=field_value_options, inline=True)
        elif field_type == FieldType.TEXT:
            return bootstrap.Input(
                id=field_id, type='text', value=DictFormAIO.__value_as_str(display_value), readonly=is_readonly,
                debounce=True, placeholder=placeholder)
        elif field_type == FieldType.NUMBER:
            return bootstrap.Input(
                id=field_id, type='number', value=display_value, readonly=is_readonly, placeholder=placeholder)
        elif field_type == FieldType.EMAIL:
            return bootstrap.Input(
                id=field_id, type='email', value=DictFormAIO.__value_as_str(display_value), readonly=is_readonly,
                debounce=True, placeholder=placeholder)
        raise Exception(f'Invalid field type {field_type}')

    @staticmethod
    def __value_as_str(value: Any) -> str:
        return '' if value is None else str(value)
