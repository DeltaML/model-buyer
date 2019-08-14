class ModelResponse:

    def __init__(self, model):
        self.model = {"id": model.id,
                      "weights": model.model.weights.tolist(),
                      "type": model.model_type,
                      "status": model.status}
        self.metrics = {"mse": model.mse,
                        "improvement":  model.improvement,
                        "partial_MSEs": model.partial_MSEs,
                        "initial_mse": model.initial_mse,
                        'iterations': model.iterations}


class NewModelResponse:

    def __init__(self, requirements, ordered_model):
        self.requirements = requirements
        self.model = {"id": ordered_model.id,
                      "status": ordered_model.status,
                      "type": ordered_model.model_type,
                      "weights": ordered_model.model.weights.tolist()
                      }
