import requests
import logging


class FederatedTrainerConnector:
    def __init__(self, config):
        self.config = config
        self.federated_trainer_host = config['FEDERATED_TRAINER_HOST']

    def send_model_order(self, data):
        logging.info("Send order model")
        server_register_url = self.federated_trainer_host + "/model"
        response = requests.post(server_register_url, json=data)
        response.raise_for_status()

    def send_transformed_prediction(self, prediction):
        server_register_url = self.federated_trainer_host + "/prediction"
        logging.info("Send prediction")
        response = requests.post(server_register_url, json=prediction.get_data()).raise_for_status()
        return response.json()

    def send_decrypted_MSEs(self, MSE, partial_MSEs, public_key):
        server_register_url = self.federated_trainer_host + "/contributions"
        logging.info("Send MSEs for calculating contributions")
        response = requests.post(server_register_url,
                                 json={"MSE": MSE, "partialMSEs": partial_MSEs, "public_key": public_key}
                                 )
        return response.json()  # TODO: SHOW RESULT IN SCREEN (IMPROVENT AND CONTRIBUTIONS)
