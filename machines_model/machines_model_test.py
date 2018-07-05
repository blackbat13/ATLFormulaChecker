from machines_model.machine_model import MachineModel
import time
import datetime
from comparing_strats.graph_drawing import GraphDrawing

random_map = False
imperfect = True

now = datetime.datetime.now()
print(now)

if random_map:
    no_robots = 3
    no_machines = 3
    size = 3
    robot_positions, machine_positions, obstacle_positions, machine_requirements = MachineModel.random_factory_layout(
        size, no_robots, no_machines)
else:
    robot_positions = []
    machine_positions = []
    obstacle_positions = []

    robot_positions.append((1, 5))
    robot_positions.append((4, 2))

    machine_positions.append((1, 3))
    machine_positions.append((4, 1))

    obstacle_positions.append((3, 0))
    obstacle_positions.append((3, 1))
    obstacle_positions.append((2, 3))

    machine_requirements = [[0, 1], [0, 0]]

    no_robots = len(robot_positions)
    no_machines = len(machine_positions)
    size = 6

print(f'({size},{size})')
start = time.clock()
machine_model = MachineModel(no_robots=no_robots, no_machines=no_machines, map_size=(size, size), items_limit=1,
                             robot_positions=robot_positions, machine_positions=machine_positions,
                             obstacle_positions=obstacle_positions, machine_requirements=machine_requirements,
                             imperfect=imperfect)
end = time.clock()
print(f'Number of states: {len(machine_model.states)}')
print(f'Model generation time: {end - start} seconds')
strategy = []
winning_states = set()
state_id = 0
for state in machine_model.states:
    # print(state)
    strategy.append(None)
    if state['it_count'][0] == 1 and state['it_count'][1] == 1:
        winning_states.add(state_id)

    state_id += 1

# graphDrawing = GraphDrawing(machine_model.model, strategy)
# graphDrawing.draw()

if imperfect:
    mode = 'imperfect'
else:
    mode = 'perfect'

print(f'{mode} information')

if not imperfect:
    atl_perfect_model = machine_model.model.to_atl_perfect(machine_model.get_actions())
    start = time.clock()
    result = atl_perfect_model.minimum_formula_many_agents([0, 1], winning_states)
    end = time.clock()
else:
    atl_imperfect_model = machine_model.model.to_atl_imperfect(machine_model.get_actions())
    start = time.clock()
    result = atl_imperfect_model.minimum_formula_many_agents([0, 1], winning_states)
    end = time.clock()

print(f'Verification time: {end - start} seconds')
print(f'Result: {0 in result}')
print(f'Number of reachable states: {len(result)}')
