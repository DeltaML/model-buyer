import logging
import time
import uuid
from datetime import datetime
from enum import Enum

import numpy as np
import sqlalchemy.types as types
from commons.model.model_service import ModelFactory
from flask import json
from sqlalchemy import Column, String, Sequence, JSON, Float, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from model_buyer.models.user import User
from model_buyer.services.data_base import DbEntity


class BuyerModelStatus(Enum):
    INITIATED = 1
    IN_PROGRESS = 2
    FINISHED = 3
    ERROR = 4


class ModelColumn(types.UserDefinedType):

    def get_col_spec(self, **kw):
        return "ModelColumn"

    def bind_processor(self, dialect):
        def process(value):
            x = value.X.tolist() if value.X is not None else None
            y = value.y.tolist() if value.y is not None else None
            weights = value.weights if type(value.weights) == list else value.weights.tolist()
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
            model = ModelFactory.get_model(model_type)(X=x, y=y, weights=weights)
            return model

        return process


class Model(DbEntity):
    __tablename__ = 'models'
    id = Column(String(100), Sequence('buyer_model_id_seq'), primary_key=True)
    model_type = Column(String(50))
    requirements = Column(JSON)
    model = Column(ModelColumn())
    request_data = Column(JSON)
    mse = Column(Float)
    initial_mse = Column(Float)
    partial_MSEs = Column(JSON)
    diffs = Column(JSON)
    partial_diffs = Column(JSON)
    status = Column(String(50), default=BuyerModelStatus.INITIATED.name)
    improvement = Column(Float)
    cost = Column(Float)
    name = Column(String(100))
    contributions = Column(JSON)
    iterations = Column(Integer)
    mse_history = Column(JSON)
    creation_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="models")
    User.models = relationship("Model", back_populates="user")

    def __init__(self, model_type, name="default", requirements=None):
        self.id = str(uuid.uuid1())
        self.model_type = model_type
        # TODO: revisar esto
        self.model = ModelFactory.get_model(model_type)(requirements=requirements)
        self.model.type = model_type
        self.status = BuyerModelStatus.INITIATED.name
        self.name = name
        self.iterations = 0
        self.improvement = 0.0
        self.mse = 0.0
        self.cost = 0.0
        self.mse_history = []
        self.diffs = []
        self.partial_diffs = {}

    def set_weights(self, weights):
        if type(weights) == list:
            weights = np.asarray(weights)
        self.model.set_weights(weights)

    def get_weights(self):
        weights = self.model.weights
        return np.asarray(weights) if type(weights) == list else weights

    def get_weights_as_list(self):
        return self.model.weights.tolist()

    def predict(self, x, y):
        x_array = np.asarray(x)
        y_array = np.asarray(y)
        prediction = self.model.predict(x, y)
        self.mse = prediction.mse
        return prediction

    @classmethod
    def get(cls, model_id=None):
        filters = {'id': model_id} if model_id else None
        return DbEntity.find(Model, filters)

    def update(self):
        filters = {'id': self.id}
        update_data = {Model.model: self.model, Model.status: self.status, Model.iterations: self.iterations,
                       Model.improvement: self.improvement, Model.name: self.name, Model.cost: self.cost,
                       Model.mse_history: self.mse_history, Model.initial_mse: self.initial_mse,
                       Model.contributions: self.contributions,
                       Model.updated_date: self.updated_date,
                       Model.partial_MSEs: self.partial_MSEs,
                       Model.mse: self.mse,
                       Model.diffs: self.diffs,
                       Model.partial_diffs: self.partial_diffs}
        super(Model, self).update(Model, filters, update_data)

    def add_mse(self, mse):
        self.mse = mse
        self.mse_history.append(dict(time=str(time.time()), mse=mse))

    def set_request_data(self, value):
        self.request_data = value.get()
