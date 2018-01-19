import os
from copy import copy
from my_turtle import trace

"""
After updating the database, please run this script.
"""

def find_solutions(trace_ans, state, index):
    solutions = []
    for x in range(1, 6):
        state[index] = x
        if index < 4:
            solutions += find_solutions(trace_ans, state, index + 1)
        else:
            try:
                trace_state = trace(state)
            except IndexError:
                pass
            else:
                if trace_ans == trace_state:
                    solutions.append(copy(state))
    return solutions


if(__name__ == "__main__"):
    traces, all_sols = [], []

    fname = os.path.join('data', 'patterns.dat')
    with open(fname, 'r') as f:
        for line in f:
            pattern = line.split()[0]
            pattern = [int(x) for x in pattern]
            try:
                pattern_trace = trace(pattern)
            except IndexError:
                pass
            else:
                traces.append(pattern_trace)

    with open('data/patterns.dat', 'w') as f:
        for value in traces:
            solutions = find_solutions(value, [1, 1, 1, 1, 1], 0)
            if solutions not in all_sols:
                all_sols.append(solutions)
                for pattern in solutions:
                    for element in pattern:
                        f.write(str(element))
                    if pattern != solutions[-1]:
                        f.write(" ")
            if value != traces[-1]:
                f.write('\n')
