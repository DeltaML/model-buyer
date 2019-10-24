import logging
from commons.web3.delta_contracts import ModelBuyerContract
from commons.web3.web3_service import Web3Service

from model_buyer.utils.singleton import Singleton


class ContractService(metaclass=Singleton):

    def __init__(self):
        self.w3_service = None
        self.default_contract_address = None
        self.contract_address = None

    def init(self, config):
        self.w3_service = Web3Service(config["ETH_URL"])
        self.default_contract_address = config["CONTRACT_ADDRESS"]
        self.contract_address = self.default_contract_address

    def set_contract_address(self, address):
        self.contract_address = address

    def get_contract_data(self):
        return {'address': self.contract_address}

    def build_contract_api(self, account):
        """

        :param account:
        :return:
        """
        return ModelBuyerContract(contract=self.w3_service.build_contract(address=self.contract_address),
                                  address=account)

    def pay_for_model(self, model_buyer_account, model_id, payment_requirements):
        logging.info("pay_for_model init {} {} ".format(model_buyer_account, model_id))
        pay = self.w3_service.transform_to_wei(value=payment_requirements['value'], currency=payment_requirements['unit'])
        contract = self.build_contract_api(model_buyer_account)
        contract.set_model_buyer(model_buyer_account)
        contract.pay_for_model(model_id=model_id, pay=pay)
        logging.info("pay_for_model finish")

    def finish_model_training(self, model_id, model_buyer_account):
        """
        Call contract function
        :param model_id:
        :param model_buyer_account:
        :return:
        """
        contract = self.build_contract_api(model_buyer_account)
        contract.finish_model_training(model_id)
        contract.generate_training_payments(model_id)
