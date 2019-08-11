import logging
import os
import uuid
from threading import Thread

import numpy as np

from model_buyer.exceptions.exceptions import ModelNotFoundException
from model_buyer.models.model import Model, BuyerModelStatus
from model_buyer.services.federated_trainer_connector import FederatedTrainerConnector
from model_buyer.utils.singleton import Singleton


class ModelBuyerService(metaclass=Singleton):

    def __init__(self):
        self.id = str(uuid.uuid1())
        self.encryption_service = None
        self.data_loader = None
        self.config = None
        self.predictions = []
        self.federated_trainer_connector = None

    def init(self, encryption_service, data_loader, config):
        self.encryption_service = encryption_service
        self.data_loader = data_loader
        self.config = config
        self.predictions = []
        if config:
            self.federated_trainer_connector = FederatedTrainerConnector(config)

    @staticmethod
    def get_all():
        return Model.get()

    def delete_model(self, model_id):
        self.get(model_id).delete()

    def make_new_order_model(self, model_type, requirements, user_id):
        """

        :param model_type:
        :param requirements:
        :param file:
        :param user_id:
        :return:
        """

        ordered_model = Model(model_type=model_type, requirements=requirements)
        ordered_model.user_id = user_id
        ordered_model.request_data = dict(requirements=requirements,
                                          status=ordered_model.status,
                                          model_id=ordered_model.id,
                                          model_type=model_type,
                                          model_buyer_id=self.id,
                                          weights=ordered_model.model.weights.tolist())
        ordered_model.save()

        self.federated_trainer_connector.send_model_order(ordered_model.request_data)
        return {"requirements": requirements,
                "model": {"id": ordered_model.id,
                          "status": ordered_model.status,
                          "type": ordered_model.model_type,
                          "weights": ordered_model.model.weights.tolist()
                          }
                }

    def finish_model(self, model_id, data):
        buyer_model = self._update_model(model_id, data, BuyerModelStatus.FINISHED.name)
        logging.info("Model status: {} weights {}".format(buyer_model.status, buyer_model.model["weights"]))
        self.federated_trainer_connector.send_decrypted_MSEs(self._build_response_with_MSEs(model_id, data))

    def _decrypt_mse(self, encrypted_mse):
        return self.encryption_service.get_deserialized_desencrypted_value(encrypted_mse) if self.config[
            "ACTIVE_ENCRYPTION"] else encrypted_mse

    def _build_response_with_MSEs(self, model_id, data):
        decrypted_MSE = self._decrypt_mse(data["mse"])
        decrypted_partial_MSEs = dict(
            [(data_owner, self._decrypt_mse(partial_mse)) for data_owner, partial_mse in data["partial_MSEs"].items()])
        public_key = self.encryption_service.get_public_key()
        return model_id, decrypted_MSE, decrypted_partial_MSEs, public_key

    def update_model(self, model_id, data):
        """

        :param model_id:
        :param data:
        :return:
        """
        return self._update_model(model_id, data, BuyerModelStatus.IN_PROGRESS.name)

    def _update_model(self, model_id, data, status):
        weights = self.encryption_service.decrypt_and_deserizalize_collection(
            self.encryption_service.get_private_key(),
            data["model"]["weights"]
        ) if self.config["ACTIVE_ENCRYPTION"] else data["model"]["weights"]
        logging.info("Updating model from fed. aggr. Weights: {}".format(weights))
        ordered_model = self.get(model_id)
        model = ordered_model.model
        model.set_weights(np.asarray(weights))
        ordered_model.model = model
        ordered_model.status = status
        # TODO: TEMPORARY SOLUTION, ADD ANOTHER ENDPOINT FOR INITIAL MSE REQUEST
        if data['first_update']:
            ordered_model.initial_mse = self._decrypt_mse(data["metrics"]["initial_mse"])
            logging.info("INITIAL MSE: {}".format(ordered_model.initial_mse))
        else:
            initial_mse = ordered_model.initial_mse
            model_id, decrypted_MSE, decrypted_partial_MSEs, public_key = self._build_response_with_MSEs(model_id, data[
                "metrics"])
            ordered_model.mse = decrypted_MSE
            ordered_model.partial_MSEs = decrypted_partial_MSEs
            progress_update = self.federated_trainer_connector.send_decrypted_MSEs(model_id, initial_mse, decrypted_MSE,
                                                                                   decrypted_partial_MSEs, public_key)
            logging.info("CONTRIBUTIONS: {}".format(progress_update))
            ordered_model.contributions = progress_update[2]
            ordered_model.improvement = progress_update[1]
            ordered_model.iterations += 1

        ordered_model.save()
        logging.info("Updating saved model. Weights: {}".format(model.weights))
        ordered_model.update_model(model, model_id)
        return ordered_model

    def get(self, model_id):
        model = Model.get(model_id)
        if not model:
            raise ModelNotFoundException
        return model

    def get_model(self, model_id):
        model = self.get(model_id)
        if not model:
            raise ModelNotFoundException
        return {
            "model": {"id": model.id, "weights": model.model.weights.tolist(), "type": model.model_type,
                      "status": model.status},
            "metrics": {"mse": model.mse, "partial_MSEs": model.partial_MSEs, "initial_mse": model.initial_mse}
        }

    def make_prediction(self, data):
        """

        :param data:
        :return:
        """
        prediction_id = data["id"]
        model = self.get(prediction_id)
        if not model:
            raise ModelNotFoundException(prediction_id)
        # TODO: Check this x_test
        x_test, y_test = self.data_loader.get_sub_set()
        logging.info(model.model)
        prediction = model.predict(x_test, y_test)
        prediction.model = model
        self.predictions.append(prediction)
        return prediction

    def get_prediction(self, prediction_id):
        return next(filter(lambda x: x.id == prediction_id, self.predictions), None)

    def transform_prediction(self, prediction_data):
        """
       {'model_id': self.model_id,
        'prediction_id': self.id,
        'encrypted_prediction': Data Owner encrypted prediction,
        'public_key': Data Owner PK}
       :param prediction_data:
       :return:
       """
        decrypted_prediction = self.encryption_service.decrypt_collection(prediction_data["encrypted_prediction"])
        encrypted_to_data_owner = self.encryption_service.encrypt_collection(decrypted_prediction,
                                                                             public_key=prediction_data["public_key"])
        prediction_transformed = {
            "encrypted_prediction": encrypted_to_data_owner,
            "model_id": prediction_data["model_id"],
            "prediction_id": prediction_data["prediction_id"]
        }
        Thread(target=self.federated_trainer_connector.send_transformed_prediction,
               args=prediction_transformed).start()

    def load_data_set(self, file, filename):
        logging.info(file)
        file.save(os.path.join(self.config.get("DATA_SETS_DIR"), filename))
        file.close()
