#!Python

from flask import Flask, request, make_response, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from achive_cache import AchiveCache
from dotenv import load_dotenv
from os.path import join, dirname
from os import urandom, environ


# -----------------------------------------------------------------------------

# Settings block

app = Flask(__name__)

# -----------------------------------------------------------------------------

# USER SETTINGS

# -----------------------------------------------------------------------------

app.config["PAGINATION_PAGE_LIM"] = 3  # pagination val page/records 3 default
app.config["GLOBAL_CACHE_BUFFER"] = 4  # default value for cache

# -----------------------------------------------------------------------------

# Load database configurations

load_dotenv(join(dirname(__file__), '.env'))

# pick up from .env

db_settings = {
    'user': environ.get('DB_USER'),
    'password': environ.get('DB_PASS'),
    'host': environ.get("DB_HOST"),
    'port': environ.get('DB_PORT'),
    'dbname': environ.get("DB_NAME")
}

# database uri formation:

app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://%s:%s@%s:%s/%s" % (
    environ.get('DB_USER'),
    environ.get('DB_PASS'),
    environ.get('DB_HOST'),
    environ.get('DB_PORT'),
    environ.get('DB_NAME'))


app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Database initiating

db = SQLAlchemy(app)

# cache creating

cache = AchiveCache(app.config["GLOBAL_CACHE_BUFFER"])

# -----------------------------------------------------------------------------

# support functionality


def page_json(page_request) -> dict:
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


def request_query_builder(asin, page) -> dict:
    """
    Function builder of answer with pagination
    contains function which paginates in filtered query
    """

    product = Products.query.filter(Products.asin == asin).first()

    page_request = Reviews.query.filter(asin == Reviews.asin).\
        paginate(page, app.config["PAGINATION_PAGE_LIM"]).items

    # finalised product card for
    data = {
        'asin': asin,
        'product_title': product.title,
        str(page): page_json(page_request),
        'state': True,
        'date': datetime.now()
    }

    return data


def checking_module(request) -> bool:
    """
    Function provides all checks
    """

    if not request.json:

        # fail if empty requests json

        return True

    if 'asin' not in request.json or type(request.json['asin']) != str or\
            len(request.json['asin']) != 10 or request.json['asin'] == '':

        # fail if no 'asin' or it`s different from str
        # or lenth of key asin is not 10 or empty json field

        return True

    product = Products.query.get_or_404(request.json['asin'])

    if 'title' not in request.json or type(request.json['title']) != str or\
            len(request.json['title']) > 1000 or request.json['title'] == '':

        # fail if no 'title' or it`s different from str
        #  or lenth of title > 1000 or empty json field

        return True

    if 'review' not in request.json or type(request.json['review']) != str or\
            request.json['review'] == '' or len(request.json['review']) > 10000:

        # fail if no 'review' or it`s different from str
        # or lenth of review > 10000 or empty json field

        return True

    return False

# -----------------------------------------------------------------------------

# Error handlers


@app.errorhandler(404)
def page_not_found(errorhandler):

    err = str(errorhandler).split(':')
    err_json = {
        err[0]: err[1],
        'state': False
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
    asin = db.Column(
        db.String(10),
        db.ForeignKey('products.asin'),
        nullable=False)
    title = db.Column(db.String(1000), nullable=False)
    review = db.Column(db.String(10000), nullable=False)

    def __repr__(self):
        return '<Reviews %r>' % self.asin

# -----------------------------------------------------------------------------

# Routes block


@app.route('/todo/api/v1.1/<asin>/<int:page>', methods=['GET'])
def index(asin, page):
    """
    Main route for GET request
    """

    # Cache processing

    if cache.check_available(asin, page):

        data = cache.get_from_cache(asin, page)

    else:

        data = request_query_builder(asin, page)
        cache.add_to_cache(asin, page, data)

    # removing service time field from responce
    final = dict(data)
    del final['date']

    return jsonify(final)


@app.route('/todo/api/v1.1/reviewadd', methods=['PUT'])
def put_review():
    """
    Route for review adding to database
    contains main check tests of availibility of fields json
    """

    if checking_module(request):
        return wrong_fields()

    # databae new object creating

    new_review = Reviews(
        asin=request.json['asin'],
        title=request.json['title'],
        review=request.json['review']
    )

    try:

        # wrote to db

        db.session.add(new_review)
        db.session.commit()
        cache.del_chain_asin(request.json['asin'])

        # Success answer

        return jsonify({
            'Success': True,
            'For': request.json['asin']
        })

    except Exception:

        return method_not_allowed()

# -----------------------------------------------------------------------------


if __name__ == '__main__':

    app.run(host='127.0.0.1', debug=True, port=1110)
    # ssl_context='adhoc')
