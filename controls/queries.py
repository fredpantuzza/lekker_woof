########################################
#              CUSTOMER                #
########################################

sql_get_all_customers = '''
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

sql_customer_by_dog_id = '''
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

sql_insert_customer = '''
INSERT INTO customer(address, balance_in_eur, notes)
VALUES(:address, :balance_in_eur, :customer_notes)
'''

sql_update_customer = '''
UPDATE customer SET 
    address=:address, 
    balance_in_eur=:balance_in_eur,
    notes=:customer_notes
WHERE customer_id=:customer_id
'''

sql_insert_dog = '''
INSERT INTO dog(customer_id, name, birth_date, breed, is_male, notes)
VALUES(:customer_id, :dog_name, :birth_date, :breed, :is_male, :dog_notes)
'''

sql_update_dog = '''
UPDATE dog SET
    name=:dog_name,
    birth_date=:birth_date,
    breed=:breed,
    is_male=:is_male,
    notes=:dog_notes
WHERE dog_id=:dog_id
'''

sql_insert_person = '''
INSERT INTO person(customer_id, name, phone1, phone2, email_address)
VALUES(:customer_id, :person_name, :phone1, :phone2, :email_address)
'''

sql_update_person = '''
UPDATE person SET
    name=:person_name,
    phone1=:phone1,
    phone2=:phone2,
    email_address=:email_address
WHERE person_id=:person_id
'''

########################################
#              TRAINING                #
########################################

sql_get_all_trainings = '''
SELECT
    t.training_id,
    t.name,
    t.price,
    t.classes_online,
    t.classes_in_person,
    t.created_timestamp
FROM training t;
'''

sql_training_by_id = '''
SELECT
    t.training_id,
    t.name,
    t.price,
    t.classes_online,
    t.classes_in_person,
    t.created_timestamp
FROM training t
WHERE t.training_id=:training_id
'''

sql_insert_training = '''
INSERT INTO training(name, price, classes_online, classes_in_person)
VALUES(:name, :price, :classes_online, :classes_in_person)
'''

sql_update_training = '''
UPDATE training SET 
    name=:name, 
    price=:price,
    classes_online=:classes_online,
    classes_in_person=:classes_in_person
WHERE training_id=:training_id
'''
