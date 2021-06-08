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

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
#db_drop_and_create_all()

# ROUTES

@app.route('/')
def index():
    return jsonify({
        "success": True,
        "message": "Welcome!"
    })

@app.route("/drinks", methods=['GET'])
def retrieve_drinks():
    try:
        drinks = Drink.query.order_by(Drink.id).all()

        return jsonify(
            {
                "success" : True,
                "drinks": [drink.short() for drink in drinks]    
                }), 200      
    except: 
        if len(drinks) == 0:
            abort(404)


@app.route("/drinks-detail", methods = ['GET'])
@requires_auth('get:drinks-detail')
def get_drink_detail(jwt):
    try:
        drink_detail = Drink.query.order_by(Drink.id).all()
        return jsonify({
            "success": True,
            "drinks": [drink.long() for drink in drink_detail]
        }), 200
    
    except:
        if len(drink_detail) == 0:
            abort(404)

@app.route('/drinks', methods = ['POST'])
@requires_auth('post:drinks')
def add_drink(jwt):
    body = request.get_json()
    
    new_title = body.get("title", None)
    recipe_json = json.dumps(body['recipe'])
    
    try:
        if not (
            "title" in body 
            or "recipe" in body
        ):
            abort(422)
        else:
            drink = Drink(
                title=new_title,
                recipe=recipe_json
            )
            drink.insert()

            return jsonify({
                "success": True,
                "created": drink.id,
                "drinks": [drink.long()]
            }), 200
    except:
        abort(422)


@app.route("/drinks/<int:drink_id>", methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(jwt, id):
    data = request.get_json()
    drink = Drink.query.filter(Drink.id==id).one_or_none()

    if drink is None:
        abort(404)
    try:
        if 'title' in data:
            drink.title=data['title']
        if 'recipe' in data:
            drink.recipe=json.dumps(request['recipe'])
        
        drink.update()

        return jsonify({
            "succes": True,
            "drinks": [drink.long()]
        }), 200
    except:
        abort(404)


@app.route("/drinks/<int:drink_id>", methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(jwt, id):

    drink = Drink.query.filter(Drink.id==id).one_or_none()

    if drink is None:
        abort(404)
    
    drink.delete()

    return jsonify({
        "success": True,
        "delete": drink.id
    }), 200


# Error Handling

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "bad request"
    }), 400

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": "unauthorized"
    }), 401

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message" : "resource not found"
    }), 404

@app.errorhandler(500)
def internal_server_error(error):
    print(error)
    return jsonify({
        "success": False,
        "error": 500,
        "message": "internal server error"
    }), 500

@app.errorhandler(AuthError)
def AuthError(error):
    return jsonify({
      "success": False,
      "error": error.status_code,
      "message": error.error.get('description')  
    }), error.status_code


