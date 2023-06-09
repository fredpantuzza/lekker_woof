import logging
import sqlite3

import pandas

from controls.types import Customer

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class DataProvider:
    __sql_get_all_customers = '''
    SELECT
        d.dog_id,
        d.name dog_name,
        d.birth_date,
        d.breed,
        d.is_male,
        c.balance_in_eur,
        c.address,
        group_concat(p.name, ', ') owners,
        group_concat(DISTINCT p.phone1) phones1,
        group_concat(DISTINCT p.phone2) phones2,
        group_concat(DISTINCT p.email_address) email_addresses
    FROM dog d
    INNER JOIN customer c USING(customer_id)
    iNNER JOIN person p USING(customer_id)
    GROUP BY d.dog_id, c.customer_id 
    '''

    __sql_customer_by_dog_id = '''
    SELECT
        c.customer_id,
        c.address,
        c.balance_in_eur,
        c.notes AS customer_notes,
        c.created_timestamp AS customer_created_timestamp,
        d.dog_id,
        d.name dog_name,
        d.birth_date,
        d.breed,
        d.is_male,
        d.notes AS dog_notes,
        d.created_timestamp AS dog_created_timestamp,
        p.person_id,
        p.name person_name,
        p.phone1,
        p.phone2,
        p.email_address,
        p.created_timestamp AS person_created_timestamp
    FROM customer c
    INNER JOIN dog d USING(customer_id)
    iNNER JOIN person p USING(customer_id)
    WHERE c.customer_id = (SELECT customer_id FROM dog WHERE dog_id = :dog_id)
    '''

    __sql_insert_customer = '''
    INSERT INTO customer(address, balance_in_eur, notes)
    VALUES(:address, :balance_in_eur, :customer_notes)
    '''

    __sql_update_customer = '''
    UPDATE customer SET 
        address=:address, 
        balance_in_eur=:balance_in_eur,
        notes=:customer_notes
    WHERE customer_id=:customer_id
    '''

    __sql_insert_dog = '''
    INSERT INTO dog(customer_id, name, birth_date, breed, is_male, notes)
    VALUES(:customer_id, :dog_name, :birth_date, :breed, :is_male, :dog_notes)
    '''

    __sql_update_dog = '''
    UPDATE dog SET
        name=:dog_name,
        birth_date=:birth_date,
        breed=:breed,
        is_male=:is_male,
        notes=:dog_notes
    WHERE dog_id=:dog_id
    '''

    __sql_insert_person = '''
    INSERT INTO person(customer_id, name, phone1, phone2, email_address)
    VALUES(:customer_id, :person_name, :phone1, :phone2, :email_address)
    '''

    __sql_update_person = '''
    UPDATE person SET
        name=:person_name,
        phone1=:phone1,
        phone2=:phone2,
        email_address=:email_address
    WHERE person_id=:person_id
    '''

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

    def get_all_customers(self) -> pandas.DataFrame:
        logger.debug('get_all_customers')
        return pandas.read_sql(DataProvider.__sql_get_all_customers, self.__connection)

    def get_customer_by_dog_id(self, dog_id: int) -> Customer:
        logger.debug('get_customer_by_dog_id')
        customer_df = pandas.read_sql(DataProvider.__sql_customer_by_dog_id, self.__connection,
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
        cur = self.__connection.execute(self.__sql_insert_customer, customer_data)
        customer_id = cur.lastrowid
        logger.info(f'Customer inserted with id ${customer_id}')
        return customer_id

    def update_customer(self, customer_data: dict) -> None:
        logger.info(f'Updating customer: ${customer_data}')
        self.__connection.execute(self.__sql_update_customer, customer_data)
        logger.info(f'Customer updated')

    def insert_dog(self, dog: dict, customer_id: int) -> int:
        logger.info(f'Inserting dog of customer {customer_id}: ${dog}')
        params = dog.copy()
        params['customer_id'] = customer_id
        cur = self.__connection.execute(self.__sql_insert_dog, params)
        dog_id = cur.lastrowid
        logger.info(f'Dog inserted with id ${dog_id}')
        return dog_id

    def update_dog(self, dog: dict) -> None:
        logger.info(f'Updating dog: ${dog}')
        self.__connection.execute(self.__sql_update_dog, dog)
        logger.info(f'Dog updated')

    def insert_person(self, person: dict, customer_id: int) -> int:
        logger.info(f'Inserting person of customer {customer_id}: ${person}')
        params = person.copy()
        params['customer_id'] = customer_id
        cur = self.__connection.execute(self.__sql_insert_person, params)
        person_id = cur.lastrowid
        logger.info(f'Person inserted with id ${person_id}')
        return person_id

    def update_person(self, person: dict) -> None:
        logger.info(f'Updating person: ${person}')
        self.__connection.execute(self.__sql_update_person, person)
        logger.info(f'Person updated')
