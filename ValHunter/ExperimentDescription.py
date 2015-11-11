import os
import FileModule
import time
from ParametersModule import ParametersModule
from ParametersModule import RandomParametersModule
from Config import Defaults
from Config import SolversDescriptions
import Threads_Launcher
from Threads_Launcher import ThreadsLauncher
import functools
import TabuModule
from decimal import Decimal
import random
import math


def get_list_of_experiments_names():
    return 'SimpleExperiment', 'TabuExperiment', 'AnnealingExperiment'


########################################################################################################################
class ExperimentDescription(object):
    def __init__(self,
                 solver_file_path,
                 cnf_file_path,
                 root_experiments_path,
                 start_parameters_values_file_path,
                 handled_parameters_indexes,
                 max_threads_number,
                 experiment_type_name,
                 experiment_name=''):
        if not os.path.exists(solver_file_path):
            raise RuntimeError('ExperimentDescription.__init__: solver file is not found.')
        if not os.path.exists(cnf_file_path):
            raise RuntimeError('ExperimentDescription.__init__: cnf file is not found.')
        if not os.path.exists(root_experiments_path):
            raise RuntimeError('ExperimentDescription.__init__: results root directory is not found.')
        if not os.path.exists(start_parameters_values_file_path):
            raise RuntimeError('ExperimentDescription.__init__: start parameters values file is not found.')
        self._solver_file_path = solver_file_path
        self._cnf_file_path = cnf_file_path
        if root_experiments_path[len(root_experiments_path)-1] != '/':
            self._root_experiments_path = root_experiments_path + '/'
        else:
            self._root_experiments_path = root_experiments_path
        self._start_parameters_values_file_path = start_parameters_values_file_path
        self._new_start_parameters_values_file_path = ""
        self._handled_parameters_indexes = handled_parameters_indexes
        self._max_threads_number = max_threads_number
        self._experiment_name = experiment_name
        self._all_experiments_conducted = False
        self._THREAD_LAUNCHER_SLEEPING_TIME = 2
        self._experiment_type_name = experiment_type_name
        self._time_of_start = -1

    def run(self):
        self._time_of_start = time.time()
        sub_experiment_index = 1
        sub_experiments_times = list()
        sub_experiment_start_time = time.time()
        while self._start_sub_experiment():
            print("Iteration №" + str(sub_experiment_index) + " time: " + str(time.time()-sub_experiment_start_time))
            sub_experiments_times.append(str(time.time()-sub_experiment_start_time))
            sub_experiment_index += 1
            sub_experiment_start_time = time.time()
        last_iter_time = time.time()-sub_experiment_start_time
        if last_iter_time > 1:
            print("Iteration №" + str(sub_experiment_index) + " time: " + str(last_iter_time))
            sub_experiments_times.append(str(last_iter_time))
        self._process_results(sub_experiments_times)

    def get_solver_file_path(self):
        return self._solver_file_path

    def get_solver_file_name(self):
        return FileModule.get_file_name(self._solver_file_path)

    def get_cnf_file_path(self):
        return self._cnf_file_path

    def get_root_experiments_path(self):
        return self._root_experiments_path

    def get_start_parameters_values(self):
        start_values_generator = StartValues(self.get_solver_file_name(),
                                             self._handled_parameters_indexes,
                                             self._start_parameters_values_file_path)
        return start_values_generator.get_start_values()

    def start_new_experiment(self):
        if self._all_experiments_conducted:
            raise RuntimeError('ExperimentDescription.start_new_experiment: all experiments conducted.')

    @staticmethod
    def get_current_time_string():
        return time.strftime('%Y-%m-%d__%H-%M-%S')

# ----------------------------------------------------------------------------------------------------------------------
    def _start_sub_experiment(self):
        raise RuntimeError('ExperimentDescription.__start_sub_experiment: abstract method.')

    def _process_results(self, sub_experiments_times):
        raise RuntimeError('ExperimentDescription._process_results: abstract method.')

    def _save_solver_output_data(self, reports_folder_path, output_file_name, output_data):
        pass
        #FileModule.create_file(reports_folder_path + output_file_name, output_data)


