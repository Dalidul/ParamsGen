from ParametersValuesFactory import BoolParameter
from ParametersValuesFactory import RangeParameter
from ParametersValuesFactory import RandomParametersValuesFactory
from ParametersValuesFactory import ParametersValuesFactory
import FileModule
from Config import SolversDescriptions
from TabuModule import Area


########################################################################################################################
class RandomParametersModule(object):
    def __init__(self,
                 solver_file_path,
                 cnf_file_path,
                 reports_folder_path,
                 threads_number,
                 handled_parameters_indexes,
                 start_parameters_values,
                 max_delta):
        self.__solver_name = FileModule.get_file_name(solver_file_path)
        self.__solver_file_path = solver_file_path
        self.__cnf_file_path = cnf_file_path
        self.__reports_folder_path = reports_folder_path
        self.__handled_parameters_indexes = handled_parameters_indexes
        self.__start_parameters_values = start_parameters_values
        self.__max_delta = max_delta
        self.__last_parameters_values_tuple = list()
        self.__parameters_templates = SolversDescriptions.get_handled_parameters_template(self.__solver_name,
                                                                                          threads_number,
                                                                                          handled_parameters_indexes)
        parameters_classes = self.__create_parameters_classes()
        self.__values_factory = RandomParametersValuesFactory(parameters_classes)
        self.__stop = False

    def get_parameters_list(self):
        self.__last_parameters_values_tuple = self.__values_factory.create_random_parameters_tuple()
        result = list()
        result.append(self.__solver_file_path)  # первый параметр - это всегда путь до решателя
        active_parameter_index = 0
        for system_parameter_template in self.__parameters_templates:
            to_concat = system_parameter_template[0]
            parameter_string = ''
            for concrete_parameter_template in system_parameter_template[1]:
                if concrete_parameter_template[0] == 'BOOL':
                    if self.__last_parameters_values_tuple[active_parameter_index]:
                        parameter_sub_string = concrete_parameter_template[1]
                    else:
                        parameter_sub_string = concrete_parameter_template[2]
                    active_parameter_index += 1
                elif concrete_parameter_template[0] == 'RANGE':
                    parameter_sub_string = str(self.__last_parameters_values_tuple[active_parameter_index])
                    active_parameter_index += 1
                elif concrete_parameter_template[0] == 'STRING':
                    parameter_sub_string = concrete_parameter_template[1]
                elif concrete_parameter_template[0] == 'CNF':
                    parameter_sub_string = self.__cnf_file_path
                elif concrete_parameter_template[0] == 'OUTPUT':
                    parameter_sub_string = self.__reports_folder_path \
                        + self.__create_output_file_name(self.__last_parameters_values_tuple)
                else:
                    raise RuntimeError("ParametersModule.get_parameters_list: invalid type of parameter.")
                if len(parameter_sub_string) != 0:
                    if to_concat:
                        parameter_string += parameter_sub_string
                    else:
                        result.append(parameter_sub_string)
            if to_concat:
                result.append(parameter_string)
        return result

    def get_last_handled_parameters_values(self):
        return self.__last_parameters_values_tuple

    def get_parameters_str(self, parameters_values):
        return self.__create_output_file_name(parameters_values)

    def get_progress_string(self):
        return "?/?"

    def has_new_parameters_list(self):
        return not self.__stop

    def stop(self):
        self.__stop = True

