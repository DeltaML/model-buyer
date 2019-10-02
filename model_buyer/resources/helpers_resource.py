import logging

from flask import request, flash, redirect
from werkzeug.utils import secure_filename
from flask_restplus import Resource, Namespace

from model_buyer.services.model_buyer_service import ModelBuyerService

api = Namespace('helpers', description='Helper related operations')


@api.route('/transform', endpoint='transform_resources_ep')
class TransformHelperResources(Resource):
    @api.doc('transform')
    def post(self):
        logging.info("transform prediction from data owner")
        ModelBuyerService().transform_prediction(request.get_json())
        return 200


@api.route('/file', endpoint='file_resources_ep')
class FileHelperResources(Resource):

    @api.doc('upload file')
    def post(self):
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        filename = secure_filename(file.filename)
        ModelBuyerService().load_data_set(file, filename)
        return 200


@api.route('/ping', endpoint='helpers_resources_ep')
class HelperResources(Resource):

    @api.doc('ping')
    def get(self):
        return 200
