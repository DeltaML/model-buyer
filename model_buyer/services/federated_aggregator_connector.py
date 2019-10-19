import logging

import requests


class FederatedAggregatorConnector:
    def __init__(self, config):
        self.config = config
        self.federated_aggregator_host = config['FEDERATED_AGGREGATOR_HOST']

    def send_model_order(self, data):
        logging.info("Send order model")
        url = self.federated_aggregator_host + "/model"
        logging.info("url: {} payload {}".format(url, data))
        response = requests.post(url, json=data)
        response.raise_for_status()
        logging.info("Response {}".format(response))

    def send_transformed_prediction(self, prediction):
        url = self.federated_aggregator_host + "/prediction"
        payload = prediction.get_data()
        logging.info("url: {} payload {}".format(url, payload))

        response = requests.post(url, json=payload)
        response.raise_for_status()
        logging.info("Response {}".format(response.json()))
        return response.json()

    def send_decrypted_MSEs(self, model_id, initial_mse, MSE, partial_MSEs, public_key):
        url = self.federated_aggregator_host + "/contributions"
        payload = {"model_id": model_id,
                   'initial_MSE': initial_mse,
                   "MSE": MSE,
                   "partial_MSEs": partial_MSEs,
                   "public_key": public_key
                   }
        logging.info("url: {} ".format(url))
        response = requests.post(url, json=payload)
        logging.info("response {}".format(response.json()))
        return response.json()  # TODO: SHOW RESULT IN SCREEN (IMPROVENT AND CONTRIBUTIONS)
