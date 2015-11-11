import FileModule
from Config import SolversDescriptions


########################################################################################################################
class ParametersModule(object):
    def __init__(self,
                 solver_file_path,
                 reports_folder_path,
                 threads_number,
                 handled_parameters_indexes,
                 # количество = количеству обрабатываемых активных параметров (лишних значений нет)
                 start_parameters_values):
        self.__solver_name = FileModule.get_file_name(solver_file_path)
        self.__solver_file_path = solver_file_path
        self.__next_cnf_index = 0
        self.__current_cnf = ''
        self.__cnf_files_paths = FileModule.get_cnf_file_path()
        self.__reports_folder_path = reports_folder_path
        self.__handled_parameters_indexes = handled_parameters_indexes
        # start_parameters_values это массив, элементы которого могут быть:
        # bool значением для параметра типа BOOL
        # double значением для параметра типа RANGE
        self.__start_parameters_values = start_parameters_values
        self.__parameters_templates = SolversDescriptions.get_handled_parameters_template(self.__solver_name,
                                                                                          threads_number,
                                                                                          handled_parameters_indexes)

    def has_new_parameters_list(self):
        return self.__next_cnf_index < len(self.__cnf_files_paths)

    def get_parameters_list(self):
        self.__current_cnf = self.__cnf_files_paths[self.__next_cnf_index]
        self.__next_cnf_index += 1
        result = list()
        result.append(self.__solver_file_path)  # первый параметр - это всегда путь до решателя
        active_parameters_index = 0
        for system_parameter_template in self.__parameters_templates:
            to_concat = system_parameter_template[0]
            parameter_string = ''
            for concrete_parameter_template in system_parameter_template[1]:
                if concrete_parameter_template[0] == 'BOOL':
                    if self.__start_parameters_values[active_parameters_index]:
                        parameter_sub_string = concrete_parameter_template[1]
                    else:
                        parameter_sub_string = concrete_parameter_template[2]
                    active_parameters_index += 1
                elif concrete_parameter_template[0] == 'RANGE':
                    parameter_sub_string = str(self.__start_parameters_values[active_parameters_index])
                    active_parameters_index += 1
                elif concrete_parameter_template[0] == 'STRING':
                    parameter_sub_string = concrete_parameter_template[1]
                elif concrete_parameter_template[0] == 'CNF':
                    parameter_sub_string = self.__current_cnf
                elif concrete_parameter_template[0] == 'OUTPUT':
                    parameter_sub_string = self.__reports_folder_path + self.__create_output_file_name()
                else:
                    raise RuntimeError("ParametersModule.get_parameters_list: invalid type of parameter.")
                if len(parameter_sub_string) != 0:
                    if to_concat:
                        parameter_string += parameter_sub_string
                    else:
                        result.append(parameter_sub_string)
            if len(parameter_string) != 0:
                if to_concat:
                    result.append(parameter_string)
        return result

    def get_last_cnf_file_path(self):
        return self.__current_cnf

    def get_progress_string(self):
        return str(self.__next_cnf_index) + "/" + str(len(self.__cnf_files_paths))

# ----------------------------------------------------------------------------------------------------------------------
    def __create_output_file_name(self):
        return FileModule.get_file_name(self.__current_cnf)