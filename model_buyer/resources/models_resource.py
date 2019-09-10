import logging

from flask import request
from flask_restplus import Resource, Namespace, fields

from model_buyer.services.model_buyer_service import ModelBuyerService

api = Namespace('models', description='Model related operations')

features = api.model(name='Features', model={
    'list': fields.List(fields.String, required=True, description='The model type'),
    'range': fields.List(fields.Integer, required=True, description='The model type'),
    'pre_processing': fields.List(fields.Raw, required=False, description='The model type'),
    'desc': fields.Raw(required=False, description='The model type')
})

target = api.model(name='Target', model={
    'range': fields.List(fields.Integer, required=True, description='The model type'),
    'desc': fields.List(fields.String, required=True, description='The model type')
})

data_requirements = api.model(name='Data Requirements', model={
    'features': fields.Nested(features, required=True, description='The model type'),
    'target': fields.Nested(target, required=True, description='The model type'),
})

requirements = api.model(name='Requirements', model={
    'model_type': fields.String(required=True, description='The model type'),
    'testing_file_name': fields.String(required=True, description='The name of the file to test'),
    'data_requirements': fields.Nested(data_requirements, required=True, description='Data requirements')
})

partial_MSE = api.model(name='Partial MSE Metrics', model={
    'data_owner': fields.String(required=True,
                                description='The data owner removed from the training of this model to obtain the partial MSE'),
    'partial_MSE': fields.Float(required=True, description='The MSE of model updated without the data owner'),
})


mse_history = api.model(name='MSE History', model={
    'time': fields.String(required=True,
                                description='The data owner removed from the training of this model to obtain the partial MSE'),
    'mse': fields.Float(required=True, description='The MSE of model updated without the data owner'),
})

metrics = api.model(name='Metrics', model={
    'initial_mse': fields.Float(required=True, description='The Initial MSE of the model'),
    'mse': fields.Float(required=True, description='The MSE of the model'),
    'partial_MSEs': fields.List(fields.Nested(partial_MSE), required=True, description='The MSE of models updated without one local trainer each'),
    'iterations': fields.Integer(required=True, description='Number of iterations'),
    'improvement': fields.Fixed(required=True, decimals=5, description='The model improvement'),
    'mse_history': fields.List(fields.Nested(mse_history), required=True, description='The model mse history list')
})

model = api.model(name='Model', model={
    'id': fields.String(required=True, description='The model identifier'),
    'status': fields.String(required=True, description='The model status'),
    'type': fields.String(required=True, description='The model type'),
    'weights': fields.List(fields.Raw, required=True, description='The model weights'),
    'creation_date': fields.String(description='The model creation date'),
    'updated_date': fields.String(description='The model updated date'),
    'user_id': fields.String(required=True, description='The model user_id'),
    'name': fields.String(required=True, description='The model name')

})
updated_model = api.model(name='Updated Model', model={
    'metrics': fields.Nested(metrics, required=True, description='The model requirements'),
    'model': fields.Nested(model, required=True, description='The model')
})

ordered_model = api.model(name='Ordered Model', model={
    'model': fields.Nested(model, required=True, description='The model')
})


model_request = api.model(name='Ordered Model Request', model={
    'data_requirements': fields.Nested(requirements, required=True, description='The model requirements'),
    'model_type': fields.String(required=True, description='The model type'),
    'initial_model': fields.Raw(required=False, description='The model type')
})

reduced_ordered_model = api.model(name='Models', model={
    'id': fields.String(required=True, description='The model identifier'),
    'status': fields.String(required=True, description='The model status'),
    'name': fields.String(required=True, description='The model name'),
    'improvement': fields.Fixed(required=True, decimals=5, description='The model improvement'),
    'cost': fields.Float(required=True, description='The model cost'),
    'iterations': fields.Integer(required=True, description='Number of iterations'),
    'mse': fields.Float(required=True, description='The model mse'),
    'user_id': fields.String(required=True, description='The model user_id'),
    'creation_date': fields.String(description='The model creation date')
})


@api.route('', endpoint='model_resources_ep')
class ModelResources(Resource):

    @api.marshal_with(ordered_model, code=201)
    @api.doc('Create order model')
    def post(self):
        logging.info("New order model")
        model_type = request.get_json()["model_type"]
        name = request.get_json()["name"]
        user_id = request.get_json()["user_id"]
        data_requirements = request.get_json()["data_requirements"]
        payment_requirements = request.form.get("payment_requirements")
        return ModelBuyerService().make_new_order_model(model_type, name, data_requirements, user_id), 200

    @api.marshal_list_with(reduced_ordered_model)
    def get(self):
        return ModelBuyerService().get_all(), 200


@api.route('/<model_id>', endpoint='model_ep')
@api.response(404, 'Model not found')
@api.param('model_id', 'The model identifier')
class ModelResource(Resource):

    @api.doc('put_model')
    def put(self, model_id):
        data = request.get_json()
        logging.info("Received final update from fed. aggr. {}".format(data))
        ModelBuyerService().finish_model(model_id)
        return 200

    @api.doc('patch_model')
    def patch(self, model_id):
        data = request.get_json()
        logging.info("Received update from fed. aggr. {}".format(data))
        return ModelBuyerService().update_model(model_id, data)

    @api.doc('get_model')
    @api.marshal_with(updated_model)
    def get(self, model_id):
        return ModelBuyerService().get_model(model_id), 200

    @api.doc('delete_model')
    def delete(self, model_id):
        return ModelBuyerService().delete_model(model_id), 200