########################################################################################################################
class SimpleExperiment(ExperimentDescription):
    def __init__(self,
                 solver_file_path,
                 cnf_file_path,
                 root_experiments_path,
                 start_parameters_values_file_path,
                 max_delta,
                 max_hamming_distance,
                 restarts_number,
                 max_threads_number,
                 handled_parameters_indexes,
                 experiment_name=''):
        ExperimentDescription.__init__(self,
                                       solver_file_path,
                                       cnf_file_path,
                                       root_experiments_path,
                                       start_parameters_values_file_path,
                                       handled_parameters_indexes,
                                       max_threads_number,
                                       experiment_name)
        self._max_delta = max_delta
        self._max_hamming_distance = max_hamming_distance
        self._restarts_number = restarts_number
        self._number_of_experiments_produced = 0
        self._start_parameters_values = self.get_start_parameters_values()
        experiment_name_folder = (self._experiment_name + '/') if len(self._experiment_name) != 0 else ""
        solver_name = FileModule.get_file_name(self._solver_file_path)
        cnf_name = FileModule.get_file_name(self._cnf_file_path)
        self._reports_folder_path = self._root_experiments_path \
            + "SimpleExperiment/" \
            + experiment_name_folder \
            + solver_name + '/' \
            + cnf_name + '/' \
            + ExperimentDescription.get_current_time_string() + '/'
        FileModule.create_folder(self._reports_folder_path)
        print("Calculating solver timeout...")
        self._solver_timeout = self._get_solver_timeout()
        print("Solver timeout = " + str(self._solver_timeout) + " seconds")
        # (parameters_values, time)
        self._best_results = list()
        self._best_results.append((self._get_default_parameters_values(), self._solver_timeout))

# ----------------------------------------------------------------------------------------------------------------------
    def _start_sub_experiment(self):
        self._best_results.append((None, None))
        if self._best_results[len(self._best_results)-2][0] is not None:
            start_params_vals = self._best_results[len(self._best_results)-2][0]
            start_values_generator = StartValues(self.get_solver_file_name(),
                                                 self._handled_parameters_indexes,
                                                 self._start_parameters_values_file_path)
            self._start_parameters_values = start_values_generator.create_start_values(start_params_vals)
        else:
            print("Local minimum finded.")
            return False
        parameters_module = ParametersModule(self._solver_file_path,
                                             self._cnf_file_path,
                                             self._reports_folder_path,
                                             self._max_threads_number,
                                             #self._max_threads_number/SolversDescriptions.get_solver_threads_number(FileModule.get_file_name(self._solver_file_path), self._max_threads_number),
                                             self._handled_parameters_indexes,
                                             self._start_parameters_values,
                                             self._max_delta,
                                             self._max_hamming_distance)
        parameters_module.skip_start_values()
        thread_launcher = ThreadsLauncher(parameters_module,
                                          self._max_threads_number,
                                          self._solver_timeout,
                                          self._THREAD_LAUNCHER_SLEEPING_TIME,
                                          SimpleExperiment.__check_params,
                                          functools.partial(SimpleExperiment.__handle_result,
                                                            self),
                                          functools.partial(SimpleExperiment._save_solver_output_data,
                                                            self,
                                                            self._reports_folder_path))
        thread_launcher.run()
        self._number_of_experiments_produced += 1
        best_time = self._best_results[len(self._best_results)-1][1]
        print("Iteration №" + str(self._number_of_experiments_produced) + ". Best time = "
              + str(best_time) + ". Parameters values: "
              + str(self._best_results[len(self._best_results)-1][0]))
        self._solver_timeout = best_time
        return self._number_of_experiments_produced < self._restarts_number

    @staticmethod
    def __check_params(parameters_values):
        return Threads_Launcher.ThreadsLauncher.CALCULATE_TUPLE

    def __handle_result(self, parameters_values, solving_time):
        # отсев запусков с обрывом рассчётов (-1) и запусков, на которых
        # решатель выплюнул ошибку (чрезвычайно малое время решения)
        print(solving_time)
        if solving_time > 0.2:
            if self._best_results[len(self._best_results)-1][0] is None:
                self._best_results[len(self._best_results)-1] = (parameters_values, solving_time)
            else:
                if self._best_results[len(self._best_results)-1][1] >= solving_time:
                    self._best_results[len(self._best_results)-1] = (parameters_values, solving_time)

    def _process_results(self, sub_experiments_times):
        results_file_data = "Time: " + str(time.time()-self._time_of_start) + "\n"
        index = 0
        for i in range(self._number_of_experiments_produced):
            work_time = sub_experiments_times[i]
            parameters_values = self._best_results[i][0]
            time_of_solving = self._best_results[i][1]
            if index == 0:
                results_file_data += "On defaults. Best time = " \
                                     + str(time_of_solving) + ".  Parameters values: " + str(parameters_values) + "\n"
            else:
                if time_of_solving is None:
                    break
                results_file_data += "Iteration №" + str(index) + ". Summary time = " + str(work_time) + ". Best time = " \
                                     + str(time_of_solving) + ". Parameters values: " + str(parameters_values) + "\n"
            index += 1
        FileModule.create_file(self._reports_folder_path + 'RESULTS.txt', results_file_data)

    def _get_solver_timeout(self):
        parameters_module = ParametersModule(self._solver_file_path,
                                             self._cnf_file_path,
                                             self._reports_folder_path,
                                             self._max_threads_number,
                                             self._handled_parameters_indexes,
                                             self._start_parameters_values,
                                             0,
                                             0)
        return Threads_Launcher.run_solver(parameters_module.get_parameters_list())

    def _get_default_parameters_values(self):
        parameters_module = ParametersModule(self._solver_file_path,
                                             self._cnf_file_path,
                                             self._reports_folder_path,
                                             self._max_threads_number,
                                             self._handled_parameters_indexes,
                                             self._start_parameters_values,
                                             0,
                                             0)
        parameters_module.get_parameters_list()
        return parameters_module.get_last_handled_parameters_values()


