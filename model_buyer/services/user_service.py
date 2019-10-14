import logging

from commons.utils.singleton import Singleton

from model_buyer.exceptions.exceptions import LoginFailureException, UserNotFoundException
from model_buyer.models.user import User
from model_buyer.services.user_login_service import UserLoginService


class UserService(metaclass=Singleton):

    def __init__(self):
        self.config = None
        self.model_buyer_service = None

    def init(self, config, model_buyer_service):
        self.config = config
        self.model_buyer_service = model_buyer_service

    @staticmethod
    def create(user_data):
        user = User(name=user_data["name"], email=user_data["email"], token=user_data["token"])
        user.save()
        return user

    @staticmethod
    def get_all():
        return User.find_all()

    @staticmethod
    def get(user_id):
        user = User.find_one_by_id(user_id)
        if not user:
            raise UserNotFoundException(user_id)
        return user

    def update(self, user_id, user_data):
        user = self.get(user_id)
        return user.partial_update(user_id, user_data)

    def delete(self, user_id):
        user = self.get(user_id)
        user.delete()

    def login(self, data):
        token = data["token"]
        user_info = UserLoginService.get_user_info(token)

        if not UserLoginService.validate(user_info):
            raise LoginFailureException()

        # Validate external email
        if not user_info["email_verified"]:
            raise LoginFailureException()

        user_external_id = user_info['sub']
        user = User.find_one_by_external_id(user_external_id)
        if not user:
            user = self.create_user(token, user_external_id, user_info)
        return user

    @staticmethod
    def create_user(token, user_external_id, user_info):
        user = User(external_id=user_external_id,
                    name=user_info["name"],
                    email=user_info["email"],
                    token=token)
        user.save()
        return user

    def add_address(self, user_id, user_data):
        """
        Register a user into delta ml context
        :param user_data:
        :param user_id:
        :return:
        """
        user = self.get(user_id)
        return user.update_address(user_id, user_data["address"])

    @staticmethod
    def get_by_delta_id(delta_id):
        user = User.find_one_by_id(delta_id)
        if not user:
            raise UserNotFoundException(delta_id)
        return user
