from sqlalchemy import Column, String, Integer
from model_buyer.services.data_base import DbEntity


import uuid


class User(DbEntity):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    delta_id = Column(String(100))
    external_id = Column(String(500), unique=True)
    email = Column(String(100), unique=True)
    name = Column(String(100))
    token = Column(String(100))
    address = Column(String(100))

    def __init__(self,  email, name, token, external_id=None, address=None):
        self.delta_id = str(uuid.uuid1())

        self.email = email
        self.name = name
        self.token = token
        self.external_id = external_id
        self.address = address

    @classmethod
    def exists_external_id(cls, external_id):
        filters = {'external_id': external_id}
        return DbEntity.exists(User, filters)

    @classmethod
    def find_all(cls):
        return DbEntity.find(User)

    @classmethod
    def find_one_by_id(cls, user_id):
        filters = {'id': user_id}
        return DbEntity.find(User, filters)

    @classmethod
    def find_one_by_external_id(cls, external_id):
        filters = {'external_id': external_id}
        return DbEntity.find(User, filters)

    @classmethod
    def find_one_by_email(cls, user_email):
        filters = {'email': user_email}
        return DbEntity.find(User, filters)

    def partial_update(self, user_id, user_data):
        filters = {"id": user_id}
        update_data = {'email': user_data["email"], 'token': user_data["token"], 'address': user_data["address"]}
        self.update(User, filters=filters, update_data=update_data)
        return self.find_one_by_id(user_id)

    def update_address(self, user_id, address):
        filters = {"id": user_id}
        update_data = {'address': address}
        self.update(User, filters=filters, update_data=update_data)
        return self.find_one_by_id(user_id)
