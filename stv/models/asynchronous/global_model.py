from typing import List, Dict, Any, Set, Tuple
import time
from stv.models.asynchronous.global_state import GlobalState
from stv.models.asynchronous.local_model import LocalModel
from stv.models.asynchronous.local_transition import LocalTransition, SharedTransition
from stv.models import SimpleModel
from stv.comparing_strats import StrategyComparer
from stv.parsers import FormulaParser


class GlobalModel:
    """
    Represents global model.

    :param local_models:
    :param reduction:

    :ivar _model:
    :ivar _local_models:
    :ivar _reduction:
    :ivar _persistent:
    :ivar _states:
    :ivar _agents_count:
    :ivar _states_dict:
    :ivar _stack1:
    :ivar _stack2:
    :ivar _G:
    :ivar coalition:
    :ivar _stack1_dict:
    :ivar _transitions_count
    """

    def __init__(self, local_models: List[LocalModel], reduction: List[str], persistent: List[str],
                 coalition: List[str], goal: List[str], formula: str, show_epistemic: bool):
        self._model: SimpleModel = None
        self._local_models: List[LocalModel] = local_models
        self._reduction: List[str] = reduction
        self._persistent: List[str] = persistent
        self._coalition: List[str] = coalition
        self._goal: List[str] = goal
        self._formula = formula
        self._formula_obj = self._parse_formula()
        self._states: List[GlobalState] = []
        self._agents_count: int = 0
        self._states_dict: Dict[str, int] = dict()
        self._stack1: List[Any] = []
        self._stack2: List[int] = []
        self._G: List = []
        self.coalition: List = self._formula_obj.agents
        self._stack1_dict: Dict[str, int] = dict()
        self._transitions_count: int = 0
        self._epistemic_states_dictionaries: List[Dict[str, Set[int]]] = []
        self._show_epistemic = show_epistemic

    def _parse_formula(self):
        formula_parser = FormulaParser()
        return formula_parser.parseFormula(self._formula)

    def get_agent(self):
        return self.agent_name_to_id(self.coalition[0])

    @property
    def formula(self):
        """Formula string"""
        return self._formula

    @property
    def model(self):
        """The model."""
        return self._model

    @property
    def states_count(self):
        return len(self._states)

    @property
    def transitions_count(self):
        return self._transitions_count

    def generate(self, reduction: bool = False):
        """
        Generates model.
        :param reduction: Should reductions be used.
        :return: None.
        """
        self._agents_count = len(self._local_models)
        self._epistemic_states_dictionaries: List[Dict[str, Set[int]]] = [{} for _ in range(self._agents_count)]
        self._model = SimpleModel(self._agents_count)
        self._add_to_stack(GlobalState.initial_state(self._agents_count))
        self._add_index_to_transitions()
        # self._compute_dependent_transitions()
        self._compute_shared_transitions()
        if reduction:
            self._iter_por()
        else:
            self._compute()

        # self._model.states = self._states
        self._prepare_epistemic_relation()

        coal_ids = self.agent_name_coalition_to_ids(self._coalition)
        self._model.set_coalition(coal_ids)

    def generate_local_models(self):
        for local_model in self._local_models:
            local_model.generate()

    def _prepare_epistemic_relation(self):
        """
        Prepares epistemic relation for the model.
        Should be called after creating the model.
        :return: None
        """
        for i in range(self._agents_count):
            for _, epistemic_class in self._epistemic_states_dictionaries[i].items():
                self.model.add_epistemic_class(i, epistemic_class)

    def _add_index_to_transitions(self):
        for agent_id in range(self._agents_count):
            for i in range(len(self._local_models[agent_id].transitions)):
                for j in range(len(self._local_models[agent_id].transitions[i])):
                    self._local_models[agent_id].transitions[i][j].i = i
                    self._local_models[agent_id].transitions[i][j].j = j

    def _compute_shared_transitions(self):
        replace = []
        for agent_id in range(self._agents_count):
            for i in range(len(self._local_models[agent_id].transitions)):
                for j in range(len(self._local_models[agent_id].transitions[i])):
                    transition = self._local_models[agent_id].transitions[i][j]
                    if not transition.shared:
                        continue

                    shared_transition = self._create_shared_transition(transition, agent_id)
                    shared_transition.transition_list.sort(key=lambda tran: tran.agent_id)
                    replace.append((agent_id, i, j, shared_transition))

        for rep in replace:
            agent_id, i, j, shared_transition = rep
            self._local_models[agent_id].transitions[i][j] = shared_transition

    def _create_shared_transition(self, transition: LocalTransition, agent_id: int) -> SharedTransition:
        shared_transition = SharedTransition(transition)
        for agent_id2 in range(self._agents_count):
            if agent_id == agent_id2:
                continue

            if self._local_models[agent_id2].has_action(transition.action):
                for transition2 in self._local_models[agent_id2].get_transitions():
                    if transition2.action == transition.action:
                        shared_transition.add_transition(transition2)
                        break

        return shared_transition

    def _available_transitions_in_state_for_agent(self, state: GlobalState, agent_id: int) -> List[LocalTransition]:
        """
        Computes a list of transitions available for the specified agent in the given state.
        :param state: Global state.
        :param agent_id: Agent identifier.
        :return: List of local transitions.
        """
        agent_state_id: int = state.local_states[agent_id]
        all_transitions: List[LocalTransition] = self._local_models[agent_id].private_transitions_from_state(
            agent_state_id)
        all_transitions += self._local_models[agent_id].shared_transitions_from_state(agent_state_id)
        return list(filter(lambda transition: transition.check_conditions(state), all_transitions))

    def _enabled_transitions_in_state(self, state: GlobalState) -> List[List[LocalTransition]]:
        """
        Computes all enabled transitions for the given global state.
        :param state:
        :return:
        """
        all_transitions = []
        for agent_id in range(len(self._local_models)):
            all_transitions.append(self._available_transitions_in_state_for_agent(state, agent_id))

        result = []
        for agent_id in range(self._agents_count):
            result.append(self._enabled_transitions_for_agent(agent_id, all_transitions))

        return result

    def _enabled_transitions_for_agent(self, agent_id: int, all_transitions: List[List[LocalTransition]]):
        """
        Computes enabled transitions for given agent based on the transitions from the global state.
        :param agent_id: Agent identifier.
        :param all_transitions: List containing all of the transitions going out from specific global state.
        :return:
        """
        result = []
        for transition in all_transitions[agent_id]:
            if not transition.shared:
                result.append(transition)
                continue

            if self._check_if_shared_transition_is_enabled(transition, agent_id, all_transitions):
                result.append(transition)

        return result

    def _check_if_shared_transition_is_enabled(self, transition: LocalTransition, agent_id: int,
                                               all_transitions: List[List[LocalTransition]]) -> bool:
        is_ok = True
        for agent_id2 in range(len(self._local_models)):
            if agent_id2 == agent_id:
                continue

            if self._local_models[agent_id2].has_action(transition.action):
                is_ok = False
                for transition2 in all_transitions[agent_id2]:
                    if transition2.shared and transition2.action == transition.action:
                        is_ok = True
                        break

            if not is_ok:
                return False

        return True

    def _enabled_transitions_in_state_single_item_set(self, state: GlobalState) -> Set[Tuple[int, int, int]]:
        enabled = self._enabled_transitions_in_state(state)
        result = set()
        for agent_id in range(self._agents_count):
            for transition in enabled[agent_id]:
                result.add(transition.to_tuple())
                if not transition.shared:
                    continue
                for agent_id2 in range(agent_id + 1, self._agents_count):
                    i = 0
                    for transition2 in enabled[agent_id2]:
                        if transition2.shared and transition2.action == transition.action:
                            enabled[agent_id2].pop(i)
                            break
                        i += 1
        return result

    def _new_state_after_private_transition(self, state: GlobalState, transition: LocalTransition) -> GlobalState:
        agent_id = transition.agent_id
        new_state = GlobalState.copy_state(state, self._persistent)
        new_state.set_local_state(agent_id, self._local_models[agent_id].get_state_id(transition.state_to))
        new_state = self._copy_props_to_state(new_state, transition)
        return new_state

    def _new_state_after_shared_transition(self, state: GlobalState, actual_transition) -> (GlobalState, List[int]):
        new_state = GlobalState.copy_state(state, self._persistent)
        agents = []
        for act_tran in actual_transition:
            new_state.set_local_state(act_tran[0], self._local_models[act_tran[0]].get_state_id(
                act_tran[1].state_to))
            new_state = self._copy_props_to_state(new_state, act_tran[1])
            agents.append(act_tran[0])
        return new_state, agents

    def _new_state_after_shared_transitions_list(self, state: GlobalState, transitions: List[LocalTransition]) -> GlobalState:
        new_state = GlobalState.copy_state(state, self._persistent)
        for transition in transitions:
            new_state.set_local_state(transition.agent_id,
                                      self._local_models[transition.agent_id].get_state_id(transition.state_to))
            new_state = self._copy_props_to_state(new_state, transition)
        return new_state

    def _compute_next_for_state(self, state: GlobalState, current_state_id: int):
        all_transitions = self._enabled_transitions_in_state(state)
        visited = []
        for agent_id in range(len(self._local_models)):
            self._compute_next_for_state_for_agent(state, current_state_id, agent_id, visited, all_transitions)

    def _compute_next_for_state_for_agent(self, state: GlobalState, current_state_id: int, agent_id: int, visited: List[str],
                                          all_transitions: List[List[LocalTransition]]):
        for transition in all_transitions[agent_id]:
            if transition.shared and transition.action not in visited:
                visited.append(transition.action)
                actual_transition = [(agent_id, transition)]
                for n_a_id in range(agent_id + 1, len(self._local_models)):
                    for n_tr in all_transitions[n_a_id]:
                        if n_tr.shared and n_tr.action == transition.action:
                            actual_transition.append((n_a_id, n_tr))
                            break
                new_state, agents = self._new_state_after_shared_transition(state, actual_transition)
                new_state_id = self._add_state(new_state)
                self._add_transition(current_state_id, new_state_id, transition)
            elif not transition.shared:
                new_state = self._new_state_after_private_transition(state, transition)
                new_state_id = self._add_state(new_state)
                self._add_transition(current_state_id, new_state_id, transition)

    def _copy_props_to_state(self, state: GlobalState, transition: LocalTransition) -> GlobalState:
        for prop in transition.props:
            if type(transition.props[prop]) is str:
                if transition.props[prop][0] == "?":
                    prop_name = transition.props[prop][1:]
                    if prop_name in transition.props:
                        state.set_prop(prop_name, transition.props[prop_name])
                    elif prop_name in state.props:
                        state.set_prop(prop_name, state.props[prop_name])
            elif type(transition.props[prop]) is bool:
                if not transition.props[prop]:
                    state.remove_prop(prop)
                else:
                    state.set_prop(prop, transition.props[prop])
            else:
                state.set_prop(prop, transition.props[prop])
        return state

    def _state_find(self, state: GlobalState) -> int:
        if state.to_str() in self._states_dict:
            return self._states_dict[state.to_str()]

        return -1

    def _is_in_G(self, state: GlobalState) -> bool:
        for st in self._G:
            if st.equal(state):
                return True
        return False

    def _find_state_on_stack1(self, state: GlobalState) -> int:
        str_state: str = state.to_str()

        if str_state in self._stack1_dict:
            return self._stack1_dict[str_state]

        return -1

    def _add_to_stack(self, state: GlobalState) -> bool:
        str_state: str = state.to_str()

        if str_state in self._stack1_dict:
            return False
        else:
            self._stack1.append(state)
            self._stack1_dict[state.to_str()] = len(self._stack1) - 1
            return True

    def _pop_from_stack(self):
        self._stack1_dict[self._stack1[-1].to_str()] = -1
        self._stack1.pop()

    def _iter_por(self):
        """
        Iterative partial order reduction algorithm.
        :return: None.
        """
        dfs_stack: List[int] = [1]
        while len(dfs_stack) > 0:
            dfs: int = dfs_stack.pop()
            if dfs == 1:
                g: GlobalState = self._stack1[-1]
                reexplore: bool = False
                i: int = self._find_state_on_stack1(g)
                if i != -1 and i != len(self._stack1) - 1:
                    if len(self._stack2) == 0:
                        depth: int = 0
                    else:
                        depth: int = self._stack2[-1]
                    if i > depth:
                        reexplore = True
                    else:
                        self._pop_from_stack()
                        continue

                if not reexplore and self._is_in_G(g):
                    self._pop_from_stack()
                    continue

                self._G.append(g)
                g_state_id: int = self._add_state(g)
                E_g: Set[Tuple[int, int, int]] = set()
                en_g: Set[Tuple[int, int, int]] = self._enabled_transitions_in_state_single_item_set(g)
                if len(en_g) > 0:
                    if not reexplore:
                        E_g = self._ample(g)

                    if len(E_g) == 0:
                        E_g = en_g

                    if E_g == en_g:
                        self._stack2.append(len(self._stack1))

                    dfs_stack.append(-1)
                    for tup in E_g:
                        a: LocalTransition = self._local_models[tup[0]].transitions[tup[1]][tup[2]]
                        g_p: GlobalState = self._successor(g, a)
                        g_p_state_id : int = self._add_state(g_p)

                        self._add_transition(g_state_id, g_p_state_id, a)
                        if self._add_to_stack(g_p):
                            dfs_stack.append(1)
            elif dfs == -1:
                if len(self._stack2) == 0:
                    depth: int = 0
                else:
                    depth: int = self._stack2[-1]
                if depth == len(self._stack1):
                    self._stack2.pop()
                self._pop_from_stack()

    def _ample(self, state: GlobalState) -> Set[Tuple[int, int, int]]:
        """
        Computes ample set for given state.
        :param state: Global state.
        :return: Ample set.
        """
        V = self._enabled_transitions_in_state_single_item_set(state)
        while len(V) > 0:
            alpha = V.pop()
            V.add(alpha)
            X = {alpha}
            U = {alpha}
            DIS = set()
            while len(X) > 0 and len(X.difference(V)) == 0:
                DIS.update(self._enabled_for_x(X))
                X = self._dependent_for_x(X, DIS, U)
                U.update(X)
            if len(X) == 0:# and not self._check_for_cycle(state, U):# and not self._check_for_k(state, U):
                return U
            V.difference_update(U)
        return set()

    def _check_for_cycle(self, state: GlobalState, X: Set[Tuple[int, int, int]]) -> bool:
        for tup in X:
            transition = self._local_models[tup[0]].transitions[tup[1]][tup[2]]
            successor_state = self._successor(state, transition)
            if self._find_state_on_stack1(successor_state) != -1:
                return True
        return False

    def _check_for_k(self, state: GlobalState, X: Set[Tuple[int, int, int]]) -> bool:
        for tup in X:
            transition = self._local_models[tup[0]].transitions[tup[1]][tup[2]]
            successor_state = self._successor(state, transition)
            for agent_id in self.agent_name_coalition_to_ids(self._coalition):
                if state.local_states[agent_id] != successor_state.local_states[agent_id]:
                    return True

                for prop in self._local_models[agent_id].props:
                    if prop in state.props and prop not in successor_state.props:
                        return True
                    if prop not in state.props and prop in successor_state.props:
                        return True
                    if prop not in state.props:
                        continue
                    if state.props[prop] != successor_state.props[prop]:
                        return True
        return False

    def _enabled_for_x(self, X: Set[Tuple[int, int, int]]) -> Set[Tuple[int, int, int]]:
        result: Set[Tuple[int, int, int]] = set()

        for tup in X:
            transition = self._local_models[tup[0]].transitions[tup[1]][tup[2]]
            if isinstance(transition, SharedTransition):
                for transition2 in transition.transition_list:
                    for tr in self._local_models[transition2.agent_id].get_transitions():
                        if tr.state_from != transition2.state_from:
                            result.add(tr.to_tuple())
            else:
                for tr in self._local_models[transition.agent_id].get_transitions():
                    if tr.state_from != transition.state_from:
                        result.add(tr.to_tuple())

        return result

    def _dependent_for_x(self, X: Set[Tuple[int, int, int]], DIS: Set[Tuple[int, int, int]], U: Set[Tuple[int, int, int]]) -> Set[Tuple[int, int, int]]:  # !!!!
        result = set()
        for tup in X:
            transition = self._local_models[tup[0]].transitions[tup[1]][tup[2]]
            if isinstance(transition, SharedTransition):
                for transition2 in transition.transition_list:
                    for tr in self._local_models[transition2.agent_id].get_transitions():
                        if tr.to_tuple() not in DIS and tr.to_tuple() not in U:
                            result.add(tr.to_tuple())
            else:
                for tr in self._local_models[transition.agent_id].get_transitions():
                    if tr.to_tuple() not in DIS and tr.to_tuple() not in U:
                        result.add(tr.to_tuple())

        return result

    def _successor(self, state: GlobalState, transition: LocalTransition) -> GlobalState:
        if not isinstance(transition, SharedTransition):
            return self._new_state_after_private_transition(state, transition)
        else:
            return self._new_state_after_shared_transitions_list(state, transition.transition_list)

    def _add_state(self, state: GlobalState) -> int:
        state_id = self._state_find(state)
        if state_id == -1:
            state_id = len(self._states)
            state.id = state_id
            self._states.append(state)
            self._states_dict[state.to_str()] = state_id
            self._model.states.append(state.to_obj())
            for i in range(len(self._local_models)):
                epistemic_state = self._get_epistemic_state(state, i)
                self._add_to_epistemic_dictionary(epistemic_state, state_id, i)

        state.id = state_id
        return state_id

    def _get_epistemic_state(self, state: GlobalState, agent_id: int) -> hash:
        """
        Compute epistemic representation of the given state.
        :param state: State to compute.
        :param agent_id: Id of the agent for which epistemic representation should be computed.
        :return: Epistemic representation of the given state.
        """

        if state.id == 0:
            return {'local_state': -1}
        epistemic_state = {'local_state': state.local_states[agent_id]}
        props = {}

        agent_name: str = self._local_models[agent_id].agent_name

        for prop in state.props:
            if prop[0:len(agent_name)] == agent_name:
                props[prop] = state.props[prop]

        epistemic_state['props'] = props
        return epistemic_state

    def _add_to_epistemic_dictionary(self, state: hash, new_state_id: int, agent_id: int):
        """
        Adds state to the epistemic dictionary.
        :param state:
        :param new_state_id:
        :param agent_id:
        :return: None
        """
        state_str = ' '.join(str(state[e]) for e in state)
        if state_str not in self._epistemic_states_dictionaries[agent_id]:
            self._epistemic_states_dictionaries[agent_id][state_str] = {new_state_id}
        else:
            self._epistemic_states_dictionaries[agent_id][state_str].add(new_state_id)

    def _add_transition(self, state_from: int, state_to: int, transition: LocalTransition):
        self._transitions_count += 1
        self._model.add_transition(state_from, state_to, self._create_list_of_actions(transition))

    def _create_list_of_actions(self, transition: LocalTransition) -> List[str]:
        actions = ['' for _ in range(self._agents_count)]

        if isinstance(transition, SharedTransition):
            for tr in transition.transition_list:
                actions[tr.agent_id] = tr.prot_name
        else:
            actions[transition.agent_id] = transition.prot_name

        return actions

    def _compute(self):
        """
        Compute global model.
        :return:
        """
        state: GlobalState = GlobalState.initial_state(len(self._local_models))
        self._add_state(state)
        # self._states.append(state)
        # self.model.states.append(state.to_str())
        i: int = 0
        while i < len(self._states):
            state = self._states[i]
            current_state_id = i
            i += 1

            self._compute_next_for_state(state, current_state_id)

    def agent_name_to_id(self, agent_name: str) -> int:
        for agent_id in range(len(self._local_models)):
            if self._local_models[agent_id].agent_name == agent_name:
                return agent_id
        return -1

    def agent_name_coalition_to_ids(self, agent_names: List[str]) -> List[int]:
        agent_ids: List[int] = []
        for agent_name in agent_names:
            agent_ids.append(self.agent_name_to_id(agent_name))
        return agent_ids

    def print(self):
        for model in self._local_models:
            model.print()

    def set_coalition(self, coalition: List[str]):
        self.coalition = self.agent_name_coalition_to_ids(coalition)

    def get_winning_states(self, formula_no: int) -> Set[int]:
        winning_states = set()
        for state in self._states:
            ok = True
            if formula_no == 1:
                if ("pun1" not in state.props) or (not state.props["pun1"]):
                    ok = False
            elif formula_no == 2:
                if "v_Voter1" not in state.props or state.props["v_Voter1"] == 1:
                    ok = False
                else:
                    for state_id in self._model.epistemic_class_for_state(state.id,
                                                                          self.agent_name_to_id(self._coalition[0])):
                        if "v_Voter1" in self._states[state_id].props and self._states[state_id].props["v_Voter1"] == 1:
                            ok = False
                            break

            if ok:
                winning_states.add(state.id)
        return winning_states

    def verify_approximation(self, perfect_inf: bool, formula_no: int):
        if perfect_inf:
            atl_model = self._model.to_atl_perfect(self.get_actions())
        else:
            atl_model = self._model.to_atl_imperfect(self.get_actions())

        start = time.process_time()
        result = atl_model.minimum_formula_many_agents(self.agent_name_coalition_to_ids(self._coalition),
                                                       self.get_winning_states(formula_no))
        end = time.process_time()

        return result, end - start

    def verify_domino(self):
        agent_id = self.agent_name_to_id(self._coalition[0])
        strategy_comparer = StrategyComparer(self._model, self.get_actions()[agent_id])
        start = time.process_time()
        result, strategy = strategy_comparer.domino_dfs(0, self.get_winning_states(), [agent_id],
                                                        strategy_comparer.basic_h)
        end = time.process_time()
        print(strategy)
        return result, end - start

    def get_actions(self):
        actions = []
        for local in self._local_models:
            actions.append(local.actions)
            actions[-1].add("")
        return actions

    def get_formula_winning_states(self):
        expr = self._formula_obj.expression
        result = []
        for state in self._states:
            if expr.evaluate(state.props):
                result.append(state.id)

        return result

    def coalition_ids_to_str(self, coalition: List[int]) -> List[str]:
        result = []
        for agent_id in coalition:
            result.append(self._local_models[agent_id].agent_name)
        return result


