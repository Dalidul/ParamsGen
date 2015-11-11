from ParametersModule import ParametersModule
import FileModule
import multiprocessing
import subprocess
import time


########################################################################################################################
class ThreadsLauncher(object):
    def __init__(self, parameters_module, threads_number, solvers_timeout, sleeping_time, data_saver_callback):
        self.__parameters_module = parameters_module
        isinstance(self.__parameters_module, ParametersModule)
        self.__threads_number = threads_number
        self.__solvers_timeout = solvers_timeout
        self.__sleeping_time = sleeping_time
        self.__data_saver_callback = data_saver_callback
        self.__results = list()  # contains tuples: (cnf_name, time_of_solving)

    def run(self):
        working_instances_number = 0
        list_of_working_instances = list()  # contains tuples: (solver_instance, output_pipe, cnf_name)
        while True:
            if self.__parameters_module.has_new_parameters_list() and \
                    (working_instances_number < self.__threads_number):
                parameters_list = self.__parameters_module.get_parameters_list()
                cnf_name = FileModule.get_file_name(self.__parameters_module.get_last_cnf_file_path())
                print("Run instance: " + self.__parameters_module.get_progress_string())
                self.__run_solver_instance(list_of_working_instances,
                                           parameters_list,
                                           cnf_name)
                working_instances_number += 1
            elif working_instances_number == 0:
                break
            working_instances_number = self. \
                __check_instances_on_finish(list_of_working_instances, working_instances_number)
            time.sleep(self.__sleeping_time)

    def get_results(self):
        return self.__results  # contains tuples: (parameters_values, time_of_solving)

# ----------------------------------------------------------------------------------------------------------------------
    def __check_instances_on_finish(self, list_of_working_instances, working_instances_number):
        instances_to_remove = list()
        # list_of_working_instances contains: (solver_instance, output_pipe, parameters_values)
        for instance in list_of_working_instances:
            solver_instance = instance[0]
            output_pipe = instance[1]
            cnf_name = instance[2]
            if not solver_instance.is_alive():
                working_instances_number -= 1
                if output_pipe.poll():
                    time_of_solving, output_data = instance[1].recv()
                    self.__data_saver_callback(cnf_name, output_data)
                    self.__results.append((cnf_name, time_of_solving))
                instances_to_remove.append(instance)
        for instance in instances_to_remove:
            list_of_working_instances.remove(instance)
        return working_instances_number

    def __run_solver_instance(self,
                              list_of_working_instances,
                              parameters_list,
                              cnf_name):
        out_connection, in_connection = multiprocessing.Pipe()
        instance_of_solver = multiprocessing. \
            Process(target=ThreadsLauncher.__run_solver, args=(parameters_list, in_connection, self.__solvers_timeout))
        instance_of_solver.start()
        list_of_working_instances.append((instance_of_solver, out_connection, cnf_name))

    @staticmethod
    def __run_solver(parameters_list, data_pipe, time_limit):
        sleep_time = int(1)
        system_process_of_solver = subprocess.Popen(parameters_list, stdout=subprocess.PIPE)
        start_time = time.time()
        data = ""
        time_delta = -1
        while True:
            if system_process_of_solver.poll() is not None:
                data = system_process_of_solver.stdout.read().decode('utf-8')
                time_delta = time.time() - start_time
                break
            else:
                if time.time() > start_time + time_limit:
                    system_process_of_solver.kill()
                    break
            time.sleep(sleep_time)
        data_pipe.send((time_delta, data))