# ----------------------------------------------------------------------------------------------------------------------
    def __create_parameters_classes(self):
        # Для справки:
        # class BoolParameter.__init__(self, start_val)
        # class RangeParameter.__init__(self, start_val, min_val, max_val, step)
        result = list()
        active_parameter_index = 0
        for system_parameter_template in self.__parameters_templates:
            for concrete_parameter_template in system_parameter_template[1]:
                if (concrete_parameter_template[0] == 'BOOL') or (concrete_parameter_template[0] == 'RANGE'):
                    if len(self.__start_parameters_values)-1 < active_parameter_index:
                        raise RuntimeError('ParametersModule.__create_parameters_classes: number of start '
                                           'parameters values is not equal to the number of handled active '
                                           'parameters (please check your start values file).')
                    if concrete_parameter_template[0] == 'BOOL':
                        result.append(BoolParameter(False))
                        active_parameter_index += 1
                    elif concrete_parameter_template[0] == 'RANGE':
                        start_val = self.__start_parameters_values[active_parameter_index][0]
                        step_val = self.__start_parameters_values[active_parameter_index][1]
                        minv = concrete_parameter_template[1] \
                            if start_val - self.__max_delta*step_val < concrete_parameter_template[1] \
                            else start_val - self.__max_delta*step_val
                        maxv = concrete_parameter_template[2] \
                            if start_val + self.__max_delta*step_val > concrete_parameter_template[2] \
                            else start_val + self.__max_delta*step_val
                        result.append(RangeParameter(minv, minv, maxv, step_val))
                        active_parameter_index += 1
                    else:  # иные типы подпараметров нас не интересуют, ибо не являются "активными"
                        pass
        return result

    def __create_output_file_name(self, parameters_values):
        result_file_name = ''
        handled_params_index = 0
        handled_params_indexes_number = len(self.__handled_parameters_indexes)
        param_index = -1
        full_templates = SolversDescriptions.get_parameters_template(self.__solver_name, 1)
        for system_parameter_template in full_templates:
            param_index += 1
            if handled_params_index >= handled_params_indexes_number:
                break
            if param_index == self.__handled_parameters_indexes[handled_params_index]:
                for concrete_parameter_template in system_parameter_template[1]:
                    if concrete_parameter_template[0] == 'BOOL':
                        if parameters_values[handled_params_index]:
                            result_file_name += str(param_index) + '-' + concrete_parameter_template[1] + '__'
                        else:
                            result_file_name += str(param_index) + '-' + concrete_parameter_template[2] + '__'
                    elif concrete_parameter_template[0] == 'RANGE':
                        result_file_name += str(param_index) + '-' \
                            + str(parameters_values[handled_params_index]) + '__'
                handled_params_index += 1
        return result_file_name[:len(result_file_name)-2]


########################################################################################################################
class ParametersModule(object):
    def __init__(self,
                 solver_file_path,
                 cnf_file_path,
                 reports_folder_path,
                 threads_number,
                 handled_parameters_indexes,
                 # количество = количеству обрабатываемых активных параметров (лишних значений нет)
                 start_parameters_values,
                 max_delta,
                 max_hamming_distance,
                 min_hamming_distance=1):
        self.__solver_name = FileModule.get_file_name(solver_file_path)
        self.__solver_file_path = solver_file_path
        self.__cnf_file_path = cnf_file_path
        self.__reports_folder_path = reports_folder_path
        self.__handled_parameters_indexes = handled_parameters_indexes
        # start_parameters_values это массив, элементы которого могут быть:
        # bool значением для параметра типа BOOL
        # кортежем из 2-х double для параметра типа RANGE
        self.__start_parameters_values = start_parameters_values
        self.__last_parameters_values_tuple = list()
        self.__parameters_templates = SolversDescriptions.get_handled_parameters_template(self.__solver_name,
                                                                                          threads_number,
                                                                                          handled_parameters_indexes)
        parameters_classes = self.__create_parameters_classes()
        self.__max_delta = max_delta
        self.__values_factory = ParametersValuesFactory(parameters_classes,
                                                        max_delta,
                                                        max_hamming_distance,
                                                        min_hamming_distance)

    def get_area(self):
        initializer = list()
        parameters_classes = self.__create_parameters_classes()
        for parameters_class in parameters_classes:
            if isinstance(parameters_class, BoolParameter):
                initializer.append((0, 1, 1))  # min, max, step
            elif isinstance(parameters_class, RangeParameter):
                start_val = parameters_class.get_start_value()
                step = parameters_class.get_step()
                if start_val-step*self.__max_delta <= parameters_class.get_min_value():
                    minv = parameters_class.get_min_value() + (start_val-parameters_class.get_min_value()) % step
                else:
                    minv = start_val-step*self.__max_delta
                if start_val+step*self.__max_delta >= parameters_class.get_max_value():
                    maxv = parameters_class.get_max_value() - (parameters_class.get_max_value()-start_val) % step
                else:
                    maxv = start_val+step*self.__max_delta
                initializer.append((minv,
                                    maxv,
                                    parameters_class.get_step()))
            else:
                raise RuntimeError("ParametersModule.get_area: .")
        return Area(initializer)

    def has_new_parameters_list(self):
        return self.__values_factory.has_new_parameters_tuples()

    def get_parameters_list(self):
        self.__last_parameters_values_tuple = self.__values_factory.create_parameters_tuple()
        result = list()
        result.append(self.__solver_file_path)  # первый параметр - это всегда путь до решателя
        active_param_index = 0
        for system_parameter_template in self.__parameters_templates:
            to_concat = system_parameter_template[0]
            parameter_string = ''
            for concrete_parameter_template in system_parameter_template[1]:
                if concrete_parameter_template[0] == 'BOOL':
                    if self.__last_parameters_values_tuple[active_param_index]:
                        parameter_sub_string = concrete_parameter_template[1]
                    else:
                        parameter_sub_string = concrete_parameter_template[2]
                    active_param_index += 1
                elif concrete_parameter_template[0] == 'RANGE':
                    parameter_sub_string = str(self.__last_parameters_values_tuple[active_param_index])
                    active_param_index += 1
                elif concrete_parameter_template[0] == 'STRING':
                    parameter_sub_string = concrete_parameter_template[1]
                elif concrete_parameter_template[0] == 'CNF':
                    parameter_sub_string = self.__cnf_file_path
                elif concrete_parameter_template[0] == 'OUTPUT':
                    parameter_sub_string = self.__reports_folder_path \
                        + self.__create_output_file_name(self.__last_parameters_values_tuple)
                else:
                    raise RuntimeError("ParametersModule.get_parameters_list: invalid type of parameter.")
                if len(parameter_sub_string) != 0:
                    if to_concat:
                        parameter_string += parameter_sub_string
                    else:
                        result.append(parameter_sub_string)
            if to_concat:
                result.append(parameter_string)
        return result

    def get_last_handled_parameters_values(self):
        return self.__last_parameters_values_tuple

    def get_last_parameters_list_index(self):
        return self.__values_factory.get_last_tuple_index()

    def get_parameters_str(self, parameters_values):
        return self.__create_output_file_name(parameters_values)

    def get_progress_string(self):
        return str(self.__values_factory.get_last_tuple_index()) + "/" \
            + str(self.__values_factory.get_number_of_parameters_tuples())

    def skip_start_values(self):
        self.__values_factory.create_parameters_tuple()

