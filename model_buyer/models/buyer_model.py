import uuid
from enum import Enum

import numpy as np
import sqlalchemy.types as types
from flask import json
from sqlalchemy import Column, String, Sequence, JSON, Float

from commons.model.model_service import ModelFactory
from model_buyer.services.data_base import DbEntity


class BuyerModelStatus(Enum):
    INITIATED = 1
    IN_PROGRESS = 2
    FINISHED = 3


class ModelColumn(types.UserDefinedType):

    def get_col_spec(self, **kw):
        return "ModelColumn"

    def bind_processor(self, dialect):
        def process(value):
            x = value.X.tolist() if value.X is not None else None
            y = value.y.tolist() if value.y is not None else None
            weights = value.weights.tolist() if value.y is not None else None
            model_type = value.type
            return json.dumps({
                'x': x, 'y': y, 'weights': weights, 'type': model_type
            })
        return process

    def result_processor(self, dialect, coltype):
        def process(value):
            model_data = json.loads(value)
            x = np.asarray(model_data['x'])
            y = np.asarray(model_data['y'])
            model_type = model_data['type']
            weights = np.asarray(model_data['weights'])
            model = ModelFactory.get_model(model_type)(x, y)
            model.set_weights(weights)
            return model
        return process


class BuyerModel(DbEntity):
    __tablename__ = 'buyer_model'
    id = Column(String(100), Sequence('buyer_model_id_seq'), primary_key=True)
    model_type = Column(String(50))
    requirements = Column(JSON)
    model = Column(ModelColumn())
    request_data = Column(JSON)
    mse = Column(Float)
    status = Column(String(50), default=BuyerModelStatus.INITIATED.name)

    def __init__(self, model_type, data):
        self.id = str(uuid.uuid1())
        self.model_type = model_type
        self.model = ModelFactory.get_model(model_type)(data)
        self.model.type = model_type
        self.status = BuyerModelStatus.INITIATED.name

    def set_weights(self, weights):
        self.model.set_weights(weights)

    def predict(self, x, y):
        x_array = np.asarray(x)
        y_array = np.asarray(y)
        prediction = self.model.predict(x, y)
        self.mse = prediction.mse
        return prediction

    @classmethod
    def get(cls, model_id=None):
        filters = {'id': model_id} if model_id else None
        return DbEntity.find(BuyerModel, filters)
