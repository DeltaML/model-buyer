import logging
from flask import jsonify, make_response, abort
from flask_restplus import Api

from model_buyer.exceptions.exceptions import NoResultFoundException, LoginFailureException, UserNotFoundException, \
    ModelNotFoundException
from model_buyer.resources.models_resource import api as model_api
from model_buyer.resources.predictions_resource import api as predictions_api
from model_buyer.resources.users_resource import api as users_api

api = Api(
    title='Model Buyer Api',
    version='1.0',
    description='Model Buyer Api API',
    doc='/doc/'
)

# Add apis to namespace
api.add_namespace(model_api)
api.add_namespace(predictions_api)
api.add_namespace(users_api)


@api.errorhandler(ModelNotFoundException)
def model_not_found_error_handler(error):
    """
    Default error handler
    :param error:
    :return:
    """
    logging.error(error)
    return {'message': str(error)}, 404


@api.errorhandler(LoginFailureException)
def login_failure_handler(error):
    """
    Default error handler
    :param error:
    :return:
    """
    logging.error(error)
    return {'message': str(error)}, 400


@api.errorhandler(NoResultFoundException)
def not_found_error_handler(error):
    """
    Default error handler
    :param error:
    :return:
    """
    logging.error(error)
    return {'message': str(error)}, 404


@api.errorhandler(UserNotFoundException)
def user_not_found_error_handler(error):
    """
    Default error handler
    :param error:
    :return:
    """
    logging.error(error)
    return {'message': str(error)}, 404


@api.errorhandler(Exception)
def default_error_handler(error):
    """
    Default error handler
    :param error:
    :return:
    """
    logging.error(error)
    return {'message': str(error)}, 500


def _handle_error(error):
    logging.error(error)
    return ErrorHandler.create_error_response(error.status_code, error.message)


class ErrorHandler:
    @staticmethod
    def create_error_response(status_code, message):
        return make_response(
            jsonify(
                {
                    "status_code": status_code,
                    "message": message
                }
            ),
            status_code
        )