########################################################################################################################
class TabuExperiment(SimpleExperiment):
    def __init__(self,
                 solver_file_path,
                 cnf_file_path,
                 root_experiments_path,
                 start_parameters_values_file_path,
                 max_delta,
                 max_hamming_distance,
                 restarts_number,
                 max_threads_number,
                 handled_parameters_indexes,
                 experiment_name=''):
        SimpleExperiment.__init__(self,
                                  solver_file_path,
                                  cnf_file_path,
                                  root_experiments_path,
                                  start_parameters_values_file_path,
                                  max_delta,
                                  max_hamming_distance,
                                  restarts_number,
                                  max_threads_number,
                                  handled_parameters_indexes,
                                  experiment_name)
        self._tabu_module = TabuModule.TabuModule()
        self._tabued_number = 0

# ----------------------------------------------------------------------------------------------------------------------
    def _start_sub_experiment(self):
        self._tabued_number = 0
        self._best_results.append((None, None))
        if self._best_results[len(self._best_results)-2][0] is not None:
            start_params_vals = self._best_results[len(self._best_results)-2][0]
            start_values_generator = StartValues(self.get_solver_file_name(),
                                                 self._handled_parameters_indexes,
                                                 self._start_parameters_values_file_path)
            self._start_parameters_values = start_values_generator.create_start_values(start_params_vals)
        else:
            print("Local minimum found.")
            return False
        parameters_module = ParametersModule(self._solver_file_path,
                                             self._cnf_file_path,
                                             self._reports_folder_path,
                                             self._max_threads_number,
                                             self._handled_parameters_indexes,
                                             self._start_parameters_values,
                                             self._max_delta,
                                             self._max_hamming_distance)
        parameters_module.skip_start_values()
        if self._tabu_module.add_area(parameters_module.get_area()):
            thread_launcher = ThreadsLauncher(parameters_module,
                                              self._max_threads_number,
                                              self._solver_timeout,
                                              self._THREAD_LAUNCHER_SLEEPING_TIME,
                                              functools.partial(TabuExperiment._check_params_on_tabu,
                                                                self),
                                              functools.partial(TabuExperiment.__handle_result,
                                                                self),
                                              functools.partial(SimpleExperiment._save_solver_output_data,
                                                                self,
                                                                self._reports_folder_path))
            thread_launcher.run()
            self._number_of_experiments_produced += 1
            best_time = self._best_results[len(self._best_results)-1][1]
            print("Iteration №" + str(self._number_of_experiments_produced) + ". Best time = "
                  + str(best_time) + ". Parameters values: "
                  + str(self._best_results[len(self._best_results)-1][0]) + "\n"
                  + "Tabued number: " + str(self._tabued_number))
            self._solver_timeout = best_time
            return self._number_of_experiments_produced < self._restarts_number
        else:
            return False

    def _check_params_on_tabu(self, parameters_values):
        coords_vals = list()
        for parameter_value in parameters_values:
            if isinstance(parameter_value, bool):
                coords_vals.append(1 if parameter_value else 0)
            else:
                coords_vals.append(parameter_value)
        point = TabuModule.Point(coords_vals)
        point_solving_time = self._tabu_module.get_solving_time(point)
        if point_solving_time == TabuModule.Area.INVALID_TIME_VALUE:
            return Threads_Launcher.ThreadsLauncher.CALCULATE_TUPLE
        else:
            self._tabued_number += 1
            # print("Tuple " + str(parameters_values) + " is in tabu list: " + str(point_solving_time))
            return Threads_Launcher.ThreadsLauncher.IGNORE_TUPLE

    def __handle_result(self, parameters_values, solving_time):
        print(solving_time)
        coords_vals = list()
        for parameter_value in parameters_values:
            if isinstance(parameter_value, bool):
                coords_vals.append(1 if parameter_value else 0)
            else:
                coords_vals.append(parameter_value)
        point = TabuModule.Point(coords_vals)
        # отсев запусков с обрывом рассчётов (-1) и запусков, на которых
        # решатель выплюнул ошибку (чрезвычайно малое время решения)
        if solving_time > 0.2:
            self._tabu_module.set_solving_time(point, solving_time)
            if self._best_results[len(self._best_results)-1][0] is not None:
                if self._best_results[len(self._best_results)-1][1] >= solving_time:
                    self._best_results[len(self._best_results)-1] = (parameters_values, solving_time)
            else:
                self._best_results[len(self._best_results)-1] = (parameters_values, solving_time)
        else:
            self._tabu_module.set_solving_time(point, -1)


