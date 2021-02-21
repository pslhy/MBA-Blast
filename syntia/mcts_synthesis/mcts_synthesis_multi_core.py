import sys
from z3 import simplify
from mcts import *
from game import Game, Variable
from grammar import Grammar
from mctsutils import get_random_inputs
from paralleliser import Paralleliser

BITSIZE = 32
MAX_UNSIGNED = 2 ** BITSIZE

if len(sys.argv) < 2:
    max_iter = 30000
else:
    max_iter = int(sys.argv[1])

if len(sys.argv) < 3:
    uct_scalar = 1.2
else:
    uct_scalar = float(sys.argv[2])


def oracle(args):
    x = args[0]
    y = args[1]
    z = args[2]
    return (x + x + x) % MAX_UNSIGNED
    # return ((x + y) - (x * z)) % MAX_UNSIGNED


def synthesise(command, result, index):
    ret = ""

    max_iter = command[0]
    uct_scalar = command[1]
    game = command[2]
    oracle = command[3]
    synthesis_inputs = command[4]

    mc = MCTS(game, oracle, synthesis_inputs, uct_scalar=uct_scalar)
    mc.verbosity_level = 1
    s = State(game, BITSIZE)

    mc.search(s, max_iter)

    if mc.final_expression:
        ret = rpn_to_infix(mc.final_expression)
        print "{} ({} iterations)".format(rpn_to_infix(mc.final_expression), mc.current_iter)
        try:
            simplified = simplify(game.to_z3(mc.final_expression))
            print "{} (simplified)".format(simplified)
        except:
            pass

    result[index] = ret


variables = []
for var_index in xrange(3):
    v = Variable("V.{}".format(var_index), BITSIZE)
    variables.append(v)

constants = OrderedSet(["1"])

grammar = Grammar(variables, constants=constants)

game = Game(grammar, variables, bitsize=BITSIZE)

task_groups = []
workers = []
commands = []

for index in xrange(1):
    task_group = "TG"
    task_groups.append(task_group)

    # this may take some time
    synthesis_inputs = get_random_inputs(len(variables), 20)

    command = [max_iter, uct_scalar, game, oracle, synthesis_inputs]

    workers.append(synthesise)
    commands.append(command)

number_of_tasks = len(commands)

print "Starting main synthesis"
print number_of_tasks

paralleliser = Paralleliser(commands, workers, number_of_tasks, task_groups)

start_time = time()
paralleliser.execute()

end_time = time()

print "Synthesis finished in {} seconds".format(end_time - start_time)
