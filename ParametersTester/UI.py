import FileModule
import Config
from Config import SolversDescriptions
from Threads_Launcher import ThreadsLauncher
from ParametersModule import ParametersModule
import functools
from decimal import Decimal


class UI(object):
    def main_dialog(self):
        greeting_text = 'ParametersTester'
        print(greeting_text)
        FileModule.init_folders()
        solver_name = UI.__request_solver_name()
        timeout = UI.__request_solving_timeout()
        handled_parameters = UI.__request_handled_parameters(solver_name, Config.Defaults.USED_CORES_NUMBER)
        active_parameters_values = UI.__request_parameters_values(SolversDescriptions.get_active_parameters_indexes(solver_name, handled_parameters))
            #len(SolversDescriptions.get_active(solver_name, handled_parameters)))
        UI.__run_solver(solver_name, timeout, handled_parameters, active_parameters_values)


# ----------------------------------------------------------------------------------------------------------------------
    @staticmethod
    def __is_int(s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    @staticmethod
    def __is_number(s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    @staticmethod
    def __request_solver_name():
        solvers_names = FileModule.get_solvers_names()
        output_string = 'Choose solver (index or name): \n'
        for index, solver_name in enumerate(solvers_names):
            output_string += '\t' + str(index+1) + ') ' + solver_name + '\n'
        user_input = input(output_string)
        if UI.__is_int(user_input):
            solver_index = int(user_input)-1
            if (solver_index >= 0) and (solver_index < len(solvers_names)):
                return solvers_names[solver_index]
            else:
                print('Error: Invalid solver index.')
                exit()
        elif solvers_names.count(user_input) == 1:
            return user_input
        else:
            print('Error: Invalid solver name.')
            exit()

    @staticmethod
    def __request_solving_timeout():
        user_input = input('Input solving timeout (default = ' + str(Config.Defaults.SOLVING_TIMEOUT) + ' seconds): ')
        if len(user_input) == 0:
            return Config.Defaults.SOLVING_TIMEOUT
        if UI.__is_number(user_input):
            return float(user_input)
        else:
            print('Error: Incorrect timeout value.')
            exit()

    @staticmethod
    def __request_handled_parameters(solver_name, threads_number):
        parameters_templates = SolversDescriptions.get_parameters_template(solver_name, threads_number)
        print('Choose handled parameters indexes (or just push ENTER for choose all):')
        for index, parameter in enumerate(parameters_templates):
            print('    ' + str(index) + ') ' + str(parameter))
        handled_indexes_string = input('(separated by commas): ')
        handled_indexes_string = handled_indexes_string.replace(' ', '')
        if len(handled_indexes_string) == 0:
            return range(len(parameters_templates))
        else:
            handled_parameters_indexes = list()
            for index_string in handled_indexes_string.split(','):
                handled_parameters_indexes.append(int(index_string))
            return handled_parameters_indexes

    @staticmethod
    def __request_parameters_values(active_parameters_indexes):
        values = list()
        print('Input parameters values:')
        for index in active_parameters_indexes:
            val = input('\t' + str(index) + ': ')
            if val == "True":
                values.append(True)
            elif val == "False":
                values.append(False)
            else:
                values.append(Decimal(val))
        return values

    @staticmethod
    def __run_solver(solver_name, timeout, handled_parameters, active_parameters_values):
        pm = ParametersModule(FileModule.get_solver_file_path(solver_name),
                              Config.Filepaths.RESULTS_FOLDER,
                              Config.Defaults.USED_CORES_NUMBER,
                              handled_parameters,
                              active_parameters_values)
        tl = ThreadsLauncher(pm, Config.Defaults.USED_CORES_NUMBER, timeout, 0.5,
                             functools.partial(UI.__save_solver_output_data,
                                               Config.Filepaths.RESULTS_FOLDER))
        tl.run()
        UI.__process_results(tl.get_results(), timeout)

    @staticmethod
    def __save_solver_output_data(reports_folder_path, output_file_name, output_data):
        FileModule.create_file(reports_folder_path + output_file_name, output_data)

    @staticmethod
    def __process_results(results, timeout):  # results contains tuples: (cnf_name, time_of_solving)
        results_file_data = 'Max time of solving: ' + str(timeout) + ' seconds\n'
        for parameters_values, time_of_solving in results:
            results_file_data += parameters_values + ': ' + str(time_of_solving) + '\n'
        print('\n'+results_file_data)
        FileModule.create_file(Config.Filepaths.RESULTS_FOLDER + '/RESULTS.txt', results_file_data)