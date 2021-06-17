import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS
from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)


# db_drop_and_create_all()

# ROUTES

# get drinks route returns list of all the drinks
@app.route('/drinks', methods=['GET'])
def retrieve_drinks():
    try:
        drinks = Drink.query.order_by(Drink.id).all()

        return jsonify({
            'success': True,
            'drinks': [drink.short() for drink in drinks]})
    except:

        # if there are no drinks, return 404 error

        if len(drinks) == 0:
            abort(404)

# get drink detail route - requires authorization
# gets the details of each drink (ingredients)


@app.route('/drinks-detail', methods=['GET', 'POST'])
@requires_auth('get:drinks-detail')
def get_drink_detail(payload):

    try:

        drinks = [drink.long() for drink in Drink.query.all()]

        return jsonify({
            'success': True,
            'drinks': drinks
            })
    except:
        abort(500)


# create a drink - requires authorization

@app.route('/drinks', methods=['GET', 'POST'])
@requires_auth('post:drinks')
def add_drink(payload):
    body = request.get_json()

    if not body:
        abort(422)
    if 'title' not in body or 'recipe' not in body:
        abort(422)

    try:
        title = body['title']
        recipe_json = json.dumps(body['recipe'])
        drink = Drink(title=title, recipe=recipe_json)

        drink.insert()

        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        })

    except:
        abort(500)


# update drink - requires authorization


@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(payload, id):
    body = request.get_json()
    drink = Drink.query.get(id)

    # if no drink return 404 error

    if drink is None:
        abort(404)

    # if title and recipe are present in the form update drink detail

    try:
        if 'title' in body:
            drink.title = body['title']
        if 'recipe' in body:
            drink.recipe = json.dumps(body['recipe'])

        drink.update()

        return jsonify({
            'success': True,
            'drinks': [drink.long()]
            })
    except:
        abort(404)


# delete drink - requires authorization


@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, id):

    drink = Drink.query.filter(Drink.id == id).one_or_none()

    # if no drink return 404 otherwise delete drink

    if drink is None:
        abort(404)

    drink.delete()

    return jsonify({
        'success': True,
        'delete': drink.id
        })


# Error Handling


# Malformed request error - the request cannot be processed due to client error
@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 400,
        'message': 'bad request'
        }), 400

# No authorization error - authentication has not been provided


@app.errorhandler(AuthError)
def unauthorized(error):
    return jsonify({
        'success': False,
        'error': 401,
        'message': 'unauthorized'
        }), 401

# No permission error
# Used to handle requests where permission missing for user


@app.errorhandler(403)
def forbidden(error):
    return jsonify({
        'success': False,
        'error': 403,
        'message': 'forbidden'
        }), 403

# Resource not found error


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 404,
        'message': 'resource not found'
        }), 404

# Unprocessable error


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        'success': False,
        'error': 422,
        'message': 'unprocessable'
        }), 422


# Internal server error


@app.errorhandler(500)
def internal_server_error(error):
    print (error)
    return jsonify({
        'success': False,
        'error': 500,
        'message': 'internal server error'
        }), 500


@app.errorhandler(AuthError)
def AuthError(error):
    response = jsonify(error.error)
    response.status_code = error.status_code
    return response
