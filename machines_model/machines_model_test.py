from machines_model.machine_model import MachineModel, MachineModelWithCharging, MachineModelWithStorage
import time
import datetime
from enum import Enum
from comparing_strats.graph_drawing import GraphDrawing


class ModelType(Enum):
    CLASSIC = 0
    CHARGING = 1
    STORAGE = 2


random_map = False
imperfect = False
model_type = ModelType.CLASSIC
items_limit = 1

now = datetime.datetime.now()
print(now)

if random_map:
    no_robots = 3
    no_machines = 3
    size = 3
    robot_positions, machine_positions, obstacle_positions, machine_requirements, production_times = MachineModel.random_factory_layout(
        size, no_robots, no_machines)
else:
    robot_positions = []
    machine_positions = []
    obstacle_positions = []
    ch_station_positions = []
    production_times = []
    storage_positions = []

    robot_positions.append((1, 5))
    robot_positions.append((4, 2))

    machine_positions.append((1, 3))
    machine_positions.append((4, 1))

    obstacle_positions.append((3, 0))
    obstacle_positions.append((3, 1))
    obstacle_positions.append((2, 3))

    ch_station_positions.append((0, 0))

    production_times.append(0)
    production_times.append(0)

    machine_requirements = [[0, 1], [0, 0]]

    storage_positions.append((0, 1))

    no_robots = len(robot_positions)
    no_machines = len(machine_positions)
    size = 6

print(f'({size},{size})')
start = time.clock()

if model_type == ModelType.CLASSIC:
    machine_model = MachineModel(no_robots=no_robots, no_machines=no_machines, map_size=(size, size), items_limit=items_limit,
                                 robot_positions=robot_positions, machine_positions=machine_positions,
                                 obstacle_positions=obstacle_positions, machine_requirements=machine_requirements,
                                 production_times=production_times, imperfect=imperfect)
elif model_type == ModelType.CHARGING:
    machine_model = MachineModelWithCharging(no_robots=no_robots, no_machines=no_machines, map_size=(size, size),
                                             items_limit=items_limit,
                                             robot_positions=robot_positions, machine_positions=machine_positions,
                                             obstacle_positions=obstacle_positions,
                                             charging_stations_positions=ch_station_positions,
                                             machine_requirements=machine_requirements,
                                             production_times=production_times,
                                             imperfect=imperfect)
elif model_type == ModelType.STORAGE:
    machine_model = MachineModelWithStorage(no_robots=no_robots, no_machines=no_machines, map_size=(size, size),
                                            items_limit=items_limit,
                                            robot_positions=robot_positions, machine_positions=machine_positions,
                                            obstacle_positions=obstacle_positions,
                                            machine_requirements=machine_requirements,
                                            storage_positions=storage_positions,
                                            production_times=production_times, imperfect=imperfect)
end = time.clock()
print(f'{machine_model.name}')
print(f'Machine requirements: {machine_requirements}')
print(f'Machine production times: {production_times}')
print(f'Items limit: {items_limit}')
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
    mode = 'Imperfect'
else:
    mode = 'Perfect'

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

# Add storage room - Done
# Add bad states: where machine is stuck (must wait):
#   machine can produce new item, but it has space to hold only one produced item
# Add times for production to each machine - Done
# Add energy and charging stations for robots (for example 100% at the beginning, and then each action uses 1%) - Done
# Add collisions for robots - Done
# Add obstacles to larger maps (maybe prepare some static maps)

# Properties:
#   Each machine can produce at least n items
#   Avoid waiting time for machines (when they cannot produce item, due to output capacity)
#   See if each machine request can be served under n minutes (adding clock to machines)
#   See if each robot can avoid running out of energy while serving requests


# Machine clocks are epistemic
