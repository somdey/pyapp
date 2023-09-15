from crypt import methods
from flask import Flask, request, jsonify, Response
from flask_restful import Api, Resource, reqparse
from pymongo import MongoClient 
import os
import uuid
from bson.json_util import dumps, loads
import json
import jwt
from werkzeug.security import generate_password_hash,check_password_hash
import datetime
from functools import wraps


app = Flask(__name__)
api = Api(app)

app.config['SECRET_KEY'] = '18aa08d7eb861ea5a544200a778890cd'
MONGODB_USERNAME = os.environ.get('MONGODB_USERNAME')
MONGODB_PASSWORD = os.environ.get('MONGODB_PASSWORD')
MONGODB_HOSTNAME = os.environ.get('MONGODB_HOSTNAME')
MONGO_URI = "mongodb://%s:%s@%s/?authSource=admin" % (MONGODB_USERNAME, MONGODB_PASSWORD, MONGODB_HOSTNAME)

cluster = MongoClient(MONGO_URI)
db      = cluster['flaskdb']
# giving the Todo_C name 
Todo_C  = db['todo']
Users  = db['users']

def token_required(f):
   @wraps(f)
   def decorator(*args, **kwargs):
       token = None
       if 'Authorization' in request.headers:
           token = request.headers['Authorization']
 
       if not token:
           return jsonify({'message': 'a valid token is missing'})
       try:
           token = token.split(" ")[1]
           data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
           current_user = Users.find_one({'public_id': data['public_id']})
       except:
           return jsonify({'message': 'token is invalid'})
 
       return f(current_user, *args, **kwargs)
   return decorator

class Todo(Resource):
    @token_required
    def get(self, current_user, todo_id):
        todo = Todo_C.find_one({'todo_id': todo_id})
        return  Response(json.dumps(todo,default=str),mimetype="application/json")

    @token_required
    def delete(self, current_user, todo_id):
        Todo_C.delete_many({'todo_id': todo_id})
        return {'message': 'Record deleted successfully'}
    @token_required
    def put(self, current_user, todo_id):
        name  = request.json['name']
        description = request.json['description']
        todo_dict = {
            "name"    : name,
            "description"   : description
        }
        Todo_C.update_many({'todo_id': todo_id}, {'$set': todo_dict})
        return {'message': 'Record updated successfully'}


class TodoList(Resource):
    @token_required
    def get(self, current_user):
        todo_list = Todo_C.find()
        todo_list = [todo for todo in todo_list]
        parser = reqparse.RequestParser()
        parser.add_argument('page', type=int, default=1)
        parser.add_argument('per_page', type=int, default=10)
        args = parser.parse_args()

        page = args['page']
        per_page = args['per_page']
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page

        items_page = todo_list[start_idx:end_idx]
        return Response(json.dumps({'items': items_page, 'total_items': len(todo_list)},default=str),mimetype="application/json")
    
    @token_required
    def post(self, current_user):
        name  = request.json['name']
        description = request.json['description']
        todo_dict = {
            "todo_id": str(uuid.uuid4()),
            "name"    : name,
            "description"   : description

        }
        Todo_C.insert_one(todo_dict)
        return {'message': 'Sucessfully created'}

class Register(Resource):
    def post(self):
        data = request.get_json() 
        hashed_password = generate_password_hash(data['password'], method='sha256') 
        new_user = {
                "public_id":str(uuid.uuid4()), 
                "name":data['username'],
                "password":hashed_password, 
                "admin":False
        }
        Users.insert_one(new_user) 
        return {'message': 'registered successfully'}

class Login(Resource):
    def post(self):
        username  = request.json['username']
        password = request.json['password']
        if not username or not password: 
            return {"message": "Invalid username or password"}, 401
        
        user = Users.find_one({'name': username})
        if check_password_hash(user['password'], password):
            token = jwt.encode({'public_id' : user['public_id'], 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=45)}, app.config['SECRET_KEY'], "HS256")
            return {"token": token}
        return {"message": "login required"}, 401
    
api.add_resource(Register, '/register')
api.add_resource(Login, '/login')
api.add_resource(TodoList, '/todos')
api.add_resource(Todo, '/todos/<string:todo_id>')

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=os.environ.get('APP_PORT'))