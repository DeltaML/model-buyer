import logging
import os
import uuid
from threading import Thread

import numpy as np

from model_buyer.exceptions.exceptions import ModelNotFoundException
from model_buyer.models.model import Model, BuyerModelStatus
from model_buyer.services.contract_service import ContractService
from model_buyer.services.entities.encrypter_wrapper import EncrypterWrapper
from model_buyer.services.entities.model_response import ModelResponse, NewModelResponse, NewModelRequestData
from model_buyer.services.federated_aggregator_connector import FederatedAggregatorConnector
from model_buyer.services.metrics_handler import MetricsHandler
from model_buyer.services.user_service import UserService
from model_buyer.utils.singleton import Singleton


class ModelBuyerService(metaclass=Singleton):

    def __init__(self):
        self.id = str(uuid.uuid1())
        self.encryption_service = None
        self.encrypted_wrapper = None
        self.contract_service = None
        self.data_loader = None
        self.config = None
        self.predictions = []
        self.federated_aggregator_connector = None

    def init(self, encryption_service, data_loader, contract_service, config):
        self.encryption_service = encryption_service
        self.encrypted_wrapper = EncrypterWrapper(self.encryption_service)
        self.data_loader = data_loader
        self.config = config
        self.predictions = []
        self.federated_aggregator_connector = FederatedAggregatorConnector(config)
        self.contract_service = contract_service

    @staticmethod
    def get_all():
        return Model.get()

    def delete_model(self, model_id):
        self.get(model_id).delete()

    def make_new_order_model(self, model_type, name, requirements, user, payment_requirements):
        """
        :param model_type:
        :param name:
        :param requirements:
        :param user:
        :param payment_requirements:
        :return:
        """
        ordered_model = Model(model_type=model_type, name=name, requirements=requirements,
                              payments=payment_requirements)

        ordered_model.user_id = user.id
        ordered_model.set_request_data(
            NewModelRequestData(ordered_model, requirements, user, model_type, self.config['STEP'],
                                self.encryption_service.get_public_key()))
        ordered_model.save()
        self.federated_aggregator_connector.send_model_order(self._get_request_data(ordered_model))

        mock_pay_reqs = {'value': ModelBuyerService().config['PAY'], 'unit': ModelBuyerService().config['UNIT']}
        pay_reqs = payment_requirements["pay_for_model"] or mock_pay_reqs
        self.contract_service.pay_for_model(model_buyer_account=user.address,
                                            model_id=ordered_model.id,
                                            payment_requirements=pay_reqs)
        return NewModelResponse(ordered_model)

    def _get_request_data(self, ordered_model):
        """
        TODO agrojas review this
        :param ordered_model:
        :return:
        """
        request_data = ordered_model.request_data
        request_data["weights"] = self.encrypted_wrapper.only_serialize_encrypted_collection(request_data["weights"])
        return request_data

    def finish_model(self, model_id, data):
        """
        Completion of model training in the model buyer
        :param model_id:
        :param data:
        :return:
        """
        if data["model"]["status"] == "ERROR":
            self._finish_on_error(model_id)
            return
        logging.info("Finish model with status {}".format(BuyerModelStatus.FINISHED.name))

        ordered_model = self.get(model_id)
        ordered_model.set_weights(self._decrypt_model(ordered_model.get_weights()))
        ordered_model.status = BuyerModelStatus.FINISHED.name
        logging.info("Model status: {} ".format(ordered_model.status))
        ordered_model.update()
        self._call_finish_contract(model_id, ordered_model)

    def _call_finish_contract(self, model_id, ordered_model):
        logging.info("Call finish model training function on smart contract")
        user = UserService().get(ordered_model.user_id)
        self.contract_service.finish_model_training(model_id=model_id, model_buyer_account=user.address)

    def _decrypt_mse(self, encrypted_mse):
        return self.encryption_service.get_deserialized_desencrypted_value(encrypted_mse) if self.config[
            "ACTIVE_ENCRYPTION"] else encrypted_mse

    def _build_response_with_MSEs(self, model_id, data):
        logging.info("_build_response_with_MSEs")
        decrypted_MSE = self.encrypted_wrapper.decrypt_number(data["mse"])
        decrypted_partial_MSEs = {}
        for data_owner, partial_mse in data["partial_MSEs"].items():
            decrypted_partial_MSEs[data_owner] = self.encrypted_wrapper.decrypt_number(partial_mse)
        public_key = self.encryption_service.get_public_key()
        return model_id, decrypted_MSE, decrypted_partial_MSEs, public_key

    def update_metrics(self, model_id, data):
        from_fa_mse = data['mse']
        from_fa_partial_mses = data['partial_mses']
        noise = data['noise']
        ordered_model = self.get(model_id)
        diffs = ordered_model.diffs
        partial_diffs = ordered_model.partial_diffs
        metrics_handler = MetricsHandler(np.asarray(noise))
        p_mses = {key: np.asarray(diffs) for key, diffs in partial_diffs.items()}
        mse, _, partial_MSEs = metrics_handler.get_mses(np.asarray(diffs), p_mses)
        if mse != from_fa_mse:
            return False
        for data_owner in partial_MSEs:
            if partial_MSEs[data_owner] != from_fa_partial_mses[data_owner]:
                return False
        if data['first_update']:
            ordered_model.initial_mse = mse
            logging.info("INITIAL MSE: {}".format(ordered_model.initial_mse))
        ordered_model.add_mse(mse)
        ordered_model.partial_MSEs = partial_MSEs
        progress_update = self.federated_aggregator_connector.send_decrypted_MSEs(
            model_id, ordered_model.initial_mse, mse, partial_MSEs, self.encryption_service.get_public_key()
        )
        logging.info("CONTRIBUTIONS: {}".format(progress_update))
        ordered_model.contributions = progress_update['contributions']
        ordered_model.improvement = progress_update['improvement']
        ordered_model.update()
        return True

    def update_model(self, model_id, data):
        """
        :param model_id:
        :param data:
        :return:
        """
        ordered_model, diffs, partial_diffs = self._update_model(model_id, data, BuyerModelStatus.IN_PROGRESS.name)
        return NewModelResponse(ordered_model).get_update_response(diffs, partial_diffs)

    def _update_model(self, model_id, data, status):
        ordered_model = self.get(model_id)
        ordered_model.status = status
        diffs = data['metrics']['diffs']
        partial_diffs = data['metrics']['partial_diffs']
        weights = self.encrypted_wrapper.decrypt_collection(data["model"]["weights"])
        logging.info("Updating model from fed. aggr. ")
        np.around(weights, decimals=3, out=weights)
        #  TODO: Refactor
        if self.encryption_service.is_active:
            weights = self.encryption_service.get_serialized_encrypted_collection(weights)
            diffs = [
                self.encryption_service.decrypt_and_deserizalize_collection(self.encryption_service.get_private_key(),
                                                                            diff) for diff in diffs]
            for trainer in partial_diffs:
                partial_diffs[trainer] = [self.encryption_service.decrypt_and_deserizalize_collection(
                    self.encryption_service.get_private_key(), diff) for diff in partial_diffs[trainer]]

        ordered_model.diffs = diffs
        ordered_model.partial_diffs = partial_diffs
        ordered_model.set_weights(weights)
        ordered_model.iterations += 1
        logging.info("Updating saved model. Weights")
        ordered_model.update()
        return ordered_model, diffs, partial_diffs

    def get(self, model_id):
        model = Model.get(model_id=model_id)
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
        Thread(target=self.federated_aggregator_connector.send_transformed_prediction,
               args=prediction_transformed).start()

    def load_data_set(self, file, filename):
        logging.info(file)
        file.save(os.path.join(self.config.get("DATA_SETS_DIR"), filename))
        file.close()

    def _finish_on_error(self, model_id):
        logging.info("Finish model {} with status {}".format(model_id, BuyerModelStatus.ERROR.name))
        ordered_model = self.get(model_id)
        ordered_model.status = BuyerModelStatus.ERROR.name
        ordered_model.save()

    def _decrypt_model(self, weights):
        encrypted_model = self.encryption_service.get_deserialized_collection(weights) if self.config[
            "ACTIVE_ENCRYPTION"] else weights
        result = self.encryption_service.decrypt_collection(encrypted_model)
        return result
