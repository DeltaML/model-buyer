from model_buyer.models.model import Model


@staticmethod
def mock_models():
    model_1 = Model("LINEAR_REGRESSION", data=None)
    model_1.id = "1"
    model_1.status = "INITIATED"
    model_1.name = "Model 1"
    model_1.improvement = 1
    model_1.cost = 2
    model_1.iterations = 3
    return [model_1]