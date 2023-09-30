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
            'page': 'training_list',
            'component': component_type,
            'index': index
        }


class Controller:
    trainings_columns = [
        {'id': 'training_id', 'name': 'ID'},
        {'id': 'name', 'name': 'Name'},
        {'id': 'price', 'name': 'Price', 'type': 'numeric'},
        {'id': 'classes_online', 'name': 'Online', 'type': 'numeric'},
        {'id': 'classes_in_person', 'name': 'In person', 'type': 'numeric'},
    ]

    id_trainings_data_table = Ids.element('DataTable', 'trainings')

    page_size = 10

    @staticmethod
    def load_trainings() -> list[dict]:
        data_provider = DataProvider()
        trainings_df = data_provider.get_all_trainings()
        return trainings_df.to_dict('records')

    @staticmethod
    @page_callback(
        action=Action.OPEN_TRAINING,
        inputs=dict(
            active_cell=Input(id_trainings_data_table, 'active_cell'),
            table_data=State(id_trainings_data_table, 'data'),
        )
    )
    def on_cell_clicked(active_cell: dict, table_data: dict) -> CallbackData:
        if not active_cell:
            raise PreventUpdate
        # FIXME doesn't work with filters
        row = active_cell['row']
        trainings_df = pd.DataFrame.from_records(table_data)
        training_id = trainings_df.at[row, 'training_id']
        return CallbackData(entity_id=training_id)


def layout() -> html.Div:
    trainings = Controller.load_trainings()

    return html.Div([
        dash_table.DataTable(
            id=Controller.id_trainings_data_table,
            data=trainings,
            columns=Controller.trainings_columns,
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
        )
    ])
