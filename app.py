from crypt import methods
from flask import Flask, request, jsonify
from pymongo import MongoClient 
import os
import uuid
from bson.json_util import dumps, loads

app = Flask(__name__)

#MONGO_URI = os.environ.get('MONGO_URI')
MONGODB_USERNAME = os.environ.get('MONGODB_USERNAME')
MONGODB_PASSWORD = os.environ.get('MONGODB_PASSWORD')
MONGODB_HOSTNAME = os.environ.get('MONGODB_HOSTNAME')
MONGO_URI = "mongodb://%s:%s@%s/?authSource=admin" % (MONGODB_USERNAME, MONGODB_PASSWORD, MONGODB_HOSTNAME)

cluster = MongoClient(MONGO_URI)
db      = cluster['flaskdb']
# giving the collection name 
collection  = db['todo']

@app.route("/todo", methods=['POST'])
def create():
    name  = request.json['name']
    description = request.json['description']
    
    todo_dict = {
        "todo_id": str(uuid.uuid4()),
        "name"    : name,
        "description"   : description

    }
    print
    collection.insert_one(todo_dict)
    return "success"

 
@app.route("/todo", methods=['GET'])
def get_all_todo():

    todo_list = collection.find()
    return jsonify(dumps(todo_list))

#for seeing the particular entire
@app.route("/todo/<todo_id>", methods=['GET'])
def get_todo(todo_id):
    todo = collection.find_one({'todo_id': todo_id})
    return jsonify(dumps(todo))

# update the existing entire
@app.route("/todo/<todo_id>", methods=['PUT'])
def update_todo(todo_id):
    name  = request.json['name']
    description = request.json['description']
    todo_dict = {
            "name"    : name,
            "description"   : description
        }

    collection.update_many({'todo_id': todo_id}, {'$set': todo_dict})
    return 'success'
    
@app.route("/todo/<todo_id>", methods=['DELETE'])
def delete_one_todo(todo_id):
    collection.delete_many({'todo_id': todo_id})
    return 'success'

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=os.environ.get('APP_PORT'))