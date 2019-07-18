import logging

from flask_restplus import Resource, Namespace, fields
from flask import request

from model_buyer.resources.models_resource import reduced_ordered_model
from model_buyer.services.user_service import UserService

api = Namespace('users', description='Users related operations')


user_google_token_req = api.model(name='User', model={
    'token': fields.String(required=True, description='Google login token')
})

user_data = api.model(name='User', model={
    'id': fields.String(required=True, description='The user identifier'),
    'external_id': fields.String(required=True, description='The user identifier'),
    'name': fields.String(required=True, description='The user name'),
    'email': fields.String(required=True, description='The user email'),
    'token': fields.String(required=True, description='The user token'),
    'models': fields.Nested(reduced_ordered_model, required=True, description='The user models')
})


@api.route('', endpoint='users_resources_ep')
class UserResources(Resource):

    @api.expect(user_data)
    @api.marshal_with(user_data, code=201)
    @api.doc('Create new user')
    def post(self):
        logging.info("Creating new user")
        data = request.get_json()
        return UserService().create(data), 201

    @api.marshal_list_with(user_data)
    def get(self):
        return UserService().get_all(), 200


@api.route('/<user_id>', endpoint='user_ep')
@api.response(404, 'User not found')
@api.param('user_id', 'The user identifier')
class UserResource(Resource):

    @api.doc('patch_user')
    @api.expect(user_data)
    @api.marshal_with(user_data)
    def put(self, user_id):
        logging.info("Update user")
        data = request.get_json()
        return UserService().update(user_id, data), 200

    @api.doc('get_user')
    @api.marshal_with(user_data)
    def get(self, user_id):
        return UserService().get(user_id), 200

    @api.doc('delete_user')
    def delete(self, user_id):
        return UserService().delete(user_id), 200


@api.route('/login', endpoint='users_login_resources_ep')
class UserLoginResources(Resource):

    @api.expect(user_google_token_req)
    @api.marshal_with(user_data, code=201)
    @api.doc('Login user')
    def post(self):
        logging.info("Login user")
        data = request.get_json()
        response = UserService().login(data)
        logging.info(response)
        return response, 200
