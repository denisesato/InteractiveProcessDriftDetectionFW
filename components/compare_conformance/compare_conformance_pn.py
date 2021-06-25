"""
    This file is part of Interactive Process Drift (IPDD) Framework.
    IPDD is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    IPDD is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with IPDD. If not, see <https://www.gnu.org/licenses/>.
"""
from pm4py.algo.evaluation.replay_fitness import algorithm as replay_fitness_evaluator
from components.compare_conformance.conformance_metric import ConformanceMetric


class ConformanceSimilarityMetric(ConformanceMetric):
    def __init__(self, window, trace, metric_name, model1, model2, sublog1, sublog2):
        super().__init__(window, trace, metric_name, model1, model2, sublog1, sublog2)

    def is_dissimilar(self):
        return self.value < 1

    def calculate(self):
        # calculate the fitness from the current sublog with the previous process model
        fitness = ConformancePn.calculate_replay_fitness(self.sublog2, self.model1)
        self.value = fitness['averageFitness']
        return self.value


class ConformancePn:
    @staticmethod
    def calculate_replay_fitness(log, model):
        fitness = replay_fitness_evaluator.apply(log, model.net, model.initial_marking, model.final_marking,
                                                 variant=replay_fitness_evaluator.Variants.ALIGNMENT_BASED)
        return fitness
