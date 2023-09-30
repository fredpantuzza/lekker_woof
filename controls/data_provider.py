import logging
import sqlite3

import pandas as pd

from controls import queries
from controls.types import Customer

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class DataProvider:
    def __init__(self):
        logger.info('Connecting to database...')
        # TODO configurable file location
        self.__connection = sqlite3.connect('sql/lekker_woof.db')
        logger.info('Connected')

    def commit(self) -> None:
        logger.info('Committing...')
        self.__connection.commit()
        logger.info('Committed')

    def rollback(self) -> None:
        logger.info('Rolling back...')
        self.__connection.rollback()
        logger.info('Rolled back')

    def get_all_customers(self) -> pd.DataFrame:
        logger.debug('get_all_customers')
        return pd.read_sql(queries.sql_get_all_customers, self.__connection)

    def get_customer_by_dog_id(self, dog_id: int) -> Customer:
        logger.debug(f'get_customer_by_dog_id {dog_id}')
        customer_df = pd.read_sql(queries.sql_customer_by_dog_id, self.__connection,
                                  params={'dog_id': dog_id})

        customer_data_df = customer_df.loc[:, ['customer_id', 'address', 'balance_in_eur', 'customer_notes',
                                               'customer_created_timestamp']]
        customer_data_df = customer_data_df.drop_duplicates(subset=['customer_id'], keep='first')
        customer_data = customer_data_df.to_dict('records')
        if len(customer_data) != 1:
            raise ValueError(f'Expected 1 and only 1 entry for customer_data, but found {len(customer_data)} '
                             f'for dog {dog_id}')
        customer_data = customer_data[0]

        dogs_df = customer_df.loc[:, ['dog_id', 'dog_name', 'birth_date', 'breed', 'is_male', 'dog_notes',
                                      'dog_created_timestamp']]
        dogs_df = dogs_df.drop_duplicates(subset=['dog_id'], keep='first')
        dogs = dogs_df.to_dict('records')

        persons_df = customer_df.loc[:, ['person_id', 'person_name', 'phone1', 'phone2', 'email_address',
                                         'person_created_timestamp']]
        persons_df = persons_df.drop_duplicates(subset=['person_id'], keep='first')
        persons = persons_df.to_dict('records')

        return Customer(customer_data, dogs, persons)

    def insert_customer(self, customer_data: dict) -> int:
        logger.info(f'Inserting customer: ${customer_data}')
        cur = self.__connection.execute(queries.sql_insert_customer, customer_data)
        customer_id = cur.lastrowid
        logger.info(f'Customer inserted with id ${customer_id}')
        return customer_id

    def update_customer(self, customer_data: dict) -> None:
        logger.info(f'Updating customer: ${customer_data}')
        self.__connection.execute(queries.sql_update_customer, customer_data)
        logger.info(f'Customer updated')

    def insert_dog(self, dog: dict, customer_id: int) -> int:
        logger.info(f'Inserting dog of customer {customer_id}: ${dog}')
        params = dog.copy()
        params['customer_id'] = customer_id
        cur = self.__connection.execute(queries.sql_insert_dog, params)
        dog_id = cur.lastrowid
        logger.info(f'Dog inserted with id ${dog_id}')
        return dog_id

    def update_dog(self, dog: dict) -> None:
        logger.info(f'Updating dog: ${dog}')
        self.__connection.execute(queries.sql_update_dog, dog)
        logger.info(f'Dog updated')

    def insert_person(self, person: dict, customer_id: int) -> int:
        logger.info(f'Inserting person of customer {customer_id}: ${person}')
        params = person.copy()
        params['customer_id'] = customer_id
        cur = self.__connection.execute(queries.sql_insert_person, params)
        person_id = cur.lastrowid
        logger.info(f'Person inserted with id ${person_id}')
        return person_id

    def update_person(self, person: dict) -> None:
        logger.info(f'Updating person: ${person}')
        self.__connection.execute(queries.sql_update_person, person)
        logger.info(f'Person updated')

    def get_all_trainings(self) -> pd.DataFrame:
        logger.debug('get_all_trainings')
        return pd.read_sql(queries.sql_get_all_trainings, self.__connection)

    def get_training_by_id(self, training_id: int) -> dict:
        logger.debug(f'get_training_by_id {training_id}')
        training_df = pd.read_sql(queries.sql_training_by_id, self.__connection, params={'training_id': training_id})
        trainings = training_df.to_dict('records')
        if len(trainings) != 1:
            raise ValueError(f'Expected 1 and only 1 training, but found {len(trainings)} for id {training_id}')
        return trainings[0]

    def insert_training(self, training_data: dict) -> int:
        logger.info(f'Inserting training: ${training_data}')
        cur = self.__connection.execute(queries.sql_insert_training, training_data)
        training_id = cur.lastrowid
        logger.info(f'Training inserted with id ${training_id}')
        return training_id

    def update_training(self, training_data: dict) -> None:
        logger.info(f'Updating training: ${training_data}')
        self.__connection.execute(queries.sql_update_training, training_data)
        logger.info(f'Training updated')
