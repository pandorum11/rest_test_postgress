#!Python

from flask import Flask, request, make_response, abort, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import json
from datetime import datetime
from achive_cache import AchiveCache

# -----------------------------------------------------------------------------

# our database uri

username = "postgres"
password = "111"
dbname = "G_sheets"

app = Flask(__name__)
app.config['SECRET_KEY'] = "SECRETKEY"

app.config["SQLALCHEMY_DATABASE_URI"] =\
            f"postgresql://{username}:{password}@localhost:5432/{dbname}"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["PAGINATION_PAGE_LIM"] = 3
app.config["GLOBAL_CACHE_BUFFER"] = 4

db = SQLAlchemy(app)

# cache activation

cache = AchiveCache(app.config["GLOBAL_CACHE_BUFFER"])

# -----------------------------------------------------------------------------

# support functionality

def page_json(page_request):

    """
    Making json from request, if there are repeating titles
    they extends by prefix (number)_copy
    """

    data = {}
    i = 1

    for review in page_request:

        if review.title in data:
            data[f'({i}_copy) {review.title}'] = review.review
            i += 1
        else:
            data[review.title] = review.review

    return data

def request_query_builder(asin, page):

    """
    Function builder of answer with pagination
    contains function which paginates in filtered query
    """

    product = Products.query.filter(Products.asin == asin).first()
    page_request = Reviews.query.filter(asin == Reviews.asin).\
        paginate(page, 3).items

    print(page_request)
     
    #finalised product card for 
    data = {
            'asin' : asin,
            'product_title' : product.title,
            str(page) : page_json(page_request),
            'state' : True,
            'date' : datetime.now()
        }   

    return data

# -----------------------------------------------------------------------------

# Error handlers

@app.errorhandler(404)
def page_not_found(errorhandler):

    err = str(errorhandler).split(':')
    err_json = {
        err[0]  :   err[1],
        'state' :   False
        }

    return make_response(jsonify(err_json), 404)


@app.errorhandler(405)
def method_not_allowed():

    return make_response(jsonify({'error': 'Method Not Allowed'}), 405)

@app.errorhandler(406)
def wrong_fields():

    return make_response(jsonify({'Not Acceptable 406': 'Wrong fields\
        of request or empty requests json'}), 406)

# -----------------------------------------------------------------------------

# Database block

class Products(db.Model):

    """
    Class Table Reviews (for each product)

    title           asin

    String(300)     db.String(10)

    for this table 'asin' - primary key
    """

    __tablename__ = 'products'
    title = db.Column(db.String(300), nullable=False)
    asin = db.Column(db.String(10), primary_key=True)

    def __repr__(self):
        return '<Products %r>' % self.asin


class Reviews(db.Model):

    """
    Class Table Reviews (for each review)

    id      asin        title           review

    Integer String(10)  String(1000)    db.String(10000)

    for this table 'id' - primary key

    asin - > foreign key Products.asin
    """

    __tablename__ = 'reviews'
    id = db.Column(db.Integer(), primary_key=True)
    asin = db.Column(db.String(10), db.ForeignKey('products.asin'), nullable=False)
    title = db.Column(db.String(1000), nullable=False)
    review = db.Column(db.String(10000), nullable=False)

    def __repr__(self):
        return '<Reviews %r>' % self.asin

    def to_json(self):
        return {
            'id': self.id,
            'asin': self.asin,
            'title': self.title,
            'review': self.review
        }

# -----------------------------------------------------------------------------

# Routes block

@app.route('/todo/api/v1.1/<asin>/<int:page>', methods=['GET'])
def index(asin, page):

    """
    Main route for GET request
    """

    # Cache processing

    if cache.check_available(asin, page):
        print(cache.global_cash)

        return jsonify(cache.get_from_cache(asin, page))

    else:

        print(cache.global_cash)
        data = request_query_builder(asin, page)
        cache.add_to_cache(asin, page, data)
        return jsonify(data)
        

        
@app.route('/todo/api/v1.1/reviewadd', methods=['PUT'])
def put_review():

    """
    Route for review adding to database
    contains main check tests of availibility of fields json
    """

    if not request.json:

        # fail if empty requests json

        return wrong_fields()

    if 'asin' not in request.json or type(request.json['asin']) != str or\
            len(request.json['asin']) != 10:

        # fail if no 'asin' or it`s different from str or lenth of key asin is not 10

        return wrong_fields()

    product = Products.query.get_or_404(request.json['asin'])

    if 'title' not in request.json or type(request.json['title']) != str or\
            len(request.json['title']) > 1000:

        # fail if no 'title' or it`s different from str or lenth of title > 1000

        return wrong_fields()

    if 'review' not in request.json or type(request.json['review']) != str or\
            len(request.json['review']) > 10000:

        # fail if no 'review' or it`s different from str or lenth of review > 10000

        return wrong_fields()


    # databae new object creating

    new_review = Reviews(asin=product.asin, title=request.json['title'],\
            review=request.json['review'])

    try:

        # wrote to db

        db.session.add(new_review)
        db.session.commit()
        cache.del_chain_asin(request.json['asin'])

        # Success answer

        return jsonify({
            'Success' : True,
            'For'     : product.asin
            })

    except Exception:

        return method_not_allowed()

# -----------------------------------------------------------------------------

if __name__ == '__main__':

    app.run(host = '127.0.0.1', debug=True, port = 1110, ssl_context='adhoc')