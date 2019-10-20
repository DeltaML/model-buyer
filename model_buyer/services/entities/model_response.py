class ModelResponse:

    @staticmethod
    def map_partial_mse(partial_mse, contribs, total_spent, improvement):
        if not partial_mse:
            return []
        # TODO: Update payment hardcoded
        p_mse_map = []
        for do_id, p_mse in partial_mse.items():
            contrib = round(contribs[do_id] * 100.0, 2)
            payment = round(int(total_spent * improvement) * contribs[do_id], 3)
            p_mse_r = round(p_mse, 2)
            p_mse_map.append({
                'data_owner': do_id,
                'partial_MSE': p_mse_r,
                'contributions': contrib,
                'payment': payment
            })
        return p_mse_map

    @staticmethod
    def map_weights(weights):
        return weights.tolist()

    def __init__(self, model):
        self.model = {"id": model.id,
                      "weights": self.map_weights(model.model.weights),
                      "type": model.model_type,
                      "status": model.status,
                      "creation_date": model.creation_date,
                      "updated_date": model.updated_date,
                      "user_id": model.user_id,
                      "name": model.name}

        self.metrics = {"mse": model.mse,
                        "improvement": model.improvement,
                        "partial_MSEs": self.map_partial_mse(model.partial_MSEs, model.contributions, model.payments, model.improvement),
                        "initial_mse": model.initial_mse,
                        'iterations': model.iterations,
                        'mse_history': model.mse_history,
                        'initial_payment': model.payments,
                        'spent': round(model.payments * model.improvement, 3)
                        }


class NewModelResponse:

    def __init__(self, ordered_model):
        self.requirements = ordered_model.request_data
        self.model = {"id": ordered_model.id,
                      "creation_date": ordered_model.creation_date,
                      "updated_date": ordered_model.updated_date,
                      "status": ordered_model.status,
                      "type": ordered_model.model_type,
                      "weights": ordered_model.get_weights_as_list()
                      }
        self.metrics = {"mse": ordered_model.mse,
                        "improvement": ordered_model.improvement,
                        }

    def get_update_response(self, diffs, partial_diffs):
        return {
            "weights": self.model['weights'],
            "mse": self.metrics['mse'],
            "diffs": diffs,
            "partial_diffs": partial_diffs
        }


class NewModelRequestData:

    def __init__(self, ordered_model, requirements, user, model_type, step, public_key):
        self.requirements = requirements
        self.status = ordered_model.status
        self.model_id = ordered_model.id
        self.model_type = model_type
        self.model_buyer_id = user.delta_id
        self.model_buyer_address = user.address
        self.weights = ordered_model.get_weights_as_list()
        self.public_key = public_key
        self.step = step
        self.payments = ordered_model.payments

    def get(self):
        return dict(requirements=self.requirements,
                    status=self.status,
                    model_id=self.model_id,
                    model_type=self.model_type,
                    model_buyer_id=self.model_buyer_id,
                    model_buyer_address=self.model_buyer_address,
                    weights=self.weights,
                    step=self.step,
                    public_key=self.public_key,
                    payments=self.payments)
