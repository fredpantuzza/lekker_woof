from dash import dash_table, html
from controls.data_provider import DataProvider


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

    id_customers_data_table = 'CustomersDataTable'

    page_size = 10

    @staticmethod
    def load_customers() -> list[dict]:
        data_provider = DataProvider()
        customers_df = data_provider.get_all_customers()
        customers_df['id'] = customers_df['dog_id']
        customers_df['sex'] = customers_df['is_male'].map({1: 'Male', 0: 'Female'})
        return customers_df.to_dict('records')


def layout() -> html.Div:
    customers = Controller.load_customers()

    return html.Div(
        dash_table.DataTable(
            id=Controller.id_customers_data_table,
            data=customers,
            columns=Controller.customers_columns,
            editable=False,
            row_deletable=False,
            row_selectable='single',
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
    )
