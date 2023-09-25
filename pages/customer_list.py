from typing import Any

import pandas as pd
from dash import dash_table, html, Input, State
from dash.exceptions import PreventUpdate

from components.page_callback import page_callback, Action, CallbackData
from controls.data_provider import DataProvider


class Ids:
    @classmethod
    def element(cls, component_type: Any, index: Any = '') -> dict:
        return {
            'page': 'customer_list',
            'component': component_type,
            'index': index
        }


class Controller:
    customers_columns = [
        {'id': 'dog_id', 'name': 'ID'},
        {'id': 'dog_name', 'name': 'Dog name'},
        {'id': 'owners', 'name': 'Owners\' names'},
        {'id': 'balance_in_eur', 'name': 'Account balance', 'type': 'numeric'},
        {'id': 'breed', 'name': 'Breed'},
        {'id': 'sex', 'name': 'Sex'},  # computed in code from is_male
        {'id': 'birth_date', 'name': 'Birth date', 'type': 'datetime'},
        {'id': 'address', 'name': 'Address'},
        {'id': 'phones1', 'name': 'Phones'},
        {'id': 'phones2', 'name': 'Phones'},
        {'id': 'email_addresses', 'name': 'E-mails'},
    ]

    id_customers_data_table = Ids.element('DataTable', 'customers')

    page_size = 10

    @staticmethod
    def load_customers() -> list[dict]:
        data_provider = DataProvider()
        customers_df = data_provider.get_all_customers()
        customers_df['id'] = customers_df['dog_id']
        customers_df['sex'] = customers_df['is_male'].map({1: 'Male', 0: 'Female'})
        return customers_df.to_dict('records')

    @staticmethod
    @page_callback(
        action=Action.OPEN_CUSTOMER,
        inputs=dict(
            active_cell=Input(id_customers_data_table, 'active_cell'),
            table_data=State(id_customers_data_table, 'data'),
        )
    )
    def on_cell_clicked(active_cell: dict, table_data: dict) -> CallbackData:
        if not active_cell:
            raise PreventUpdate
        # FIXME doesn't work with filters
        row = active_cell['row_id'] - 1
        customers_df = pd.DataFrame.from_records(table_data)
        dog_id = customers_df.at[row, 'dog_id']
        return CallbackData(dog_id=dog_id)


def layout() -> html.Div:
    customers = Controller.load_customers()

    return html.Div([
        dash_table.DataTable(
            id=Controller.id_customers_data_table,
            data=customers,
            columns=Controller.customers_columns,
            editable=False,
            row_deletable=False,
            row_selectable=False,
            filter_action='native',
            filter_options={'case': 'insensitive'},
            sort_action='native',
            sort_mode="multi",
            page_action="native",
            page_current=0,
            page_size=Controller.page_size,
            css=[{"selector": ".row", "rule": "margin: 0; display: block"}],
            style_table={'overflowY': 'scroll'},
            style_data_conditional=[
                {
                    'if': {
                        'column_id': 'balance_in_eur',
                        'filter_query': '{balance_in_eur} < 0.0'
                    },
                    'backgroundColor': 'var(--bs-warning)'
                }
            ]
        )
    ])
