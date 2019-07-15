from sqlalchemy import Column, String, Integer
from model_buyer.services.data_base import DbEntity


class User(DbEntity):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(100), unique=True)
    name = Column(String(100))
    token = Column(String(100))

    @classmethod
    def get(cls, user_id=None):
        filters = {'id': user_id} if user_id else None
        return DbEntity.query(User, filters)

    def partial_update(self, user_id, user_data):
        filters = {"id": user_id}
        update_data = {'email': user_data["email"], 'token': user_data["token"]}
        self.update(User, filters=filters, update_data=update_data)
        return self.get(user_id)
