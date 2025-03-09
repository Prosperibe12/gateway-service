import pika, json
import pika.spec

def upload(f, fs, channel, access_data):
    """
    Uploads the provided file to the MongoDB database and sends a message to the queue for downstream processing.

    params:
    f (file): The file to be uploaded.
    fs (GridFS): The GridFS instance for MongoDB storage.
    channel (BlockingChannel): The channel for RabbitMQ communication.
    access_data (dict): The access data containing user authentication.
    """
    try:
        # save the uploaded file to db
        fid = fs.put(f)
    except Exception as err:
        return {"error": f"Internal Server Error: {err}"}, 500
    
    # define message to be sent
    message = {
        "video_fid": str(fid),
        "mp3_fid": None,
        "email": access_data["data"].get("email")
    }
    
    try:
        # publish message to queue and make it durable
        channel.basic_publish(
            exchange="",
            routing_key="video",
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ),
        )
    except Exception as er:
        # if message is not delivered, delete from the mongodb 
        fs.delete(fid)
        return {"error": f"Internal Server Error: {er}"}, 500
    
    return {"message": "File uploaded successfully", "file_id": str(fid)}, 200