########################################################################################################################
class AnnealingExperiment(TabuExperiment):
    def __init__(self,
                 solver_file_path,
                 cnf_file_path,
                 root_experiments_path,
                 start_parameters_values_file_path,
                 max_delta,
                 max_hamming_distance,
                 restarts_number,
                 max_threads_number,
                 handled_parameters_indexes,
                 experiment_name=''):
        TabuExperiment.__init__(self,
                                solver_file_path,
                                cnf_file_path,
                                root_experiments_path,
                                start_parameters_values_file_path,
                                max_delta,
                                max_hamming_distance,
                                restarts_number,
                                max_threads_number,
                                handled_parameters_indexes,
                                experiment_name)
        self._thermometer = Thermometer(7)

# ----------------------------------------------------------------------------------------------------------------------
    def _start_sub_experiment(self):
        self._tabued_number = 0
        self._best_results.append((None, None))
        if len(self._best_results) >= 2:
            if self._best_results[len(self._best_results)-2][0] is not None:
                start_params_vals = self._best_results[len(self._best_results)-2][0]
                start_values_generator = StartValues(self.get_solver_file_name(),
                                                     self._handled_parameters_indexes,
                                                     self._start_parameters_values_file_path)
                self._start_parameters_values = start_values_generator.create_start_values(start_params_vals)
                self._solver_timeout = self._best_results[len(self._best_results)-2][1]
            else:
                print("Local minimum found.")
                return False
        parameters_module = ParametersModule(self._solver_file_path,
                                             self._cnf_file_path,
                                             self._reports_folder_path,
                                             self._max_threads_number,
                                             self._handled_parameters_indexes,
                                             self._start_parameters_values,
                                             self._max_delta,
                                             self._max_hamming_distance)
        parameters_module.skip_start_values()
        current_area = parameters_module.get_area()
        if self._tabu_module.add_area(current_area):
            thread_launcher = ThreadsLauncher(parameters_module,
                                              self._max_threads_number,
                                              self._solver_timeout,
                                              self._THREAD_LAUNCHER_SLEEPING_TIME,
                                              functools.partial(TabuExperiment._check_params_on_tabu,
                                                                self),
                                              functools.partial(AnnealingExperiment.__handle_result,
                                                                self),
                                              functools.partial(SimpleExperiment._save_solver_output_data,
                                                                self,
                                                                self._reports_folder_path))
            thread_launcher.run()
            self._number_of_experiments_produced += 1
            print("Iteration №" + str(self._number_of_experiments_produced) +
                  " .Tabued number: " + str(self._tabued_number))
        if self._best_results[len(self._best_results)-1][0] is None:
            self._find_random_point()
        return self._number_of_experiments_produced < self._restarts_number

    def __handle_result(self, parameters_values, solving_time):
        coords_vals = list()
        for parameter_value in parameters_values:
            if isinstance(parameter_value, bool):
                coords_vals.append(1 if parameter_value else 0)
            else:
                coords_vals.append(parameter_value)
        point = TabuModule.Point(coords_vals)
        # отсев запусков с обрывом рассчётов (-1) и запусков, на которых
        # решатель выплюнул ошибку (чрезвычайно малое время решения)
        if solving_time > 0.2:
            self._tabu_module.set_solving_time(point, solving_time)
            if self._best_results[len(self._best_results)-1][0] is not None:
                if self._best_results[len(self._best_results)-1][1] >= solving_time:
                    self._best_results[len(self._best_results)-1] = (parameters_values, solving_time)
            else:
                self._best_results[len(self._best_results)-1] = (parameters_values, solving_time)
        else:
            self._tabu_module.set_solving_time(point, -1)

    def _process_results(self, sub_experiments_times):
        results_file_data = "Time: " + str(time.time()-self._time_of_start) + "\n"
        index = 0
        best_of_the_best = self._best_results[0]
        for i in range(self._number_of_experiments_produced):
            work_time = sub_experiments_times[i]
            parameters_values = self._best_results[i][0]
            time_of_solving = self._best_results[i][1]
            if index == 0:
                results_file_data += "On defaults. Best time = " \
                                     + str(time_of_solving) + ".  Parameters values: " + str(parameters_values) + "\n"
            else:
                if time_of_solving is None:
                    break
                if best_of_the_best[1] > time_of_solving:
                    best_of_the_best = self._best_results[i]
                results_file_data += "Iteration №" + str(index) + ". Summary time = " + str(work_time) + ". Best time = " \
                                     + str(time_of_solving) + ". Parameters values: " + str(parameters_values) + "\n"
            index += 1
        results_file_data = "Best time = " + str(best_of_the_best[1]) + \
                            ". Parameters: " + str(best_of_the_best[0]) + "\n\n" + results_file_data
        FileModule.create_file(self._reports_folder_path + 'RESULTS.txt', results_file_data)

    def _find_random_point(self):
        random_parameters_module = RandomParametersModule(self._solver_file_path,
                                                          self._cnf_file_path,
                                                          self._reports_folder_path,
                                                          self._max_threads_number,
                                                          self._handled_parameters_indexes,
                                                          self._start_parameters_values,
                                                          10)
        thread_launcher = ThreadsLauncher(random_parameters_module,
                                          self._max_threads_number,
                                          # максимально допустимое время не более чем в 1.5 раза хуже стартового
                                          self._best_results[0][1]*1.5,
                                          self._THREAD_LAUNCHER_SLEEPING_TIME,
                                          functools.partial(AnnealingExperiment.__check_random_params_on_tabu,
                                                            self),
                                          functools.partial(AnnealingExperiment.__handle_random_result,
                                                            self,
                                                            random_parameters_module),
                                          functools.partial(SimpleExperiment._save_solver_output_data,
                                                            self,
                                                            self._reports_folder_path))
        thread_launcher.run()

    def __check_random_params_on_tabu(self, parameters_values):
        return Threads_Launcher.ThreadsLauncher.CALCULATE_TUPLE

    def __handle_random_result(self, random_parameters_module,  parameters_values, solving_time):
        # отсев запусков с обрывом рассчётов (-1) и запусков, на которых
        # решатель выплюнул ошибку (чрезвычайно малое время решения)
        if self._thermometer.get_val() <= 0:
            random_parameters_module.stop()
            return
        if solving_time > 0.2:
            print("НАЙДЕНО СНОСНОЕ ВРЕМЯ!!! " + str(solving_time) + "/"
                  + str(self._best_results[len(self._best_results)-2][1]))
            previous_point_time = self._best_results[len(self._best_results)-2][1]
            if solving_time <= previous_point_time:
                if self._best_results[len(self._best_results)-1][0] is None:
                    self._best_results[len(self._best_results)-1] = (parameters_values, solving_time)
                else:
                    if self._best_results[len(self._best_results)-1][1] > solving_time:
                        self._best_results[len(self._best_results)-1] = (parameters_values, solving_time)
                random_parameters_module.stop()
            else:
                probability = math.exp(-1*(solving_time-previous_point_time)/self._thermometer.get_val())
                rand_val = random.random()
                if rand_val <= probability:
                    if self._best_results[len(self._best_results)-1][0] is None:
                        self._best_results[len(self._best_results)-1] = (parameters_values, solving_time)
                    else:
                        if self._best_results[len(self._best_results)-1][1] > solving_time:
                            self._best_results[len(self._best_results)-1] = (parameters_values, solving_time)
                    print("Prob: " + str(rand_val)+"/"+str(probability) + " --- " + "(+)")
                    random_parameters_module.stop()
                else:
                    print("Prob: " + str(rand_val)+"/"+str(probability) + " --- " + "(-)")
        self._thermometer.cool()


