class ModelNotFoundException(Exception):
    def __init__(self, model_id, status_code=404):
        message = "Model not found with id {}".format(model_id)
        # Call the base class constructor with the parameters it needs
        super().__init__(message)

        # Now for your custom code...
        self.status_code = status_code


class UserNotFoundException(Exception):
    def __init__(self, user_id, status_code=404):
        message = "User not found {}".format(user_id)
        # Call the base class constructor with the parameters it needs
        super().__init__(message)

        # Now for your custom code...
        self.status_code = status_code


class OrderedModelNotFoundException(Exception):
    def __init__(self, model_id, status_code=404):
        message = "Not found ordered model {}".format(model_id)
        # Call the base class constructor with the parameters it needs
        super().__init__(message)

        # Now for your custom code...
        self.status_code = status_code


class NoResultFoundException(Exception):
    def __init__(self, filters, status_code=404):
        message = "Resource not found with filters {}".format(filters)
        # Call the base class constructor with the parameters it needs
        super().__init__(message)
        # Now for your custom code...
        self.status_code = status_code


class LoginFailureException(Exception):
    def __init__(self, status_code=400):
        # Call the base class constructor with the parameters it needs
        super().__init__()
        # Now for your custom code...
        self.status_code = status_code
