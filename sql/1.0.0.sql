CREATE TABLE customer (
    customer_id INTEGER PRIMARY KEY,
    address TEXT NOT NULL,
    balance_in_eur REAL NOT NULL DEFAULT 0,
    notes TEXT,
    created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE person (
    person_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    phone1 TEXT NOT NULL,
    phone2 TEXT NULL,
    email_address TEXT NOT NULL,
    created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_person_customer FOREIGN KEY (customer_id) REFERENCES customer(customer_id)
);

CREATE TABLE dog (
    dog_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    birth_date DATE NOT NULL,
    breed TEXT NOT NULL,
    is_male BOOLEAN NOT NULL,
    notes TEXT,
    created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_dog_customer FOREIGN KEY (customer_id) REFERENCES customer(customer_id)
);

-- Types of training
CREATE TABLE training (
    training_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    classes_online INTEGER NOT NULL,
    classes_in_person INTEGER NOT NULL,
    notes TEXT,
    created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Subscription is the purchase of a training
CREATE TABLE subscription (
    subscription_id INTEGER PRIMARY KEY,
    training_id INTEGER NOT NULL,
    dog_id INTEGER NOT NULL,
    actual_price REAL NOT NULL,
    notes TEXT,
    created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_subscription_training FOREIGN KEY (training_id) REFERENCES training(training_id),
    CONSTRAINT fk_subscription_dog FOREIGN KEY (dog_id) REFERENCES dog(dog_id)
);

-- Class is the execution of a training lesson
CREATE TABLE class (
    class_id INTEGER PRIMARY KEY,
    -- Expect either subscription_id or dog_id+single_class_price
    subscription_id INTEGER,
    dog_id INTEGER,
    single_class_price REAL,
    is_online BOOLEAN NOT NULL,
    class_date DATE,
    notes TEXT,
    created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_class_subscription FOREIGN KEY (subscription_id) REFERENCES subscription(subscription_id),
    CONSTRAINT fk_class_dog FOREIGN KEY (dog_id) REFERENCES dog(dog_id)
);

CREATE TABLE payment (
    payment_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    payment_date DATE NOT NULL,
    amount REAL NOT NULL,
    CONSTRAINT fk_payment_customer FOREIGN KEY (customer_id) REFERENCES customer(customer_id)
);