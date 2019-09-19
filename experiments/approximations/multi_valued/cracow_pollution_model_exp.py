from models.mv.cracow_pollution_model import PollutionModel
from logics.atl.mv import mvatl_parser
from tools.list_tools import ListTools
from experiments.aexperiment import AExperiment
import datetime
import time


class CracowPollutionModelExp(AExperiment):
    def __init__(self, n_agent: int, energy: int, radius: int, selected_place: int, first_place_id: int, DEBUG: bool = False):
        super().__init__(DEBUG)
        self._file_name = "results-f2-perf.txt"
        self.__n_agent = n_agent
        self.__energy = energy
        self.__radius = radius
        self.__selected_place = selected_place
        self.__first_place_id = first_place_id
        self.__energies = ListTools.create_value_array_of_size(n_agent, energy)
        self.__map, self.__connections = self.__create_map()
        self.__result = None

    def __create_map(self):
        map = []
        connections = []

        map.append({
            "id": 0,
            "name": "Vlastimila Hofmana",
            "PM2.5": "t",
            "d_PM2.5": "t",
            "x": 0,
            "y": 0
        })

        map.append({
            "id": 1,
            "name": "Leona Wyczółkowskiego",
            "PM2.5": "t",
            "d_PM2.5": "t",
            "x": 0,
            "y": 1
        })

        map.append({
            "id": 2,
            "name": "Aleje Trzech Wieszczów",
            "PM2.5": "t",
            "d_PM2.5": "f",
            "x": 1,
            "y": 0
        })

        map.append({
            "id": 3,
            "name": "Wiedeńska",
            "PM2.5": "f",
            "d_PM2.5": "t",
            "x": 1,
            "y": 1
        })

        map.append({
            "id": 4,
            "name": "Przybyszewskiego 56",
            "PM2.5": "u",
            "d_PM2.5": "f",
            "x": 1,
            "y": 2
        })

        map.append({
            "id": 5,
            "name": "Studencka",
            "PM2.5": "u",
            "d_PM2.5": "u",
            "x": 2,
            "y": 0
        })

        map.append({
            "id": 6,
            "name": "Na Błonie",
            "PM2.5": "t",
            "d_PM2.5": "f",
            "x": 3,
            "y": 1
        })

        map.append({
            "id": 7,
            "name": "osiedle Złota Podkowa",
            "PM2.5": "t",
            "d_PM2.5": "f",
            "x": 3,
            "y": 2
        })

        map.append({
            "id": 8,
            "name": "aleja Juliusza Słowackiego",
            "PM2.5": "f",
            "d_PM2.5": "f",
            "x": 2,
            "y": 1
        })

        connections.append([0, 1])
        connections.append([1, 4])
        connections.append([2, 5])
        connections.append([2, 5])
        connections.append([3, 4])
        connections.append([3, 8])
        connections.append([5, 6])
        connections.append([5, 8])
        connections.append([6, 7])

        return map, connections

    def _write_file_header(self):
        self._results_file.write(f'----------------Pollution Model----------------\n')
        self._results_file.write(f'{datetime.datetime.now()}\n')
        self._results_file.write(f"Drones: {self.__n_agent}\n")
        self._results_file.write(f"Energies: {self.__energies}\n")
        self._results_file.write(f"Map: {self.__map}\n")
        self._results_file.write(f"Connections: {self.__connections}\n")
        self._results_file.write(f'Map size: {len(self.__map)}\n')
        self._results_file.write(f'Radius: {self.__radius}\n')
        self._results_file.write(f'Selected place: {self.__selected_place}\n')
        self._results_file.write(f'First place id: {self.__first_place_id}\n')

    def _generate_model(self):
        start = time.perf_counter()
        self._model = PollutionModel(self.__map, self.__connections, self.__n_agent, self.__energies, self.__radius,
                                         self.__first_place_id)
        stop = time.perf_counter()
        tgen = stop - start

        # pollution_model.print_states()

        self._results_file.write(f'Tgen: {tgen}\n')
        self._results_file.write(f'Number of states: {len(self._model.states)}\n')

    def _run_mc(self):
        phi1_l = "<<>> F polnew_0"
        phi1_r = "<<0>> F polnew_0"
        phi2 = self.generate_new_formula2(self.__n_agent, self.__selected_place)

        formula_txt = phi2

        self._results_file.write(f"Formula: {formula_txt}\n")

        print(formula_txt)
        props = list()
        for l in range(0, len(self.__map)):
            for a in range(0, self.__n_agent):
                props.append("pol" + str(l))
                props.append("polE" + str(l))
                props.append("loc" + str(l))
                props.append("polD" + str(l))
        props.append('locA')
        props.append('polnew')
        self._model.model.props = props
        const = "t td tg f fd fg u"
        atlparser = mvatl_parser.AlternatingTimeTemporalLogicParser(const, props)
        formula = atlparser.parse(formula_txt)
        print("Formula:", formula)
        start = time.perf_counter()
        self.__result = self._model.model.interpreter(formula, 0)
        stop = time.perf_counter()
        tverif = stop - start
        print(str(self.__result))

        self._results_file.write(f"Result: {self.__result}\n")
        self._results_file.write(f'Tverif: {tverif}\n')
        self._results_file.write("\n")

    def _write_result(self):
        pass

    # Syntax for propositions:
    # Polution prop -> poll the list of size no_drones with (the second) l as the location number
    # In formula -> poll_d with l location and d drone (ex: pol3 = [t,f,t] and pol3_1 = f)
    # Location prop -> locl the list of size no_drones with (the second) l as the location number
    # In formula -> locl_d with l location and d drone (ex: loc3 = [t,f,t] and loc3_1 = f)
    def generate_new_formula2(self, no_drones, location_id):
        coal = ""
        for d in range(0, no_drones):
            coal += str(d)
            if d != no_drones - 1:
                coal += ","

        result = f"<<{coal}>> F "
        lst = list()
        for d in range(0, no_drones):
            lst2 = list()
            lst2.append(f"(loc{location_id}_{d} & polnew_{d})")
            lst.append(lst2)

        result += self.cformula2string(lst, 0)
        return result

    def dformula2string(self, disj, i):
        if i == len(disj) - 1:
            return disj[i]
        return "(" + disj[i] + " | " + self.dformula2string(disj, i + 1) + ")"

    def cformula2string(self, conj, i):
        if i == len(conj) - 1:
            return self.dformula2string(conj[i], 0)
        return "(" + self.dformula2string(conj[i], 0) + " | " + self.cformula2string(conj, i + 1) + ")"


# cracow_pollution_model_exp = CracowPollutionModelExp(1, 1, 1, 7, 5)
# cracow_pollution_model_exp.run_experiments()