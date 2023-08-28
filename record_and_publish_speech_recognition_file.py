import websocket
import time
import json
import os
import subprocess
import _thread
import rel
import re
import argparse
import platform
import datetime
import hashlib


from pvrecorder import PvRecorder
import wave
import struct

for index, device in enumerate(PvRecorder.get_available_devices()):
    print(f"[{index}] {device}")

recorder = PvRecorder(device_index=3, frame_length=512)
audio = []

try:
    recorder.start()

    while True:
        frame = recorder.read()
        audio.extend(frame)
except KeyboardInterrupt:
    recorder.stop()
    with wave.open("demo.wav", 'w') as f:
        f.setparams((1, 2, 16000, 512, "NONE", "NONE"))
        f.writeframes(struct.pack("h" * len(audio), *audio))
finally:
    recorder.delete()



# parser = argparse.ArgumentParser(description='')
# parser.add_argument('--audio_file', help='Audio File', required=True, type=str)
# parser.add_argument('--method', help='Speech Recognition Model', required=True, type=str)
# parser.add_argument('--requestor_type', help='Requestor Type', required=True, type=str)

# args = parser.parse_args()
# audio_file = args.audio_file
# print("Audio File: ", audio_file)
# method = args.method
# print("Speech Recognition Model: ", method)
# requestor_type = args.requestor_type
# print("Requestor Type: ", requestor_type)


audio_file = "demo.wav"
method = "Whisper"
requestor_type = "NSSD"


# Put in Input JSON File
entity_types = ['PERSON', 'NORP', 'FAC', 'ORG', 'GPE', 'LOC', 'PRODUCT', 'EVENT', 'WORK_OF_ART', 'LAW', 'LANGUAGE', 'DATE', 'TIME', 'PERCENT', 'MONEY', 'QUANTITY', 'ORDINAL', 'CARDINAL']

def on_error(ws, error):
    print(error)


def on_close(ws, close_status_code, close_msg):
    print("### Connection closed ###")


def on_open(ws):
    print("### Connection established ###")

def publish(entity_types, audio_file):
    requestor_id = platform.node()

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
                "topic_name": "SIFIS:Privacy_Aware_Speech_Recognition",
                "topic_uuid": "Speech_Recognition",
                "value": {
                    "description": "Speech Recognition",
                    "requestor_id": str(requestor_id),
                    "requestor_type": str(requestor_type),
                    "request_id": str(request_id),
                    "Type": "Audio_file",
                    "Entity Types": entity_types,
                    "Audio File": str(audio_file),
                    "method": str(method)
                }
            }
        }
    ws.send(json.dumps(ws_req))

publish(entity_types, audio_file)