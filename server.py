import os, gridfs, pika
from flask import Flask, request, jsonify, send_file
from flask_pymongo import PyMongo
from auth_svc.access import AuthService
from storage import utils
from bson.objectid import ObjectId
import gridfs
from pymongo.errors import PyMongoError
from gridfs.errors import NoFile

# instantiate flask and set mongodb url
server = Flask(__name__)

# create a PyMongo and GridFs instance 
mongo_uri = f"mongodb://{os.environ.get('MONGODB_HOST')}:27017"
mongo_video = PyMongo(server,uri=f"{mongo_uri}/videos")
mongo_mp3 = PyMongo(server,uri=f"{mongo_uri}/mp3s")

# create mongodb interface for sharding files and store them in chunks
fs_videos = gridfs.GridFS(mongo_video.db)
fs_mp3s = gridfs.GridFS(mongo_mp3.db)

# create a connection to Rabbitmq
parameters = pika.ConnectionParameters(
    host=os.environ.get("RABBITMQ_HOST"),  
    port=os.environ.get("RABBITMQ_PORT"), 
    credentials=pika.PlainCredentials("guest", "guest"),
    heartbeat=30,
    blocked_connection_timeout=300,
    connection_attempts=10,
    retry_delay=5,
    socket_timeout=120
)

connection = pika.BlockingConnection(parameters)
channel = connection.channel()

# create an instance of AuthService Class
auth_svc = AuthService(os.environ.get("AUTH_SVC_ADDRESS"))

@server.route("/", methods=["GET"])
def home():
    return {"Service_Name": "Gateway Service"}

# create routes to direct request to other services
@server.route("/register/", methods=["POST"])
def register():
    """
    Gateway Service registration function.
    """
    token, err = auth_svc.register(request)
    if err:
        return {"error": err}, 401
    return {"data": token}, 200

@server.route("/verify-email/", methods=["GET"])
def verify_email():
    """
    Handles user email verification by forwarding the token to the authentication service.
    """
    # get the token from query parameters
    token = request.args.get('token')

    # Validate if the token is provided
    if not token:
        return jsonify({"error": "Missing token"}), 400

    # request the authentication service to verify the token
    response_data, status_code = auth_svc.verify_email_token(token)

    return jsonify(response_data), status_code

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

    # Validate claims
    if access_data.get("data", {}).get("token_type") == "access":
        if len(request.files) != 1:
            return {"error": "Only 1 file is required"}, 400

        # get request files
        for _, f in request.files.items():
            # put message in queue
            err = utils.upload(f, fs_videos, channel, access_data)
            if err:
                return {"error": err}, 500

        return {"message": "Success! You will be notified when your video is converted"}, 200

    return {"error": "Not authorized"}, 401

@server.route("/download/", methods=["GET"])
def download():
    """
    Gateway Service Download function.
    Retrieves the requested file from the storage service.
    """
    access_data, err = auth_svc.token(request)
    
    if err:
        return {"error": "Invalid token"}, 401
    
    # Validate claims
    if access_data.get("data", {}).get("token_type") != "access":
        return {"error": "Not authorized"}, 401

    file_id = request.args.get("id")
    
    # Validate that file_id is passed
    if not file_id:
        return {"error": "File ID is required"}, 400

    # Ensure file_id is a valid ObjectId before querying GridFS
    if not ObjectId.is_valid(file_id):
        return {"error": "Invalid File ID format"}, 400

    try:
        # Retrieve file from GridFS
        file = fs_mp3s.get(ObjectId(file_id))
        return send_file(file, download_name=f"{file_id}.mp3")

    except NoFile:
        # Handle missing file exception
        print(f"Download Error: File with ID {file_id} not found in GridFS")
        return {"error": "File not found"}, 404

    except PyMongoError as db_err:
        #Handle MongoDB-related errors
        print(f"Download Error (MongoDB Issue): {db_err}")
        return {"error": "Database Error"}, 500

    except Exception as err: 
        # Catch all other unexpected errors
        print(f"Download Error: {err}")
        return {"error": "Internal Server Error"}, 500

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080)