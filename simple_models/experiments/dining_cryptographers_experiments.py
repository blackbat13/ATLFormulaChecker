from simple_models.dining_cryptographers import DiningCryptographers
from tools.graph_drawing import GraphDrawing


class DiningCryptographersExperiments:
    def __init__(self, n: int):
        self.n = n
        self.model = None

    def run_experiments(self):
        self.generate_model()
        strategy = []
        for i in range(0, len(self.model.model.states)):
            strategy.append(None)
        graphDrawing = GraphDrawing(self.model.model, strategy)
        graphDrawing.draw()

    def generate_model(self):
        self.model = DiningCryptographers(self.n)
        self.model.generate()

# dining_cryptographers_experiments = DiningCryptographersExperiments(5)
# dining_cryptographers_experiments.run_experiments()
