from commons.web3.delta_contracts import ModelBuyerContract


class ContractService:

    def __init__(self, w3_service, contract_address):
        self.w3_service = w3_service
        self.contract_address = contract_address

    def build_contract_api(self, account):
        """

        :param account:
        :return:
        """
        return ModelBuyerContract(contract=self.w3_service.build_contract(address=self.contract_address),
                                  address=account)

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
