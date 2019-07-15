from model_buyer.models.user import User
from model_buyer.utils.singleton import Singleton


class UserService(metaclass=Singleton):

    @staticmethod
    def create(user_data):
        user = User(name=user_data["name"], email=user_data["email"], token=user_data["token"])
        user.save()

    @staticmethod
    def get_all():
        return User.get()

    @staticmethod
    def get(user_id):
        return User.get(user_id)

    @staticmethod
    def update(user_id, user_data):
        return User().partial_update(user_id, user_data)

    def delete(self, user_id):
        user = self.get(user_id)
        user.delete()

