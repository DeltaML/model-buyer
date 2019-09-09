import logging
import os
import uuid
import numpy as np
from threading import Thread

from model_buyer.exceptions.exceptions import ModelNotFoundException
from model_buyer.models.model import Model, BuyerModelStatus
from model_buyer.services.entities.model_response import ModelResponse, NewModelResponse, NewModelRequestData
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

    def _decrypt_number(self, number):
        if self.config["ACTIVE_ENCRYPTION"]:
            return self.encryption_service.get_deserialized_desencrypted_value(number)
        else:
            return number

    def _decrypt_collection(self, collection):
        private_key = self.encryption_service.get_private_key()
        if self.encryption_service.is_active:
            collection = self.encryption_service.decrypt_and_deserizalize_collection(private_key, collection)
        return np.asarray(collection)

    def _only_serialize_collection(self, collection):
        if self.encryption_service.is_active:
            return self.encryption_service.get_serialized_collection(collection)
        else:
            return collection

    def _only_serialize_encrypted_collection(self, collection):
        if self.encryption_service.is_active:
            return self.encryption_service.get_serialized_encrypted_collection(collection)
        else:
            return collection

    def make_new_order_model(self, model_type, name, requirements, user_id):
        """
        :param model_type:
        :param name:
        :param requirements:
        :param user_id:
        :return:
        """
        ordered_model = Model(model_type=model_type, name=name, requirements=requirements)
        # TODO agrojas: validate if user exists
        ordered_model.user_id = user_id
        # TODO agrojas: extract to commons
        ordered_model.set_request_data(NewModelRequestData(ordered_model, requirements, user_id, model_type, self.config['STEP'], self.encryption_service.get_public_key()))
        ordered_model.save()
        self.federated_trainer_connector.send_model_order(self._get_request_data(ordered_model))
        return NewModelResponse(ordered_model)

    def _get_request_data(self, ordered_model):
        """
        TODO agrojas review this
        :param ordered_model:
        :return:
        """
        request_data = ordered_model.request_data
        request_data["weights"] = self._only_serialize_encrypted_collection(request_data["weights"])
        return request_data

    def finish_model(self, model_id):
        ordered_model = self.get(model_id)
        ordered_model.status = BuyerModelStatus.FINISHED.name
        logging.info("Model status: {} weights {}".format(ordered_model.status, ordered_model.model.weights))
        ordered_model.update()

    def _build_response_with_MSEs(self, model_id, data):
        logging.info("_build_response_with_MSEs")
        logging.info(data)
        decrypted_MSE = self._decrypt_number(data["mse"])
        decrypted_partial_MSEs = {}
        for data_owner, partial_mse in data["partial_MSEs"].items():
            decrypted_partial_MSEs[data_owner] = self._decrypt_number(partial_mse)
        public_key = self.encryption_service.get_public_key()
        return model_id, decrypted_MSE, decrypted_partial_MSEs, public_key

    def update_model(self, model_id, data):
        """
        _decrypt_mse
        :param model_id:
        :param data:
        :return:
        """
        ordered_model, diffs = self._update_model(model_id, data, BuyerModelStatus.IN_PROGRESS.name)
        return NewModelResponse(ordered_model).get_update_response(diffs)

    def _update_model(self, model_id, data, status):
        ordered_model = self.get(model_id)
        ordered_model.status = status
        diffs = data['metrics']['diffs']
        partial_diffs = data['metrics']['partial_diffs']
        weights = self._decrypt_collection(data["model"]["weights"])
        logging.info("Updating model from fed. aggr. Weights: {}".format(weights))
        np.around(weights, decimals=3, out=weights)
        if self.encryption_service.is_active:
            weights = self.encryption_service.get_serialized_encrypted_collection(weights)
            diffs = [self.encryption_service.decrypt_and_deserizalize_collection(self.encryption_service.get_private_key(), diff) for diff in diffs]
            for trainer in partial_diffs:
                partial_diffs[trainer] = [self.encryption_service.decrypt_and_deserizalize_collection(self.encryption_service.get_private_key(), diff) for diff in partial_diffs[trainer]]

        mse = np.mean(np.asarray(diffs) ** 2)
        partial_MSEs = {}
        for trainer in partial_diffs:
            partial_MSEs[trainer] = np.mean(np.asarray(partial_diffs[trainer]) ** 2)
        if data['first_update']:
            ordered_model.initial_mse = mse
            logging.info("INITIAL MSE: {}".format(ordered_model.initial_mse))
        ordered_model.add_mse(mse)
        ordered_model.set_weights(weights)
        ordered_model.partial_MSEs = partial_MSEs
        progress_update = self.federated_trainer_connector.send_decrypted_MSEs(
            model_id, ordered_model.initial_mse, mse, partial_MSEs, self.encryption_service.get_public_key()
        )
        logging.info("CONTRIBUTIONS: {}".format(progress_update))
        ordered_model.contributions = progress_update[2]
        ordered_model.improvement = progress_update[1]
        ordered_model.iterations += 1
        logging.info("Updating saved model. Weights: {}".format(ordered_model.get_weights()))
        ordered_model.update()
        return ordered_model, diffs

    def get(self, model_id):
        model = Model.get(model_id)
        if not model:
            raise ModelNotFoundException
        return model

    def get_model(self, model_id):
        model = self.get(model_id)
        if not model:
            raise ModelNotFoundException
        return ModelResponse(model)

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