########################################################################################################################
class Thermometer(object):
    def __init__(self, start_temperature):
        self.__temperature = start_temperature

    def get_val(self):
        return self.__temperature

    def cool(self):
        self.__temperature -= 0.08
        print("Cooled to " + str(self.__temperature) + " degrees")


########################################################################################################################
########################################################################################################################
class StartValues:
    def __init__(self, solver_name, handled_parameters_indexes, start_values_filepath=""):
        if solver_name not in Defaults.DEFAULT_PARAMETERS_VALUES:
            raise RuntimeError("StartValues:__init__: Invalid solver name.")
        else:
            self.__solver_name = solver_name
            self.__start_values_filepath = start_values_filepath
            self.__handled_parameters_indexes = handled_parameters_indexes

    def get_start_values(self):
        if len(self.__start_values_filepath) == 0:
            default_values = SolversDescriptions.get_default_parameters_values(self.__solver_name)
            return SolversDescriptions.get_start_parameters_values(self.__solver_name,
                                                                   self.__handled_parameters_indexes,
                                                                   default_values)
        else:
            read_values = self.__read_start_parameters()
            return SolversDescriptions.get_start_parameters_values(self.__solver_name,
                                                                   self.__handled_parameters_indexes,
                                                                   read_values)

    def create_start_values(self, pure_parameters_values):
        result = list()
        start_tuple = self.get_start_values()
        for i in range(len(pure_parameters_values)):
            if isinstance(start_tuple[i], bool):
                result.append(pure_parameters_values[i])
            else:
                result.append((pure_parameters_values[i], start_tuple[i][1]))
        return result


# ----------------------------------------------------------------------------------------------------------------------
    def __read_start_parameters(self, new_start_values_filepath=""):
        if new_start_values_filepath is not "":
            self.__start_values_filepath = new_start_values_filepath
            result = list()
            data = FileModule.read_file(self.__start_values_filepath)
            for line in str(data).split('\n'):
                line = line.replace(' ', '')
                line = line.replace('\t', '')
                if len(line) == 0:
                    continue
                words = line.split(',')
                if len(words) == 1:
                    if words[0].lower() in ['true', '1']:
                        result.append(True)
                    elif words[0].lower() in ['false', '0']:
                        result.append(False)
                    else:
                        raise RuntimeError('StartValues.__read_start_parameters: invalid start values bool line: ' + line)
                elif len(words) == 2:
                    range_val = list()
                    for val in words:
                        try:
                            range_val.append(Decimal(val))
                        except:
                            raise RuntimeError('StartValues.__read_start_parameters: invalid start values bool line: '
                                               + line)
                    result.append(range_val)
                else:
                    raise RuntimeError('StartValues.__read_start_parameters: invalid start values line: ' + line)
        else:
            result = Defaults.DEFAULT_PARAMETERS_VALUES[self.__solver_name]
        return result