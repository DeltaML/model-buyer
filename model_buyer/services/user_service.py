from model_buyer.exceptions.exceptions import LoginFailureException
from model_buyer.models.user import User
from model_buyer.services.user_login_service import UserLoginService
from model_buyer.utils.mocks import mock_models


class UserService:

    @staticmethod
    def create(user_data):
        user = User(name=user_data["name"], email=user_data["email"], token=user_data["token"])
        user.save()

    @staticmethod
    def get_all():
        return User.find_all()

    @staticmethod
    def get(user_id):

        user = User.find_one_by_id(user_id)
        return user

    @staticmethod
    def update(user_id, user_data):
        return User().partial_update(user_id, user_data)

    def delete(self, user_id):
        user = self.get(user_id)
        user.delete()

    @staticmethod
    def login(data):
        token = data["token"]
        user_info = UserLoginService.get_user_info(token)

        if not UserLoginService.validate(user_info):
            raise LoginFailureException()

        user_external_id = user_info['sub']
        user = User.find_one_by_external_id(user_external_id)
        if user:
            return user

        if not user_info["email_verified"]:
            raise LoginFailureException()

        user = User(external_id=user_external_id,
                    name=user_info["name"],
                    email=user_info["email"],
                    token=token)
        user.save()
        return user
