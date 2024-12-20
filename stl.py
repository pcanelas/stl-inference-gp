from __future__ import annotations
from abc import ABC
from dataclasses import dataclass
from typing import Annotated, Union
from geneticengine.prelude import abstract
import numpy as np
import pandas as pd

from geml.simplegp import SimpleGP
from geneticengine.grammar.grammar import extract_grammar
from geneticengine.grammar.metahandlers.floats import FloatRange
from geneticengine.grammar.metahandlers.ints import IntRange
from geneticengine.grammar.metahandlers.vars import VarRange

# Load dataset
trace1 = pd.read_csv("data/nominal_trace1.csv")
time_lb = trace1["Time"].min()
time_up = trace1["Time"].max()
variables = list(trace1.columns[1:-1])

operators = [">", "<", "=="]


# Abstract base class for STL formulas
class STLFormula(ABC):
    def evaluate(self, X): ...


@abstract
class FOLFormula(STLFormula):
    def evaluate(self, X): ...


# Terminal class for Boolean literal
@dataclass
class BooleanTerminal(FOLFormula):
    value: bool

    def evaluate(self, X):
        return self.value

    def __str__(self):
        return str(self.value)


# STL Temporal Operators
@dataclass
class Always(STLFormula):
    expression: STLFormula
    lower_bound: Annotated[float, FloatRange(float(time_lb), float(time_up))]
    upper_bound: Annotated[float, FloatRange(float(time_lb), float(time_up))]
    is_open_lower_bound: bool
    is_open_upper_bound: bool

    def evaluate(self, X):
        return np.all([self.expression.evaluate(X[i]) for i in range(X.shape[0])])


@dataclass
class Eventually(STLFormula):
    expression: STLFormula
    lower_bound: Annotated[float, FloatRange(float(time_lb), float(time_up))]
    upper_bound: Annotated[float, FloatRange(float(time_lb), float(time_up))]
    is_open_lower_bound: bool
    is_open_upper_bound: bool

    def evaluate(self, X):
        return np.any([self.expression.evaluate(X[i]) for i in range(X.shape[0])])


@dataclass
class Conjunction(FOLFormula):
    left: FOLFormula
    right: FOLFormula

    def evaluate(self, X):
        return self.left.evaluate(X) and self.right.evaluate(X)


@dataclass
class Disjunction(FOLFormula):
    left: FOLFormula
    right: FOLFormula

    def evaluate(self, X):
        return self.left.evaluate(X) or self.right.evaluate(X)


# Boolean expressions
@dataclass
class Variable(FOLFormula):
    var: Annotated[str, VarRange(variables)]

    def evaluate(self, X):
        return X[self.var]  # Assumes X is a dictionary or DataFrame row

    def __str__(self):
        return f"var[{self.var}]"


@dataclass
class Negation(FOLFormula):
    expression: FOLFormula

    def evaluate(self, X):
        return not self.expression.evaluate(X)


@dataclass
class Operator(FOLFormula):
    left: Variable
    op: Annotated[str, VarRange(operators)]
    right: Union[Variable, Annotated[int, IntRange(-10, 10)]]

    def evaluate(self, X):
        left_val = self.left.evaluate(X)
        right_val = self.right.evaluate(X)
        if self.op == ">":
            return left_val > right_val
        elif self.op == "<":
            return left_val < right_val
        elif self.op == "==":
            return left_val == right_val
        else:
            raise ValueError(f"Unknown operator {self.op}")

    def __str__(self):
        return f"({self.left}) {self.op} ({self.right})"


# Fitness function for Genetic Programming
def fitness_function(formula: STLFormula):
    # y_pred = [formula.evaluate(row) for _, row in trace1.iterrows()]
    # y_true = trace1["ExpectedOutput"].values  # Replace with actual target column
    # mse = np.mean((np.array(y_pred) - y_true) ** 2)
    # TODO:
    return 10


def main():
    # Define the grammar for genetic programming
    grammar = extract_grammar(
        [
            Always,
            Eventually,
            Conjunction,
            Disjunction,
            Variable,
            Negation,
            Operator,
            BooleanTerminal,
        ],
        STLFormula,
    )

    print(grammar)

    # Run the genetic programming algorithm
    gp: SimpleGP = SimpleGP(
        fitness_function=fitness_function,
        grammar=grammar,
        minimize=True,
        max_depth=10,
        seed=123,
        population_size=50,
        elitism=1,
        novelty=2,
        mutation_probability=0.1,
        crossover_probability=0.8,
    )

    # Execute the GP search
    best_individual = gp.search()
    print("Best individual found:")
    print()
    print(best_individual)


if __name__ == "__main__":
    main()