if __name__ == "__main__":
    from stv.models.asynchronous.parser import GlobalModelParser
    from stv.parsers import FormulaParser

    model = GlobalModelParser().parse("train_controller.txt")
    model.generate(reduction=False)
    formula_parser = FormulaParser()
    print(model._formula)
    formula_obj = formula_parser.parseFormula(formulaStr=model._formula)
    print(formula_obj.agents, formula_obj.type, formula_obj.expression)
    model.get_formula_winning_states()
    print(model.get_agent())

    # results_file = open("selene_results.txt", "a")
    #
    # teller_count = int(input("Teller Count: "))
    # voter_count = int(input("Voter Count: "))
    # cand_count = int(input("Candidates Count: "))
    # reduction = int(input("Reduction: "))
    #
    # formula_no = int(input("Formula (1-pun, 2-K!vVoter1): "))
    #
    # file_name = f"Selene_{teller_count}_{voter_count}_{cand_count}_0.txt"
    # model = GlobalModelParser().parse(file_name)
    # start = time.process_time()
    # model.generate(reduction=(reduction == 1))
    # end = time.process_time()
    #
    # for state in model._states:
    #     state.print()
    #
    # model.model.simulate(2)
    #
    # results_file.write(f"Teller Count: {teller_count}\n")
    # results_file.write(f"Voter Count: {voter_count}\n")
    # results_file.write(f"Candidates Count: {cand_count}\n")
    # results_file.write(f"Reduction: {reduction == 1}\n")
    # results_file.write(f"Model generated in {end - start} seconds.\n")
    # results_file.write(f"Model has {model.states_count} states.\n")
    # results_file.write(f"Model has {model.transitions_count} transitions.\n")
    # results_file.write("\n")
    #
    # # model.model.simulate(model.agent_name_to_id("Coercer1"))
    #
    # result, comp_time = model.verify_approximation(perfect_inf=True, formula_no=formula_no)
    #
    # results_file.write(f"Perfect Information:\ntime: {comp_time} seconds, result: {0 in result}\n")
    #
    # result, comp_time = model.verify_approximation(perfect_inf=False, formula_no=formula_no)
    # results_file.write(f"Imperfect Information Approximation:\ntime: {comp_time} seconds, result: {0 in result}\n")
    # results_file.write(f"Formula: {formula_no}\n")
    # results_file.write("\n\n")
    # results_file.close()

