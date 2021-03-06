#!/usr/bin/python3
from flask import Flask, request, jsonify, abort
from flask_sockets import Sockets
from decoder import decoder
import json
import logging
import os

logger = logging.getLogger("webapi")

app = Flask(__name__)
sockets = Sockets(app)

@app.route('/')
def app_running():
    return 'app is running !'

@app.route('/decoder/fromclient', methods=['POST'])
def decode_from_client():
    return jsonify(decoder.readMsg(request.get_data(as_text=True), True))


@app.route('/decoder/fromserver', methods=['POST'])
def decode_from_server():
    return jsonify(decoder.readMsg(request.get_data(as_text=True), False))

@app.route('/encode', methods=['POST'])
def encode_endpoint():
    jsonMsg = request.get_json()
    msgType = jsonMsg["__type__"]
    return decoder.write(msgType, jsonMsg).hex()

@app.errorhandler(Exception)
def exception_handler(error):
    print(error)
    return 'data couldn\'t be read', 400


@sockets.route('/decoder')
def echo_socket(ws):
    while not ws.closed:
        try:
            message = json.loads(ws.receive())
            logger.debug("Message received %s", message)
            ws.send(json.dumps(
                decoder.readMsg(message['data'], message['fromclient'])))
        except json.decoder.JSONDecodeError as err:
            logger.error(err)
            ws.send("Error while parsing data from json")
        except:
            logger.error("Error while processing data")
            ws.send("Error")


if __name__ == "__main__":
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    port = int(os.environ.get('PORT', 5000))
    server = pywsgi.WSGIServer(('', port), app, handler_class=WebSocketHandler)
    server.serve_forever()
