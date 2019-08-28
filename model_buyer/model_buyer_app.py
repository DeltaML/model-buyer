import logging
import os
import random
from logging.config import dictConfig

from flask import Flask, request, jsonify, send_from_directory, flash, redirect
from werkzeug.utils import secure_filename
from flask_cors import CORS

from commons.data.data_loader import DataLoader
from commons.encryption.encryption_service import EncryptionService
from model_buyer.services.data_base import Database
from model_buyer.services.model_buyer_service import ModelBuyerService
from model_buyer.resources import api
from model_buyer.config.logging_config import DEV_LOGGING_CONFIG, PROD_LOGGING_CONFIG



def create_app():
    # create and configure the app
    flask_app = Flask(__name__)
    if 'ENV_PROD' in os.environ and os.environ['ENV_PROD']:
        flask_app.config.from_pyfile("config/prod/app_config.py")
        dictConfig(PROD_LOGGING_CONFIG)
    else:
        dictConfig(DEV_LOGGING_CONFIG)
        flask_app.config.from_pyfile("config/dev/app_config.py")
    # ensure the instance folder exists
    try:
        os.makedirs(flask_app.instance_path)
    except OSError:
        pass

    return flask_app


app = create_app()
api.init_app(app)

CORS(app)
logging.info("Model Buyer is running")

encryption_service = EncryptionService(is_active=app.config["ACTIVE_ENCRYPTION"])
public_key, private_key = encryption_service.generate_key_pair(app.config["KEY_LENGTH"])
encryption_service.set_public_key(public_key.n)
data_base = Database(app.config)
data_loader = DataLoader(app.config['DATA_SETS_DIR'])
model_buyer_service = ModelBuyerService()
model_buyer_service.init(encryption_service, data_loader, app.config)


@app.route('/transform', methods=['POST'])
def transform_prediction():
    logging.info("transform prediction from data owner")
    model_buyer_service.transform_prediction(request.get_json())
    return jsonify(200), 200


@app.route('/file', methods=['POST'])
def load_data_set():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    filename = secure_filename(file.filename)
    model_buyer_service.load_data_set(file, filename)
    return jsonify(200)


@app.route('/ping', methods=['GET'])
def ping():
    response = {
        "values": [1, 2, 3],
        "MSE": random.randint(1, 2)
    }
    return jsonify(response)
