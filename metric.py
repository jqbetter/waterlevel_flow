import numpy as np

class evaluate_metric:
    def __init__(self,x,prediction):
        super(evaluate_metric, self).__init__()
        self.n = len(x)

        deviate_value = prediction - x
        mean_dv = np.mean(deviate_value)
        se = np.sqrt(np.sum((deviate_value / prediction) ** 2) / (self.n - 2))

        relativate_error = deviate_value/x
        self.systematic_error = np.mean(relativate_error)

        number_sign_change = 0
        flag_pre = x[0] - prediction[0]
        for idx in range(1, self.n):
            delta = x[idx] - prediction[idx]
            if flag_pre > 0 and delta < 0:
                number_sign_change += 1
            elif flag_pre < 0 and delta > 0:
                number_sign_change += 1
            if delta == 0:
                pass
            else:
                flag_pre = delta

        self.random_uncertainty = 2.0 * se

        self.number_pulse_sign = len(np.where(relativate_error > 0.0001)[0]) + 0.5 * len(np.where(np.abs(relativate_error) <= 0.0001)[0])
        self.sign_test = (abs(self.number_pulse_sign - 0.5 * self.n) - 0.5) / (0.5 * np.sqrt(self.n))
        self.number_of_sign_changes = number_sign_change

        self.curve_fitting = (0.5 * (self.n - 1) - self.number_of_sign_changes - 0.5) / (0.5 * np.sqrt(self.n - 1))
        if number_sign_change >= 0.5 * (self.n - 1):
            self.curve_fitting = "NaN"

        sp = np.std(deviate_value)
        self.deviation_mean =  mean_dv / sp
