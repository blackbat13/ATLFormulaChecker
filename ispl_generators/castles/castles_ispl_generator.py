import itertools
import random
from tools.string_tools import StringTools
from typing import List


class CastlesIsplGenerator:
    ispl_model = ""
    workers = []
    no_castles = 3
    castles_life = [3, 3, 3]
    no_workers = 0

    def __init__(self):
        return

    def create_ispl_model(self, workers: List[int]):
        self.workers = workers
        self.no_workers = sum(self.workers)
        self.ispl_model += self.__define_semantics()
        self.ispl_model += self.__create_environment()
        for worker_id in range(0, self.no_workers):
            self.ispl_model += self.__create_worker(worker_id)
        self.ispl_model += self.__create_evaluation()
        self.ispl_model += self.__create_init_states()
        self.ispl_model += self.__create_groups()
        self.ispl_model += self.__create_formulae()
        return self.ispl_model

    def __define_semantics(self):
        semantics = "Semantics=SingleAssignment;\n\n"
        return semantics

    def __create_environment(self):
        environment = "Agent Environment\n"
        environment += self.__create_environment_obsvars()
        environment += self.__create_environment_vars()
        environment += self.__create_environment_actions()
        environment += self.__create_environment_protocol()
        environment += self.__create_environment_evolution()
        environment += "end Agent\n\n"
        return environment

    def __create_environment_obsvars(self):
        obsvars = "\tObsvars:\n"

        for castle_id in range(1, self.no_castles + 1):
            obsvars += f"\t\tcastle{castle_id}Defeated: boolean;\n"

        obsvars += "\tend Obsvars\n"
        return obsvars

    def __create_environment_vars(self):
        vars = "\tVars:\n"

        for castle_id in range(1, self.no_castles + 1):
            vars += f"\t\tcastle{castle_id}HP: 0..{self.castles_life[castle_id-1]};\n"

        vars += "\tend Vars\n"
        return vars

    def __create_environment_actions(self):
        actions = "\tActions = {none};\n"
        return actions

    def __create_environment_protocol(self):
        protocol = "\tProtocol:\n\t\tOther: {none};\n\tend Protocol\n"
        return protocol

    def __create_environment_evolution(self):
        evolution = "\tEvolution:\n"

        actions = []

        worker_id = -1
        for castle_id in range(1, self.no_castles + 1):
            for _ in range(0, self.workers[castle_id - 1]):
                worker_id += 1
                actions.append(['wait', 'defend'])
                for attacked_id in range(1, self.no_castles + 1):
                    if attacked_id == castle_id:
                        continue
                    actions[-1].append(f'attack{attacked_id}')

        for round in itertools.product(*actions):
            castle_lifes = [0, 0, 0]
            defenders = [0, 0, 0]
            attacked = [0, 0, 0]

            worker_id = -1
            for castle_id in range(1, self.no_castles + 1):
                for _ in range(0, self.workers[castle_id - 1]):
                    worker_id += 1
                    action = round[worker_id]
                    if action == "defend":
                        defenders[castle_id - 1] += 1
                    elif action != "wait":
                        for attacked_id in range(1, self.no_castles + 1):
                            if action == f'attack{attacked_id}':
                                attacked[attacked_id - 1] += 1
                                break

            for castle_id in range(0, self.no_castles):
                if attacked[castle_id] > defenders[castle_id]:
                    castle_lifes[castle_id] -= (attacked[castle_id] - defenders[castle_id])

            for castle_id in range(1, self.no_castles + 1):
                if castle_lifes[castle_id - 1] == 0:
                    continue

                evolution += f"\t\tcastle{castle_id}Defeated=true if\n"
                for worker_id in range(0, self.no_workers):
                    evolution += f"\t\t\tWorker{worker_id + 1}.Action={round[worker_id]} and\n"

                life_req = castle_lifes[castle_id-1] * (-1)
                if life_req > 3:
                    life_req = 3
                evolution += f"\t\t\tcastle{castle_id}HP <= {life_req};\n"

            for castle_id in range(1, self.no_castles + 1):
                if castle_lifes[castle_id - 1] == 0:
                    continue

                for life in range(0, self.castles_life[castle_id - 1] + 1):
                    new_life = life + castle_lifes[castle_id - 1]
                    if new_life < 0:
                        new_life = 0

                    evolution += f"\t\tcastle{castle_id}HP={new_life} if\n"
                    for worker_id in range(0, self.no_workers):
                        evolution += f"\t\t\tWorker{worker_id + 1}.Action={round[worker_id]} and\n"

                    evolution += f"\t\t\tcastle{castle_id}HP = {life};\n"

        evolution += "\tend Evolution\n"
        return evolution

    def __create_worker(self, worker_id: int):
        agent = f"Agent Worker{worker_id+1}\n"
        # agent += self.__create_worker_lobsvars(worker_id)
        agent += self.__create_worker_vars(worker_id)
        agent += self.__create_worker_actions(worker_id)
        agent += self.__create_worker_protocol(worker_id)
        agent += self.__create_worker_evolution(worker_id)
        agent += "end Agent\n\n"
        return agent

    def __create_worker_lobsvars(self, worker_id: int):
        lobsvars = "\tLobsvars = {"

        worker_castle_id = self.get_castle_id(worker_id) + 1
        lobsvars += f"castle{worker_castle_id}HP"

        lobsvars += "};\n"
        return lobsvars

    def __create_worker_vars(self, worker_id: int):
        vars = "\tVars:\n"
        vars += "\t\tcanDefend: boolean;\n"
        vars += "\tend Vars\n"
        return vars

    def __create_worker_actions(self, worker_id: int):
        actions = "\tActions = {"
        worker_castle_id = self.get_castle_id(worker_id)
        for castle_id in range(0, self.no_castles):
            if worker_castle_id == castle_id:
                continue
            actions += f"attack{castle_id+1}, "
        actions += "defend, "
        actions += "wait};\n"
        return actions

    def __create_worker_protocol(self, worker_id: int):
        protocol = "\tProtocol:\n"
        worker_castle_id = self.get_castle_id(worker_id)
        protocol += f"\t\tEnvironment.castle{worker_castle_id + 1}Defeated=true: " + "{wait};\n"
        protocol += f"\t\tEnvironment.castle{worker_castle_id + 1}Defeated=false and canDefend=true: " + "{defend, "
        for castle_id in range(0, self.no_castles):
            if worker_castle_id == castle_id:
                continue
            protocol += f"attack{castle_id+1}, "
        protocol += "wait};\n"
        protocol += f"\t\tEnvironment.castle{worker_castle_id + 1}Defeated=false and canDefend=false: " + "{"
        for castle_id in range(0, self.no_castles):
            if worker_castle_id == castle_id:
                continue
            protocol += f"attack{castle_id+1}, "
        protocol += "wait};\n"
        protocol += "\tend Protocol\n"
        return protocol

    def __create_worker_evolution(self, worker_id: int):
        evolution = "\tEvolution:\n"
        evolution += "\t\tcanDefend=false if Action=defend;\n"
        evolution += "\t\tcanDefend=true if canDefend=false;\n"
        evolution += "\tend Evolution\n"
        return evolution

    def __create_evaluation(self):
        evaluation = "Evaluation\n"
        evaluation += "\tcastle3Defeated if Environment.castle3Defeated = true;\n"
        evaluation += "end Evaluation\n\n"
        return evaluation

    def __create_init_states(self):
        init_states = "InitStates\n"
        for castle_id in range(0, self.no_castles):
            init_states += f"\tEnvironment.castle{castle_id + 1}HP={self.castles_life[castle_id]} and\n"
            init_states += f"\tEnvironment.castle{castle_id + 1}Defeated=false and\n"

        for worker_id in range(0, self.no_workers):
            init_states += f"\tWorker{worker_id + 1}.canDefend=true and\n"
        init_states = init_states.rstrip("\ndna ")
        init_states += ";\nend InitStates\n\n"
        return init_states

    def __create_groups(self):
        groups = "Groups\n"
        groups += "\tc12 = {"
        for worker_id in range(0, self.workers[0] + self.workers[1]):
            groups += f"Worker{worker_id + 1}, "

        groups = groups.rstrip(" ,")
        groups += "};\n"
        groups += "end Groups\n\n"
        return groups

    def __create_formulae(self):
        formulae = "Formulae\n"
        formulae += "\t<c12>F(castle3Defeated);\n"
        formulae += "end Formulae\n\n"
        return formulae

    def get_castle_id(self, worker_id: int):
        castle_id = 0
        workers_sum = 0
        for i in self.workers:
            workers_sum += i
            if worker_id >= workers_sum:
                castle_id += 1
            else:
                break

        return castle_id


castles_ispl_generator = CastlesIsplGenerator()
workers = [1, 1, 2]
f = open(f"castles{workers[0]}{workers[1]}{workers[2]}.ispl", "w")
f.write(castles_ispl_generator.create_ispl_model(workers))
f.close()

print(f"Done. Created model saved in castles{workers[0]}{workers[1]}{workers[2]}.ispl")
