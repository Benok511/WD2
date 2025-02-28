
DROP TABLE IF EXISTS customers;


CREATE TABLE customers (
    user_id TEXT PRIMARY KEY NOT NULL,
    password TEXT NOT NULL,
    is_admin INTEGER DEFAULT 0
);

DROP TABLE IF EXISTS menu;


CREATE TABLE menu (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT NOT NULL,
    price INTEGER NOT NULL,
    stock INTEGER NOT NULL,
    image TEXT NOT NULL,
    description text NOT NULL

);

DROP TABLE IF EXISTS placed_order;


CREATE TABLE placed_order (
    order_num INTEGER PRIMARY KEY AUTOINCREMENT, 
    user_id TEXT NOT NULL,
    order_datetime DATETIME NOT NULL,
    order_address TEXT NOT NULL,
    instructions TEXT DEFAULT 'None',
    price INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES customers(user_id)
);

DROP TABLE IF EXISTS in_order;


CREATE TABLE in_order (
    order_num INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity INTEGER,
    PRIMARY KEY (order_num, item_id),
    FOREIGN KEY (order_num) REFERENCES placed_order(order_num),
    FOREIGN KEY (item_id) REFERENCES menu(item_id)
);

DROP TABLE IF EXISTS reviews;

CREATE TABLE reviews (
    review_num INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    date_sent DATE NOT NULL,
    rating INTEGER NOT NULL,
    details TEXT NOT NULL
);



INSERT INTO menu (item_name, price, stock, image, description) VALUES
    ('Apple Tart', 5, 20, 'appletart.jpg', 'A delicious apple tart with a buttery crust.'),
    ('Baguette', 3, 15, 'baguette.jpg', 'A classic French baguette with a crispy crust.'),
    ('Brownies', 4, 25, 'brownies.jpg', 'Rich and fudgy chocolate brownies.'),
    ('Cake', 10, 10, 'cake.jpg', 'A delightful sponge cake with creamy frosting.'),
    ('Cheesecake', 7, 12, 'Cheesecake.jpg', 'Creamy cheesecake with a graham cracker crust.'),
    ('Chocolate Biscuit Cake', 6, 18, 'chocbiscuitcake.jpg', 'A crunchy and chocolatey biscuit cake.'),
    ('Cookie', 2, 30, 'cookie.jpg', 'A classic chocolate chip cookie.'),
    ('Croissant', 4, 22, 'Croissant,_whole.jpg', 'A flaky, buttery croissant.'),
    ('Donut', 3, 28, 'donut.jpg', 'A soft, glazed donut.'),
    ('Eclair', 5, 15, 'eclair.png', 'A chocolate-covered éclair with cream filling.'),
    ('Muffin', 3, 20, 'muffin.jpg', 'A fluffy blueberry muffin.'),
    ('Pain au Chocolat', 4, 18, 'painauchoc.jpg', 'A croissant filled with chocolate.');

SELECT * from customers

UPDATE placed_order SET user_id = 'test' WHERE user_id = ''

SELECT * from placed_order

ALTER TABLE placed_order ADD TEXT DEFAULT 'In Progress';

DELETE FROM menu WHERE item_name = '1'

SELECT * FROM reviews