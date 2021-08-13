#!Python

from flask import Flask, request, make_response, abort, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import json
from datetime import datetime

# our database uri

# -----------------------------------------------------------------------------

username = "postgres"
password = "111"
dbname = "G_sheets"

app = Flask(__name__)
app.config['SECRET_KEY'] = "SECRETKEY"

app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql://{username}:{password}@localhost:5432/{dbname}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["PAGINATION_PAGE_LIM"] = 3
app.config["GLOBAL_CACHE_BUFFER"] = 4

db = SQLAlchemy(app)


# -----------------------------------------------------------------------------

# support functionality

def page_json(page_request):

    data = {}
    for review in page_request:
        data[review.title] = review.review

    return data

def request_query_builder(asin, page):

    """
    Function builder of answer with pagination
    contains function which paginates in filtered query
    """

    product = Products.query.filter(Products.asin == asin).first()
    page_request = Reviews.query.filter(Reviews.asin == asin).\
        paginate(page=page, per_page=app.config["PAGINATION_PAGE_LIM"]).items
     
    #finalised product card for 
    data = {
            'asin' : asin,
            'product_title' : product.title,
            str(page) : page_json(page_request),
            'state' : True,
        }   

    return data


# -----------------------------------------------------------------------------
# Cache classs

class AchiveCatche:

    def __init__(self):
        self.global_cash = {}
        self.time_store = {}

    def __repr__(self):
        return self.global_cash


    def add_to_cache(self, asin, page, data):

        if len(self.time_store) > app.config["GLOBAL_CACHE_BUFFER"]:
            del_cache_by_size()

        if asin in self.global_cash:
            if page not in self.global_cash[asin]:
                pass
            else:
                return
        else:
            self.global_cash[asin] = {}

        self.global_cash[asin][page] = data
        self.time_store[datetime.now()] = asin + str(page)

        return


    def check_available(self, asin, page):

        if asin in self.global_cash:
            if page in self.global_cash[asin]:
                return True
            else:
                return False
        else:
            return False


    def get_from_cache(self, asin, page):

        return self.global_cash[asin][page]


    def del_chain_asin(self, asin):

        if asin in self.global_cash:
            del self.global_cash[asin]

        return


    def del_cache_by_size(self):

        # Get the row which was wrote the first
        sorted_time = sorted(self.time_store)
        first_row = self.time_store[sorted_time[0]]

        del self.time_store[sorted_time[0]]

        asin = sorted_time[:10]
        page = sorted_time[10:]

        del self.global_cash[asin][page]

        return



cache = AchiveCatche()

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

# -----------------------------------------------------------------------------

# database block

class Products(db.Model):
    """
    Table Reviews (for each product)

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
    Table Reviews (for each review)

    id      asin        title           review

    Integer String(10)  String(1000)    db.String(10000)

    for this table 'id' - primary key
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

# routes block

@app.route('/todo/api/v1.1/<asin>/<int:page>', methods=['GET'])
def index(asin, page):

    """
    Main route for GET request
    """

    # Cache processing

    # if len(global_cash) > app.config["GLOBAL_CACHE_BUFFER"]:
    if cache.check_available(asin, page):
        return jsonify(cache.get_from_cache(asin, page))

    else:
        data = request_query_builder(asin, page)
        cache.add_to_cache(asin, page, data)
        return jsonify(data)
        

        
@app.route('/todo/api/v1.1/reviewadd', methods=['PUT'])
def put_review():

    if not request.json:
        abort(400)

    if 'asin' not in request.json or type(request.json['asin']) != str or\
            len(request.json['asin']) != 10:
        abort(400)

    product = Products.query.get_or_404(request.json['asin'])

    if 'title' not in request.json or type(request.json['title']) != str or\
            len(request.json['title']) > 1000:
        abort(400)

    if 'review' not in request.json or type(request.json['review']) != str or\
            len(request.json['review']) > 10000:
        abort(400)


    new_review = Reviews(asin=product.asin, title=request.json['title'],\
            review=request.json['review'])

    try:

        db.session.add(new_review)
        db.session.commit()
        cache.del_chain_asin(request.json['asin'])

        return jsonify({
            'Success' : True,
            'For'     : product.asin
            })

    except Exception:
        return method_not_allowed()

# -----------------------------------------------------------------------------

if __name__ == '__main__':

    app.run(host = '127.0.0.1', debug=True, port = 1110)