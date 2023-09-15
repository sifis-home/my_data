import websocket
import time
import json
import os
import subprocess
import _thread
import rel
import re
import argparse
import socket
import datetime
import hashlib


from pvrecorder import PvRecorder
import wave
import struct

for index, device in enumerate(PvRecorder.get_available_devices()):
    print(f"[{index}] {device}")

recorder = PvRecorder(device_index=0, frame_length=512)
audio = []

try:
    recorder.start()

    while True:
        frame = recorder.read()
        audio.extend(frame)
except KeyboardInterrupt:
    recorder.stop()
    with wave.open("audio.wav", 'w') as f:
        f.setparams((1, 2, 16000, 512, "NONE", "NONE"))
        f.writeframes(struct.pack("h" * len(audio), *audio))
finally:
    recorder.delete()


audio_file = "audio.wav"
# method = "dp_noise"
# method = "scrample"
method = "nothing"
requestor_type = "NSSD"


def on_error(ws, error):
    print(error)


def on_close(ws, close_status_code, close_msg):
    print("### Connection closed ###")


def on_open(ws):
    print("### Connection established ###")

def publish(method, audio_file, requestor_type):

    ## getting the hostname by socket.gethostname() method
    hostname = socket.gethostname()
    ## getting the IP address using socket.gethostbyname() method
    ip_address = socket.gethostbyname(hostname)
    ## printing the hostname and ip_address
    print(f"Hostname: {hostname}")
    print(f"IP Address: {ip_address}")

    requestor_id = ip_address

    # Get current date and time
    now = datetime.datetime.now()

    # Generate a random hash using SHA-256 algorithm
    hash_object = hashlib.sha256()
    hash_object.update(bytes(str(now), 'utf-8'))
    hash_value = hash_object.hexdigest()

    # Concatenate the time and the hash
    request_id = str(requestor_id) + str(now) + hash_value
    request_id = re.sub('[^a-zA-Z0-9\n\.]', '', request_id).replace('\n', '').replace(' ', '')

    ws = websocket.WebSocketApp("ws://localhost:3000/ws",
                                on_open=on_open,
                                on_error=on_error,
                                on_close=on_close)

    ws.run_forever(dispatcher=rel)  # Set dispatcher to automatic reconnection
    rel.signal(2, rel.abort)  # Keyboard Interrupt

    ws_req = {
            "RequestPostTopicUUID": {
                "topic_name": "SIFIS:Privacy_Aware_Audio_Anomaly_Detection",
                "topic_uuid": "Audio_Anomaly_Detection",
                "value": {
                    "description": "Audio Anomaly Detection",
                    "requestor_id": str(requestor_id),
                    "requestor_type": str(requestor_type),
                    "request_id": str(request_id),
                    "Type": "Audio_file",
                    "audio_file": str(audio_file),
                    "method": str(method)
                }
            }
        }
    ws.send(json.dumps(ws_req))

publish(method, audio_file, requestor_type)