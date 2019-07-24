import logging
import json
from flask_restplus import Resource, Namespace, fields
from flask import request, flash, redirect
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

partial_MSE = api.model(name='Metrics', model={
    'data_owner': fields.String(required=True, description='The data owner removed from the training of this model to obtain the partial MSE'),
    'partial_MSE': fields.Float(required=True, description='The MSE of model updated without the data owner'),
})

metrics = api.model(name='Metrics', model={
    'mse': fields.Float(required=True, description='The MSE of the model'),
    'partial_MSEs': fields.List(fields.Nested(partial_MSE), required=True, description='The MSE of models updated without one local trainer each'),
})

model = api.model(name='Model', model={
    'id': fields.String(required=True, description='The model identifier'),
    'status': fields.String(required=True, description='The model status'),
    'type': fields.String(required=True, description='The model type'),
    'weights': fields.List(fields.Raw, required=True, description='The model weights')
})

ordered_model = api.model(name='Ordered Model', model={
    'requirements': fields.Nested(requirements, required=True, description='The model requirements'),
    'model': fields.Nested(model, required=True, description='The model')
})

updated_model = api.model(name='Ordered Model', model={
    'metrics': fields.Nested(metrics, required=True, description='The model requirements'),
    'model': fields.Nested(model, required=True, description='The model')
})

model_request = api.model(name='Ordered Model Request', model={
    'data_requirements': fields.Nested(requirements, required=True, description='The model requirements'),
    'model_type': fields.String(required=True, description='The model type'),
    'initial_model': fields.Raw(required=False, description='The model type')
})

model_buyer_service = ModelBuyerService()


@api.route('', endpoint='model_resources_ep')
class ModelResources(Resource):

    @staticmethod
    def _load_file(request_file, filename):
        if filename not in request_file:
            flash('No file part')
            return redirect(request.url)
        return request_file[filename]


    #@api.expect(requirements, validate=True)
    @api.marshal_with(ordered_model, code=201)
    @api.doc('Create order model')
    def post(self):
        logging.info("New order model")
        data = json.loads(self._load_file(request.files, 'model').stream.read())
        file = self._load_file(request.files, 'file')
        return model_buyer_service.make_new_order_model(data, file), 200

    @api.marshal_list_with(ordered_model)
    def get(self):
        return model_buyer_service.get_all(), 200


@api.route('/<model_id>', endpoint='model_ep')
@api.response(404, 'Model not found')
@api.param('model_id', 'The model identifier')
class ModelResource(Resource):

    @api.doc('put_model')
    #@api.marshal_with(updated_model)
    def put(self, model_id):
        data = request.get_json()
        logging.info("Received final update from fed. aggr. {}".format(data))
        return model_buyer_service.finish_model(model_id, data), 200

    @api.doc('patch_model')
    #@api.marshal_with(updated_model)
    def patch(self, model_id):
        data = request.get_json()
        logging.info("Received update from fed. aggr. {}".format(data))
        model_buyer_service.update_model(model_id, data)
        return 200

    @api.doc('get_model')
    @api.marshal_with(model)
    def get(self, model_id):
        model_buyer_service.get(model_id)
        return 200
