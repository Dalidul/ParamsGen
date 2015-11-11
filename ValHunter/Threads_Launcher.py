from ParametersModule import ParametersModule
import multiprocessing
import subprocess
import time


########################################################################################################################
class ThreadsLauncher(object):
    CALCULATE_TUPLE = -2
    IGNORE_TUPLE = -3

    def __init__(self,
                 parameters_module,
                 threads_number,
                 solvers_timeout,
                 sleeping_time,
                 check_params_callback,
                 results_handler_callback,
                 data_saver_callback):
        self.__parameters_module = parameters_module
        isinstance(self.__parameters_module, ParametersModule)
        self.__threads_number = threads_number
        self.__solvers_timeout = solvers_timeout
        self.__sleeping_time = sleeping_time
        self.__check_params_callback = check_params_callback
        self.__results_handler_callback = results_handler_callback
        self.__data_saver_callback = data_saver_callback

    def run(self):
        working_instances_number = 0
        list_of_working_instances = list()  # contains tuples: (solver_instance, output_pipe, parameters_values)
        while True:
            if (working_instances_number < self.__threads_number) \
                    and self.__parameters_module.has_new_parameters_list():
                parameters_list = self.__parameters_module.get_parameters_list()
                parameters_values = self.__parameters_module.get_last_handled_parameters_values()
                status = self.__check_params_callback(parameters_values)
                if status == ThreadsLauncher.CALCULATE_TUPLE:
                    #print("Run instance: " + self.__parameters_module.get_progress_string() +
                    #      " : " + str(parameters_values))
                    self.__run_solver_instance(list_of_working_instances,
                                               parameters_list,
                                               parameters_values)
                    working_instances_number += 1
                elif status == ThreadsLauncher.IGNORE_TUPLE:
                    pass
                else:
                    raise RuntimeError("ThreadsLauncher.run: invalid parameters values tuple status.")
            elif working_instances_number == 0:
                break
            working_instances_number = self.__check_instances_on_finish(list_of_working_instances,
                                                                        working_instances_number)
            if working_instances_number >= self.__threads_number:
                time.sleep(self.__sleeping_time)
            elif not self.__parameters_module.has_new_parameters_list():
                time.sleep(self.__sleeping_time)

# ----------------------------------------------------------------------------------------------------------------------
    def __check_instances_on_finish(self, list_of_working_instances, working_instances_number):
        instances_to_remove = list()
        # list_of_working_instances contains: (solver_instance, output_pipe, parameters_values)
        for instance in list_of_working_instances:
            solver_instance = instance[0]
            output_pipe = instance[1]
            parameters_values = instance[2]
            if not solver_instance.is_alive():
                working_instances_number -= 1
                if output_pipe.poll():
                    time_of_solving, output_data = instance[1].recv()
                    output_file_name = self.__parameters_module.get_parameters_str(parameters_values)
                    self.__data_saver_callback(output_file_name, output_data)
                    self.__results_handler_callback(parameters_values, time_of_solving)
                instances_to_remove.append(instance)
        for instance in instances_to_remove:
            list_of_working_instances.remove(instance)
        return working_instances_number

    def __run_solver_instance(self,
                              list_of_working_instances,
                              parameters_list,
                              parameters_values):
        out_connection, in_connection = multiprocessing.Pipe()
        instance_of_solver = multiprocessing. \
            Process(target=ThreadsLauncher.__run_solver, args=(parameters_list, in_connection, self.__solvers_timeout))
        instance_of_solver.start()
        list_of_working_instances.append((instance_of_solver, out_connection, parameters_values))

    @staticmethod
    def __run_solver(parameters_list, data_pipe, time_limit):
        sleep_time = int(time_limit / 30)
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


########################################################################################################################
def run_solver(parameters_list):
    system_process_of_solver = subprocess.Popen(parameters_list, stdout=subprocess.PIPE)
    start_time = time.time()
    system_process_of_solver.wait()
    time_delta = time.time() - start_time
    return time_delta
