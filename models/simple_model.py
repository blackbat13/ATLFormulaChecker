import json
import ast
from typing import List, Set
from logics.atl.atl_ir_model import ATLIrModel, ATLirModel
from logics.atl.mv.mvatl_model import MvATLirModel
from logics.sl.strategy_logic import SLIr
from logics.atl.transition import Transition


class SimpleModel:
    @property
    def graph(self) -> List[List[Transition]]:
        return self.__graph

    @graph.setter
    def graph(self, value: List[List[Transition]]):
        self.__graph = value

    no_states = 0
    no_agents = 0
    no_transitions = 0
    epistemic_classes = []
    epistemic_class_membership = []
    states = []
    first_state_id = 0
    pre_image = []

    def __init__(self, no_agents: int):
        self.prepare_variables()
        self.no_agents = no_agents
        for _ in range(0, self.no_agents):
            self.epistemic_classes.append([])
            self.epistemic_class_membership.append([])

    def prepare_variables(self) -> None:
        """
        Sets default values for used variables
        :return: None
        """
        self.graph = []
        self.pre_image = []
        self.no_states = 0
        self.no_agents = 0
        self.no_transitions = 0
        self.epistemic_classes = []
        self.epistemic_class_membership = []
        self.states = []
        self.first_state_id = 0

    def add_transition(self, from_state_id: int, to_state_id: int, actions: List[str]) -> None:
        """
        Adds transition between to states in the model
        :param from_state_id:
        :param to_state_id:
        :param actions: List of actions for the transition
        :return: None
        """
        self.resize_to_state(max(from_state_id, to_state_id))
        # if self.is_unique_transition(Transition(to_state_id, actions), from_state_id):
        self.graph[from_state_id].append(Transition(to_state_id, actions))
        self.pre_image[to_state_id].append(from_state_id)
        self.no_transitions += 1

    def is_unique_transition(self, transition: Transition, state_id: int) -> bool:
        for tr in self.graph[state_id]:
            if tr.actions == transition.actions and tr.next_state == transition.next_state:
                return False

        return True

    def resize_to_state(self, state_id: int) -> None:
        """
        Resize used structures to hold more states
        :param state_id:
        :return:
        """
        while len(self.graph) <= state_id:
            self.graph.append([])
            self.pre_image.append([])

        for agent_number in range(0, self.no_agents):
            while len(self.epistemic_class_membership[agent_number]) <= state_id:
                self.epistemic_class_membership[agent_number].append(-1)

        self.no_states = max(self.no_states, state_id + 1)

    def add_epistemic_relation(self, state_id_1: int, state_id_2: int, agent_number: int) -> None:
        """
        Adds epistemic relation between two states for the given agent to the model
        :param state_id_1:
        :param state_id_2:
        :param agent_number:
        :return: None
        """
        if self.epistemic_class_membership[agent_number][state_id_1] != -1:
            self.epistemic_classes[agent_number][self.epistemic_class_membership[agent_number][state_id_1]].append(
                state_id_2)
            self.epistemic_class_membership[agent_number][state_id_2] = self.epistemic_class_membership[agent_number][
                state_id_1]
        elif self.epistemic_class_membership[agent_number][state_id_2] != -1:
            self.epistemic_classes[agent_number][self.epistemic_class_membership[agent_number][state_id_2]].append(
                state_id_1)
            self.epistemic_class_membership[agent_number][state_id_1] = self.epistemic_class_membership[agent_number][
                state_id_2]
        else:
            self.epistemic_classes[agent_number].append([state_id_1, state_id_2])
            self.epistemic_class_membership[agent_number][state_id_1] = len(
                self.epistemic_class_membership[agent_number]) - 1
            self.epistemic_class_membership[agent_number][state_id_2] = self.epistemic_class_membership[agent_number][
                state_id_1]

    def add_epistemic_class(self, agent_id: int, epistemic_class: Set[int]) -> None:
        """
        Adds epistemic class to the model
        :param agent_id: Agent id for which epistemic class is specified
        :param epistemic_class: Set of states ids in the epistemic class
        :return: None
        """
        self.epistemic_classes[agent_id].append(epistemic_class)
        epistemic_class_number = len(self.epistemic_classes[agent_id]) - 1
        for state in epistemic_class:
            self.epistemic_class_membership[agent_id][state] = epistemic_class_number

    def epistemic_class_for_state(self, state_id: int, agent_id: int) -> Set[int]:
        """
        Returns a set of states ids in the epistemic class of a given state for a given agent
        :param state_id:
        :param agent_id:
        :return: Set of states ids in the epistemic class
        """
        if self.epistemic_class_membership[agent_id][state_id] == -1:
            return {state_id}

        return self.epistemic_classes[agent_id][self.epistemic_class_membership[agent_id][state_id]]

    def epistemic_class_for_state_and_coalition(self, state_id: int, coalition: List[int]) -> Set[int]:
        """
        Returns a set of states ids in the epistemic class of a given state for a given coalition
        :param state_id:
        :param coalition: List of agents ids
        :return: Set of states ids in the epistemic class
        """
        epistemic_class = set()
        for agent_number in coalition:
            if self.epistemic_class_membership[agent_number][state_id] == -1:
                epistemic_class.add(state_id)
            else:
                epistemic_class.update(
                    self.epistemic_classes[agent_number][self.epistemic_class_membership[agent_number][state_id]])

        return epistemic_class

    def get_possible_strategies(self, state_id: int) -> List[tuple]:
        """
        Returns a list of possible strategies in a state
        :param state_id:
        :return: List of possible strategies
        """
        possible_actions = set()
        for transition in self.graph[state_id]:
            possible_actions.add(tuple(transition.actions))

        return list(possible_actions)

    def get_possible_strategies_for_coalition(self, state_id: int, coalition: List[int]) -> List[tuple]:
        """
        Returns a list of possible strategies for given coalition in a given state.
        Order of actions in a strategy is the same as order of agents in the coalition.
        :param state_id:
        :param coalition: list of agents ids
        :return: List of possible strategies
        """
        possible_actions = set()
        for transition in self.graph[state_id]:
            actions = []
            for agent_id in coalition:
                actions.append(transition.actions[agent_id])
            possible_actions.add(tuple(actions))

        return list(possible_actions)

    def to_atl_perfect(self, actions) -> ATLIrModel:
        """
        Creates Alternating-Time Temporal Logic model with perfect information
        :param actions:
        :return: ATLIr model
        """
        atl_model = ATLIrModel(self.no_agents)
        for i in range(0, len(actions)):
            for action in actions[i]:
                atl_model.add_action(i, action)
        for state_id in range(0, len(self.graph)):
            for transition in self.graph[state_id]:
                atl_model.add_transition(state_id, transition.next_state, transition.actions)
        atl_model.states = self.states
        return atl_model

    def to_atl_imperfect(self, actions) -> ATLirModel:
        """
        Creates Alternating-Time Temporal Logic model with imperfect information
        :param actions:
        :return: ATLir model
        """
        atl_model = ATLirModel(self.no_agents)
        for i in range(0, len(actions)):
            for action in actions[i]:
                atl_model.add_action(i, action)
        for state_id in range(0, len(self.graph)):
            for transition in self.graph[state_id]:
                atl_model.add_transition(state_id, transition.next_state, transition.actions)
        for i in range(0, len(self.epistemic_classes)):
            for epistemic_class in self.epistemic_classes[i]:
                atl_model.add_epistemic_class(i, epistemic_class)
        atl_model.states = self.states
        return atl_model

    def to_mvatl_imperfect(self, actions, lattice) -> MvATLirModel:
        """
        Creates Multi-Valued Alternating-Time Temporal Logic model with imperfect information
        :param actions:
        :param lattice:
        :return: MvATLir model
        """
        mvatl_model = MvATLirModel(self.no_agents, lattice)
        for i in range(0, len(actions)):
            for action in actions[i]:
                mvatl_model.add_action(i, action)
        for state_id in range(0, len(self.graph)):
            for transition in self.graph[state_id]:
                mvatl_model.add_transition(state_id, transition.next_state, transition.actions)
        for i in range(0, len(self.epistemic_classes)):
            for epistemic_class in self.epistemic_classes[i]:
                mvatl_model.add_epistemic_class(i, epistemic_class)
        mvatl_model.states = self.states
        return mvatl_model

    def to_sl_perfect(self, actions) -> SLIr:
        """
        Creates Strategy Logic model with perfect information
        :param actions:
        :return: SLIr model
        """
        sl_model = SLIr(self.no_agents)
        for i in range(0, len(actions)):
            for action in actions[i]:
                sl_model.add_action(i, action)
        for state_id in range(0, len(self.graph)):
            for transition in self.graph[state_id]:
                sl_model.add_transition(state_id, transition.next_state, transition.actions)
        sl_model.states = self.states
        return sl_model

    def to_subjective(self, coalition: List[int]) -> None:
        """
        Converts model to subjective semantics for ATLir
        Adds one more state to the model and marks it as the initial state
        :param coalition: list of agent ids for which model should be converted
        :return: None
        """
        first_state_epistemic_class = self.epistemic_class_for_state_and_coalition(0, coalition)
        state_id = len(self.states)
        actions = []
        for _ in range(0, self.no_agents):
            actions.append('Wait')
        for epistemic_state_id in first_state_epistemic_class:
            self.add_transition(state_id, epistemic_state_id, actions)

        self.first_state_id = state_id
        self.states.append(self.states[0])

    def simulate(self, agent_number: int) -> None:
        print("----SIMULATION START-----")
        current_state = 0
        while True:
            print()
            self.simulate_print_current_state(current_state)
            self.simulate_print_epistemic_states(current_state, agent_number)
            if len(self.graph[current_state]) == 0:
                break

            self.simulate_print_transitions(current_state)
            choice = int(input("Choose transition="))
            if choice == -1:
                break

            current_state = self.graph[current_state][choice].next_state

        print("----SIMULATION END-----")

    def simulate_print_current_state(self, current_state: int) -> None:
        print("Current state:")
        print(self.states[current_state])

    def simulate_print_epistemic_states(self, current_state: int, agent_number: int) -> None:
        print("Epistemic states:")
        for state in self.epistemic_class_for_state(current_state, agent_number):
            print(self.states[state])

    def simulate_print_transitions(self, current_state: int) -> None:
        print('Transitions:')
        i = 0
        for transition in self.graph[current_state]:
            print(str(i) + ":", transition.to_str())
            i += 1

    def dump(self) -> str:
        result = ""
        result += f"{self.no_states}\n"
        result += f"{self.no_agents}\n"
        result += self.dump_states()
        result += self.dump_transitions()
        result += self.dump_epistemic_classes()
        return result

    def dump_states(self) -> str:
        result = ""
        for state in self.states:
            result += f"{json.dumps(state)}\n"

        return result

    def dump_transitions(self) -> str:
        result = f"{self.no_transitions}\n"
        for state_id in range(0, self.no_states):
            for transition in self.graph[state_id]:
                result += f"{state_id} {transition.next_state} {json.dumps(transition.actions)}\n"

        return result

    def dump_epistemic_classes(self) -> str:
        result = ""
        for agent_id in range(0, self.no_agents):
            result += f"{len(self.epistemic_classes[agent_id])}\n"
            for epistemic_class in self.epistemic_classes[agent_id]:
                result += f"{len(epistemic_class)}"
                for state_id in epistemic_class:
                    result += f" {state_id}"
                result += "\n"

        return result

    def js_dump_model(self) -> str:
        nodes = self.fill_nodes_model()
        links = self.fill_links_model()
        return json.dumps({"nodes": nodes, "links": links})

    def fill_nodes_model(self) -> List[hash]:
        nodes = []
        state_id = 0
        for state in self.states:
            nodes.append({"T": state, "id": state_id, "bgn": 0})
            state_id += 1

        for state_id in self.epistemic_class_for_state(0, 0):
            nodes[state_id]["bgn"] = 1

        return nodes

    def fill_links_model(self) -> List[hash]:
        links = []
        id = 0
        for state_id in range(0, self.no_states):
            for transition in self.graph[state_id]:
                if transition.next_state == state_id:
                    continue
                links.append(
                    {"id": id, "source": state_id, "target": transition.next_state, "T": transition.actions, "str": 0})
                id += 1

        return links

    def js_dump_strategy_objective(self, strategy) -> str:
        nodes = self.fill_nodes_strategy_objective()
        links = self.fill_links_strategy_objective(nodes, strategy)
        return json.dumps({"nodes": nodes, "links": links})

    def fill_nodes_strategy_objective(self) -> List[hash]:
        nodes = []
        state_id = 0
        for state in self.states:
            nodes.append({"T": state, "id": state_id, "str": 0})
            state_id += 1

        return nodes

    def fill_links_strategy_objective(self, nodes, strategy) -> List[hash]:
        links = []
        id = 0
        for state_id in range(0, self.no_states):
            for transition in self.graph[state_id]:
                if transition.next_state == state_id:
                    continue

                self.js_dump_transition(transition, state_id, strategy, links, nodes, id)
                id += 1

        return links

    def js_dump_strategy_subjective(self, strategy) -> str:
        nodes = self.fill_nodes_strategy_subjective()
        links = self.fill_links_strategy_subjective(nodes, strategy)
        return json.dumps({"nodes": nodes, "links": links})

    def fill_nodes_strategy_subjective(self) -> List[hash]:
        nodes = []
        state_id = 0
        for state in self.states:
            if state_id != self.first_state_id:
                nodes.append({"T": state, "id": state_id, "str": 0})
            state_id += 1

        return nodes

    def fill_links_strategy_subjective(self, nodes, strategy) -> List[hash]:
        links = []
        id = 0
        for state_id in range(0, self.no_states):
            if state_id == self.first_state_id:
                continue
            for transition in self.graph[state_id]:
                if transition.next_state == state_id:
                    continue

                self.js_dump_transition(transition, state_id, strategy, links, nodes, id)
                id += 1

        return links

    def js_dump_transition(self, transition, state_id, strategy, links, nodes, id) -> None:
        actions = []
        ln = 0
        if strategy[state_id] is not None:
            ln = len(strategy[state_id])
        for i in range(0, ln):
            actions.append(transition.actions[i])
        if strategy[state_id] == actions:
            links.append(
                {"id": id, "source": state_id, "target": transition.next_state, "T": transition.actions, "str": 1})
            nodes[state_id]["str"] = 1
            nodes[transition.next_state]["str"] = 1
        else:
            links.append(
                {"id": id, "source": state_id, "target": transition.next_state, "T": transition.actions, "str": 0})

    @staticmethod
    def load_from_json(json_str: str, no_agents: int, DEBUG: bool = False):
        simple_model = SimpleModel(no_agents)

        json_obj = json.loads(json_str)
        no_states = len(json_obj['nodes'])
        simple_model.states = [None for _ in range(no_states)]
        simple_model.no_states = no_states
        simple_model.resize_to_state(no_states - 1)
        actions = [set() for _ in range(no_agents)]
        for node in json_obj['nodes']:
            if DEBUG:
                print(node)
            id = int(node['id'])
            label = node['label']
            props = node['props']
            simple_model.states[id] = {'label': label, 'props': props}

        for transition in json_obj['links']:
            if DEBUG:
                print(transition)
            source = transition['source']
            target = transition['target']
            label = ast.literal_eval(transition['label'])
            for agent_id in range(no_agents):
                actions[agent_id].add(label[agent_id])
            simple_model.add_transition(from_state_id=source, to_state_id=target, actions=label)

        formula = json_obj['formula']['form']
        # print(formula)
        coalition = formula['group']
        formula = formula['operand1']['form']
        if formula['op'] == 'F':
            formula = formula['operand1']
            expression = formula
            winning_states = set()
            for state_id in range(len(simple_model.states)):
                state = simple_model.states[state_id]
                if simple_model.evaluate_on_state(expression, state):
                    winning_states.add(state_id)
                    # print(state)

            atl_Ir_model = simple_model.to_atl_perfect(actions)
            result = atl_Ir_model.minimum_formula_many_agents(coalition, winning_states)
            # print(result)

        elif formula['op'] == 'G':
            formula = formula['operand1']
            expression = formula
            winning_states = set()
            for state_id in range(len(simple_model.states)):
                state = simple_model.states[state_id]
                if simple_model.evaluate_on_state(expression, state):
                    winning_states.add(state_id)
                    # print(state)

            atl_Ir_model = simple_model.to_atl_perfect(actions)
            result = atl_Ir_model.maximum_formula_many_agents(coalition, winning_states)
            # print(result)


        return result

    def evaluate_on_state(self, expression, state) -> bool:
        if 'op' not in expression:
            expression = expression['form']

        operator = expression['op']
        if operator[0] == 'p':
            id = int(operator[1:])
            return id in state['props']

        if operator == 'and':
            return self.evaluate_on_state(expression['operand1'], state) and self.evaluate_on_state(expression['operand2'], state)

        if operator == 'or':
            return self.evaluate_on_state(expression['operand1'], state) or self.evaluate_on_state(expression['operand2'], state)

        if operator == 'not':
            return not self.evaluate_on_state(expression['operand1'], state)