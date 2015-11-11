import ExperimentDescription
import FileModule
import Config
from Config import SolversDescriptions
from decimal import Decimal


class UI(object):
    def main_dialog(self):
        greeting_text = 'ValHunter'
        print(greeting_text)
        FileModule.init_folders()
        print('Choose type of experiment:')
        experiments_names = ExperimentDescription.get_list_of_experiments_names()
        attempt_index = 0
        selected_index = -1
        for index, experiment_name in enumerate(experiments_names):
            print("    {0}) {1}".format(index+1, experiment_name))
        while attempt_index < 3:
            answer_string = input('Input number of experiment type: ')
            try:
                selected_index = int(answer_string)-1
                if selected_index < len(experiments_names):
                    break
            except:
                pass
            attempt_index += 1
            print('Invalid experiment index. Please, try again.')
        if attempt_index == 3:
            exit()
        else:
            self.__request_general_input_data()
            self.__request_specific_input_data()
            self.__run_experiment(experiments_names[selected_index])

# ----------------------------------------------------------------------------------------------------------------------
    def __request_general_input_data(self):
        solver_name = input('Choose index of minisat subtype: \n'
                            '    1) minisat_core\n'
                            '    2) minisat_simp\n'
                            '    3) pmcsat\n'
                            '    4) glucored+march_release\n'
                            '    5) glucan_static\n'
                            '    6) mipisat\n'
                            '    7) minisat_ClauseSplit\n'
        )
        if (solver_name == '1') or (solver_name == 'minisat_core'):
            solver_name = 'minisat_core'
        elif (solver_name == '2') or (solver_name == 'minisat_simp'):
            solver_name = 'minisat_simp'
        elif (solver_name == '3') or (solver_name == 'pmcsat'):
            solver_name = 'pmcsat'
        elif (solver_name == '4') or (solver_name == 'glucored+march_release'):
            solver_name = 'glucored+march_release'
        elif (solver_name == '5') or (solver_name == 'glucan_static'):
            solver_name = 'glucan_static'
        elif (solver_name == '6') or (solver_name == 'mipisat'):
            solver_name = 'mipisat'
        elif (solver_name == '7') or (solver_name == 'minisat_ClauseSplit'):
            solver_name = 'minisat_ClauseSplit'
        else:
            print('Error: Invalid minisat subtype.')
            exit()
        if not FileModule.solver_exist(solver_name):
            print('Error: Solver file does not exist.')
            exit()
        # general ---------------
        self.__solver_file_path = FileModule.get_solver_file_path(solver_name)
        self.__cnf_file_path = FileModule.get_cnf_file_path()
        if len(self.__cnf_file_path) == 0:
            print('Error: Multiple cnf files in cnf folder.')
            exit()
        self.__root_experiments_path = Config.Filepaths.RESULTS_FOLDER
        start_file_name = input('Input start values file name: ')
        self.__start_parameters_values_file_path = Config.Filepaths.START_VALUES_FOLDER + '/' + start_file_name
        if not FileModule.file_exist(self.__start_parameters_values_file_path):
            print('File does not exist.')
            exit()
        self.__max_threads_number = Config.Defaults.USED_CORES_NUMBER
        parameters_templates = SolversDescriptions.get_parameters_template(solver_name, self.__max_threads_number)
        print('Choose handled parameters indexes (or just push ENTER for choose all):')
        for index, parameter in enumerate(parameters_templates):
            print('    ' + str(index) + ') ' + str(parameter))
        handled_indexes_string = input('(separated by commas): ')
        handled_indexes_string = handled_indexes_string.replace(' ', '')
        if len(handled_indexes_string) == 0:
            self.__handled_parameters_indexes = range(len(parameters_templates))
        else:
            self.__handled_parameters_indexes = list()
            for index_string in handled_indexes_string.split(','):
                self.__handled_parameters_indexes.append(int(index_string))
        self.__experiment_name = input('Input experiment name (optional): ')

    def __request_specific_input_data(self):
        try:
            self.__max_delta = Decimal(input('Input max delta deviation: '))
            self.__max_hamming_distance = Decimal(input('Input max hamming distance: '))
            self.__restarts_number = int(input('Input restarts number: '))
        except:
            print('Error: invalid value.')
            exit()

    def __run_experiment(self, experiment_type_name):
        if experiment_type_name == 'SimpleExperiment':
            experiment = ExperimentDescription.SimpleExperiment(self.__solver_file_path,
                                                                       self.__cnf_file_path,
                                                                       self.__root_experiments_path,
                                                                       self.__start_parameters_values_file_path,
                                                                       self.__max_delta,
                                                                       self.__max_hamming_distance,
                                                                       self.__restarts_number,
                                                                       self.__max_threads_number,
                                                                       self.__handled_parameters_indexes,
                                                                       self.__experiment_name)
            experiment.run()
        elif experiment_type_name == 'TabuExperiment':
            experiment = ExperimentDescription.TabuExperiment(self.__solver_file_path,
                                                                     self.__cnf_file_path,
                                                                     self.__root_experiments_path,
                                                                     self.__start_parameters_values_file_path,
                                                                     self.__max_delta,
                                                                     self.__max_hamming_distance,
                                                                     self.__restarts_number,
                                                                     self.__max_threads_number,
                                                                     self.__handled_parameters_indexes,
                                                                     self.__experiment_name)
            experiment.run()
        elif experiment_type_name == 'AnnealingExperiment':
            experiment = ExperimentDescription.AnnealingExperiment(self.__solver_file_path,
                                                                          self.__cnf_file_path,
                                                                          self.__root_experiments_path,
                                                                          self.__start_parameters_values_file_path,
                                                                          self.__max_delta,
                                                                          self.__max_hamming_distance,
                                                                          self.__restarts_number,
                                                                          self.__max_threads_number,
                                                                          self.__handled_parameters_indexes,
                                                                          self.__experiment_name)
            experiment.run()
        else:
            raise RuntimeError('UI.__run_experiment: invalid type of experiment.')