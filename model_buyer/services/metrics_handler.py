import numpy as np


class Diff(object):
    def __init__(self, diff):
        self.diff = diff

    def add_noise(self, noise):
        self.diff = self.diff + noise

    def substract_noise(self, noise):
        self.diff = self.diff - noise

    def get_array(self):
        return self.diff

    def get_mse(self):
        return np.mean(np.asarray(self.diff) ** 2)


class Diffs(object):
    def __init__(self, diffs_array):
        self.diffs = [Diff(diff) for diff in diffs_array]

    def add_noise(self, noise):
        for diff in self.diffs:
            diff.add_noise(noise)

    def substract_noise(self, noise):
        for diff in self.diffs:
            diff.substract_noise(noise)

    def get_arrays(self):
        return [diff.get_array() for diff in self.diffs]

    def get_mses(self):
        mses = [diff.get_mse() for diff in self.diffs]
        return np.mean(mses), mses


class PartialDiffs(object):
    def __init__(self, partial_diffs_dict):
        self.partial_diffs = {key: Diffs(diffs) for key, diffs in partial_diffs_dict.items()}

    def add_noise(self, noise):
        for key in self.partial_diffs:
            self.partial_diffs[key].add_noise(noise)

    def substract_noise(self, noise):
        for key in self.partial_diffs:
            self.partial_diffs[key].substract_noise(noise)

    def get_dict(self):
        return {key: p_diffs.get_arrays() for key, p_diffs in self.partial_diffs.items()}

    def get_partial_mses(self):
        return {key: p_diffs.get_mses()[0] for key, p_diffs in self.partial_diffs.items()}


class MetricsHandler(object):

    def __init__(self, noise):
        self.noise = noise

    def get_diffs(self, encr_diffs, encr_partial_diffs):
        diffs = Diffs(encr_diffs)
        diffs.add_noise(self.noise)
        partial_diffs = PartialDiffs(encr_partial_diffs)
        partial_diffs.add_noise(self.noise)
        return diffs.get_arrays(), partial_diffs.get_dict()

    def get_mses(self, diffs, partial_diffs):
        diffs = Diffs(diffs)
        diffs.substract_noise(self.noise)
        partial_diffs = PartialDiffs(partial_diffs)
        partial_diffs.substract_noise(self.noise)
        mse, mses_per_valid = diffs.get_mses()
        return mse, mses_per_valid, partial_diffs.get_partial_mses()

    def get_noise(self):
        return self.noise.tolist()
