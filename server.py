import asyncio
import os 

from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer

redpanda_server = "localhost:9092"  # Replace with your Redpanda server address
request_topic = "image-request"
reply_topic = "image-reply"


# Startup event handler
@asynccontextmanager
async def startup(app):
    app.producer = AIOKafkaProducer(bootstrap_servers=[redpanda_server])
    await app.producer.start()
    
    app.consumer = AIOKafkaConsumer(
        reply_topic,
        group_id="image-reply-group"
    )
    await app.consumer.start()

    yield

app = FastAPI(lifespan=startup)

# Mount the static directory to serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Redirect root URL to the static index.html
@app.get("/")
async def read_index():
    return FileResponse('static/index.html')

# Endpoint to upload an image
@app.post("/upload-image/")
async def upload_image(file: UploadFile = File(...)):
    # Save the file
    current_dir = os.path.dirname(os.path.realpath(__file__))
    file_location = os.path.join(current_dir, f"static/images/{file.filename}")
    print(f"Saving file to {file_location}")
    with open(file_location, "wb") as file_object:
        file_object.write(await file.read())
    
    # Send filename to Redpanda
    await app.producer.send(request_topic, file.filename.encode('utf-8'))
    return {"filename": file.filename}

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    async def send_message_to_websocket(msg):
        await websocket.send_text(msg.value.decode('utf-8'))

    async def consume_from_topic(topic, callback):
        print(f"Consuming from {topic}")
        async for msg in app.consumer:
            print(f"Received message: {msg.value.decode('utf-8')}")
            await callback(msg)

    # Start consuming
    asyncio.create_task(consume_from_topic(reply_topic, send_message_to_websocket))

    # Keep the connection open
    while True:
        await asyncio.sleep(10)



