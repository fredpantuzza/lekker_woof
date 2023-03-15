DELETE FROM payment;
DELETE FROM class;
DELETE FROM subscription;
DELETE FROM training;
DELETE FROM dog;
DELETE FROM person;
DELETE FROM customer;

INSERT INTO customer (customer_id, balance_in_eur, address)
            SELECT 1, 0.0, 'Nowherestraat 122, Amsterdam'
UNION ALL   SELECT 2, -470.0, 'Lagoa Santa 119, BH'
UNION ALL   SELECT 3, 30.0, 'Star street 122, Universe';

INSERT INTO person (person_id, customer_id, name, phone1, email_address)
            SELECT 1, 1, 'Joaquim', '06 34567891', 'joaquiem@fake.com'
UNION ALL   SELECT 2, 2, 'Joao', '+55 31 98872-8736', 'joao@fake.com'
UNION ALL   SELECT 3, 2, 'Maria', '06 36767891', 'maria@fake.com'
UNION ALL   SELECT 4, 3, 'Toninho', '06 34567891', 'toninho@fake.com';

INSERT INTO dog (dog_id, customer_id, name, birth_date, breed, is_male, notes)
            SELECT 1, 1, 'Elton', '2020-10-01', 'Australian Shepherd', TRUE, 'Pain in the ass, needs therapy'
UNION ALL   SELECT 2, 2, 'Tonico', '2021-01-13', 'Labradoodle', TRUE, 'Cute'
UNION ALL   SELECT 3, 2, 'Tinoco ', '2021-07-33', 'Labradoodle', TRUE, 'Endemoniado'
UNION ALL   SELECT 4, 3, 'Anitta', '2017-04-01', 'German Shepherd', FALSE, 'Can I keep her?';

INSERT INTO training (training_id, name, price, classes_online, classes_in_person)
            SELECT 1, 'Separation anxiety - 5 classes', 500.0, 4, 1
UNION ALL   SELECT 2, 'Separation anxiety - 9 classes', 800.0, 8, 1
UNION ALL   SELECT 3, 'Separation anxiety - 13 classes', 1100.0, 12, 1
UNION ALL   SELECT 4, 'Reactive dog - 5 classes', 300.0, 4, 1
UNION ALL   SELECT 5, 'Reactive dog - 9 classes', 500.0, 8, 1
UNION ALL   SELECT 6, 'Reactive dog - 13 classes', 700.0, 12, 1;

INSERT INTO subscription (subscription_id, training_id, dog_id, actual_price, notes)
            SELECT 1, 2, 1, 800.0, 'Elton - Sep anxiety 9x'
UNION ALL   SELECT 2, 5, 2, 500.0, 'Tonico - Reactive 9x'
UNION ALL   SELECT 3, 5, 3, 400.0, 'Tinoco - Reactive 9x - Group discount wtih Tonico';

INSERT INTO class (class_id, subscription_id, dog_id, single_class_price, is_online, class_date, notes)
            SELECT 1, 1, NULL, NULL, TRUE, '2022-12-16', 'Elton - Sep anxiety 9x'
UNION ALL   SELECT 2, NULL, 2, 30.0, TRUE, '2022-12-01', 'Tonico & Tinoco - First call'
UNION ALL   SELECT 3, 2, NULL, NULL, FALSE, '2023-01-09', 'Tonico - Reactive 9x'
UNION ALL   SELECT 4, 3, NULL, NULL, FALSE, '2023-01-09', 'Tinoco - Reactive 9x'
UNION ALL   SELECT 5, NULL, 4, 30.0, TRUE, '2023-12-15', 'Anitta - First call';

INSERT INTO payment (payment_id, customer_id, payment_date, amount)
            SELECT 1, 1, '2022-12-10', 800.0 -- Joaquim pays Elton's training
UNION ALL   SELECT 2, 2, '2023-01-06', 400.0; -- Joao and Maria pay Tinoco's training