import logging
import os
from logging.config import dictConfig

from commons.web3.web3_service import Web3Service
from flask import Flask
from flask_cors import CORS

from commons.data.data_loader import DataLoader
from commons.encryption.encryption_service import EncryptionService
from model_buyer.services.data_base import Database
from model_buyer.services.model_buyer_service import ModelBuyerService
from model_buyer.resources import api
from model_buyer.config.logging_config import DEV_LOGGING_CONFIG, PROD_LOGGING_CONFIG
from model_buyer.services.user_service import UserService


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

encryption_service = EncryptionService(is_active=app.config["ACTIVE_ENCRYPTION"])
public_key, private_key = encryption_service.generate_key_pair(app.config["KEY_LENGTH"])
encryption_service.set_public_key(public_key.n)
data_base = Database(app.config)
data_loader = DataLoader(app.config['DATA_SETS_DIR'])
w3_service = Web3Service(app.config["ETH_URL"])

model_buyer_service = ModelBuyerService()
model_buyer_service.init(encryption_service=encryption_service,
                         data_loader=data_loader,
                         w3_service=w3_service,
                         config=app.config)

user_service = UserService()
user_service.init(app.config, model_buyer_service)

logging.info("Model Buyer is running")