# ----------------------------------------------------------------------------------------------------------------------
    def __create_parameters_classes(self):
        # Для справки:
        # class BoolParameter.__init__(self, start_val)
        # class RangeParameter.__init__(self, start_val, min_val, max_val, step)
        result = list()
        active_parameter_index = 0
        for system_parameter_template in self.__parameters_templates:
            for concrete_parameter_template in system_parameter_template[1]:
                if (concrete_parameter_template[0] == 'BOOL') or (concrete_parameter_template[0] == 'RANGE'):
                    if len(self.__start_parameters_values)-1 < active_parameter_index:
                        raise RuntimeError('ParametersModule.__create_parameters_classes: number of start '
                                           'parameters values is not equal to the number of handled active '
                                           'parameters (please check your start values file).')
                    if concrete_parameter_template[0] == 'BOOL':
                        start_val = self.__start_parameters_values[active_parameter_index]
                        if isinstance(start_val, bool):
                            result.append(BoolParameter(start_val))
                        elif int(start_val) == 1:
                            result.append(BoolParameter(True))
                        elif int(start_val) == 0:
                            result.append(BoolParameter(False))
                        else:
                            raise RuntimeError("ParametersModule.__create_parameters_classes: "
                                               "invalid bool parameter val.")
                    elif concrete_parameter_template[0] == 'RANGE':
                        result.append(RangeParameter(self.__start_parameters_values[active_parameter_index][0],
                                                     concrete_parameter_template[1],
                                                     concrete_parameter_template[2],
                                                     self.__start_parameters_values[active_parameter_index][1]))
                    else:  # иные типы подпараметров нас не интересуют, ибо не являются "активными"
                        pass
                    active_parameter_index += 1
        return result

    def __create_output_file_name(self, parameters_values):
        result_file_name = ''
        handled_params_index = 0
        handled_params_indexes_number = len(self.__handled_parameters_indexes)
        param_index = -1
        full_templates = SolversDescriptions.get_parameters_template(self.__solver_name, 1)
        for system_parameter_template in full_templates:
            param_index += 1
            if handled_params_index >= handled_params_indexes_number:
                break
            if param_index == self.__handled_parameters_indexes[handled_params_index]:
                for concrete_parameter_template in system_parameter_template[1]:
                    if concrete_parameter_template[0] == 'BOOL':
                        if parameters_values[handled_params_index]:
                            result_file_name += str(param_index) + '-' + concrete_parameter_template[1] + '__'
                        else:
                            result_file_name += str(param_index) + '-' + concrete_parameter_template[2] + '__'
                    elif concrete_parameter_template[0] == 'RANGE':
                        result_file_name += str(param_index) + '-' \
                            + str(parameters_values[handled_params_index]) + '__'
                handled_params_index += 1
        return result_file_name[:len(result_file_name)-2]
