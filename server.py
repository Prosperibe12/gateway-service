import os, gridfs, pika, json
from flask import Flask, request
from flask_pymongo import PyMongo
from auth_svc.access import AuthService
from storage import utils

# instantiate flask and set mongodb url
server = Flask(__name__)
server.config["MONGO_URI"] = "mongodb://mongodb-service:27017/videos"

# create a PyMongo and GridFs instance 
mongo = PyMongo(server)
# create mongodb interface for sharding files and store them in chunks
fs = gridfs.GridFS(mongo.db)

# create a connection to Rabbitmq
connection = pika.BlockingConnection(pika.URLParameters("rabbitmq"))
channel = connection.channel()

# create an instance of AuthService Class
auth_svc = AuthService(os.environ.get("AUTH_SVC_ADDRESS"))

@server.route("/", methods=["GET"])
def home():
    return {"Service_Name": "Gateway Service"}

# create routes to direct request to other services
@server.route("/login/", methods=["POST"])
def login():
    """
    Gateway Service login function.
    It validates user credentials by sending a request to the AUTH SERVICE.
    """
    token, err = auth_svc.login(request)
    if err:
        return {"error": err}, 401
    return {"token": token}, 200

@server.route("/upload/", methods=["POST"])
def upload():
    """
    Gateway Service Upload function.
    Takes a user uploaded file, validates user authorization credentials and if valid,
    puts a message in queue for converter service.
    """
    access_data, err = auth_svc.token(request)
    if err:
        return {"error": "Invalid token"}, 401

    access_data = json.loads(access_data)
    # validate claims
    if access_data["data"].get("token_type") == "access":
        if len(request.files) != 1:
            return {"error": "Only 1 file is required"}, 400

        # get request files
        for _, f in request.files.items():
            # put message in queue
            err = utils.upload(f, fs, channel, access_data)
            if err:
                return {"error": err}, 500

        return {"message": "Success! You will be notified when your video is converted"}, 200

    return {"error": "Not authorized"}, 401

@server.route("/download/", methods=["GET"])
def download():

    """
    Gateway Service Download function.
    Provide method for user converted mp3 file.
    Retrieves the requested file from the storage service.
    """
    access_data, err = auth_svc.token(request)
    if err:
        return {"error": "Invalid token"}, 401

    access_data = json.loads(access_data)
    # validate claims
    if access_data["data"].get("token_type") == "access":
        file_id = request.args.get("file_id")
        if not file_id:
            return {"error": "File ID is required"}, 400

        try:
            # retrieve file from GridFS
            file = fs.get(file_id)
            return file.read(), 200, {"Content-Type": "application/octet-stream"}
        except gridfs.errors.NoFile:
            return {"error": "File not found"}, 404

    return {"error": "Not authorized"}, 401

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8000)

    