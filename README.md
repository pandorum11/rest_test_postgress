#!Python

FLASK created API srv side app.

There are 2 main commands:

> curl -X GET http://127.0.0.1:1110/todo/api/v1.1/B06X14Z8JP/1

> curl -X PUT http://127.0.0.1:1110/todo/api/v1.1/reviewadd -H "Content-Type: application/json" -d "{\"asin\":\"B06X14Z8JP\", \"title\":\"THET WAS RLY GOOD\",\"review\":\"Fo no reson i like this stuf, spam, smam\"}"

The command are based on localhost srv addresses. Right order:

f"http://{yourhostname}/todo/api/v1.1/{product_asin}/{page}

f"http://{yourhostname}/todo/api/v1.1/{reviewadd} -H "Content-Type: application/json" -d "{\"asin\":\"{product_asin}\", \"title\":\"{review_title}\",\"review\":\"{review}\"}"

For Windows - while using curl command, in json body place slash before "

#--------------------------------------------------------------------------------------------------------

** All code setting are based at top of code:

- SQLALCHEMY_DATABASE_URI	- >	set database
- PAGINATION_PAGE_LIM		- > set page/record quantity
- GLOBAL_CACHE_BUFFER		- > set global buffer of cache

#--------------------------------------------------------------------------------------------------------

** Using PostgreSQL V.13 psql commands for create DB:

> CREATE TABLE Products (Title VARCHAR(300) NOT NULL,Asin VARCHAR(10) NOT NULL PRIMARY KEY);

> \copy Products FROM 'C:\Users\Wrong_Way\Desktop\G1\testdb\Products.csv' DELIMITER ',' CSV;

> CREATE TABLE Reviews (id SERIAL PRIMARY KEY, asin VARCHAR(10), Title VARCHAR(1000) NOT NULL, Review VARCHAR(10000) NOT NULL, FOREIGN KEY (asin) REFERENCES Products (asin) ON DELETE CASCADE ON UPDATE CASCADE);

> \copy Reviews(asin, title, review) FROM 'C:\Users\Wrong_Way\Desktop\G1\testdb\Reviews.csv' DELIMITER ',' CSV HEADER;

#--------------------------------------------------------------------------------------------------------

Test_TT_docs:

> https://docs.google.com/document/d/1OapNUAMfUz12KOgWJXPH8lyGHpxRI9r0WncbYYALxFE/edit