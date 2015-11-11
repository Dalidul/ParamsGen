import sys
from Config.Defaults import DEFAULT_PARAMETERS_VALUES
from decimal import Decimal

# количество потоков, в которых работает решатель
from FileModule import solver_exist


def get_solver_threads_number(solver_name, full_threads_number):
        __solver_cores_using = {
            'default': full_threads_number,
            'glucan_static': full_threads_number,
            'glucored+march_release': full_threads_number,
            'glucored-multi_release': full_threads_number,
            'glucored-simp_release': full_threads_number,
            'minisat_core': Decimal('1'),
            'minisat_simp': Decimal('1'),
            'mipisat': Decimal('1'),
            'minisat_ClauseSplit': Decimal('1'),
            'minigolf': Decimal('1'),
            'pmcsat': Decimal('8'),
            'plingeling': full_threads_number,
            'treengeling': full_threads_number,
            'lingeling_aqw': Decimal('1'),
            'lingeling_ats1': Decimal('1')
        }
        return __solver_cores_using[solver_name]


# Формат параметров:
# Решатель принимает на вход некоторое количество параметров.
# Каждый из параметров может состоять из одного или нескольких подпараметров, имеющий общий тип "сборки".
# О типе сборки: --------------------------------------------------
# Функия, запускающая процесс решателя, принимает на вход объект типа список (list).
# Каждый элемент этого списка - строка (string).
# В силу внутренних особенностей устройства решателя, у некоторых из их параметов,
# имя параметра и его значение должны идти не одним элементом списка, а двумя разными.
# Для этого был введён модификатор "тип сборки": concatenate_sub_parameters/separate_sub_parameters,
# значение которого подбирается опытным путём (в случае ошибки решатель просто не запустится или
# проигнорирует невалидный параметр)
# -----------------------------------------------------------------
# !!! Имеется ограничение: среди подпараметров одного и того же параметра может быть не более одного "активного",
# т.е. учуствующего в подборе значений. На данный момент к таковым относятся только RANGE и BOOL параметры.
# -----------------------------------------------------------------
# Типы подпараметров:
# CNF:
#       - путь до файла кнф (значение не указывается)
# OUTPUT:
#       - путь до файла, в который будет помещёны результаты работы решателя,
#         которые не выводятся на консоль (значение не указывается)
# BOOL:
#       - идентификатор true
#       - идентификатор false
# RANGE: (неявно делятся на int и float. У int шаг в файле стартовых значений надо задать целым числом)
#       - min значение
#       - max значение
# STRING (используется в случае, если сам решатель как-то криво принимает параметры):
#       - строка
def get_parameters_template(solver_name, full_threads_number):
    concatenate_sub_parameters = True
    separate_sub_parameters = False
    __solvers_parameters = {
        'default':                 ((concatenate_sub_parameters, (('CNF', ), )), ),
        'glucan_static':           ((concatenate_sub_parameters, (('STRING', '-var-decay='),                # 0
                                                                  ('RANGE', 0, 1))),
                                    (concatenate_sub_parameters, (('STRING', '-cla-decay='),                # 1
                                                                  ('RANGE', 0, 1))),
                                    (concatenate_sub_parameters, (('STRING', '-nof-threads=' + str(get_solver_threads_number('glucan_static', full_threads_number))), )),
                                    (concatenate_sub_parameters, (('CNF', ), )),
                                    (concatenate_sub_parameters, (('OUTPUT', ), ))),
        'glucored+march_release':  ((concatenate_sub_parameters, (('STRING', '-var-decay='),                # 0
                                                                  ('RANGE', 0, 1))),
                                    (concatenate_sub_parameters, (('STRING', '-cla-decay='),                # 1
                                                                  ('RANGE', 0, 1))),
                                    (concatenate_sub_parameters, (('STRING', '-minLBDMinimizingClause='),   # 2
                                                                  ('RANGE', 3, 100))),
                                    (concatenate_sub_parameters, (('STRING', '-minSizeMinimizingClause='),  # 3
                                                                  ('RANGE', 3, 200))),
                                    (concatenate_sub_parameters, (('CNF', ), )),
                                    (concatenate_sub_parameters, (('OUTPUT', ), ))),
        'glucored-multi_release':  ((concatenate_sub_parameters, (('CNF', ), )),
                                    (concatenate_sub_parameters, (('OUTPUT', ), ))),
        'glucored-simp_release':   ((concatenate_sub_parameters, (('CNF', ), )),
                                    (concatenate_sub_parameters, (('OUTPUT', ), ))),

        'minisat_core':            ((concatenate_sub_parameters, (('BOOL', '-luby', '-no-luby'), )),    # 0
                                    (concatenate_sub_parameters, (('STRING', '-var-decay='),            # 1
                                                                  ('RANGE', 0, 1))),
                                    (concatenate_sub_parameters, (('STRING', '-cla-decay='),            # 2
                                                                  ('RANGE', 0, 1))),
                                    (concatenate_sub_parameters, (('STRING', '-rinc='),                 # 3
                                                                  ('RANGE', 1, 100))),
                                    (concatenate_sub_parameters, (('STRING', '-gc-frac='),              # 4
                                                                  ('RANGE', 0, 10))),
                                    (concatenate_sub_parameters, (('STRING', '-rfirst='),               # 5 integer
                                                                  ('RANGE', 1, 1000))),
                                    (concatenate_sub_parameters, (('STRING', '-ccmin-mode='),           # 6 integer
                                                                  ('RANGE', 0, 2))),
                                    (concatenate_sub_parameters, (('STRING', '-phase-saving='),         # 7 integer
                                                                  ('RANGE', 0, 2))),
                                    (concatenate_sub_parameters, (('CNF', ), )),                        # 8
                                    (concatenate_sub_parameters, (('OUTPUT', ), ))),                    # 9

        'minisat_simp':            ((concatenate_sub_parameters, (('BOOL', '-luby', '-no-luby'), )),    # 0
                                    (concatenate_sub_parameters, (('STRING', '-var-decay='),            # 1
                                                                  ('RANGE', 0, 1))),
                                    (concatenate_sub_parameters, (('STRING', '-cla-decay='),            # 2
                                                                  ('RANGE', 0, 1))),
                                    (concatenate_sub_parameters, (('STRING', '-rinc='),                 # 3
                                                                  ('RANGE', 1, sys.maxsize))),
                                    (concatenate_sub_parameters, (('STRING', '-gc-frac='),              # 4
                                                                  ('RANGE', 0, sys.maxsize))),
                                    (concatenate_sub_parameters, (('STRING', '-rfirst='),               # 5 integer
                                                                  ('RANGE', 1, sys.maxsize))),
                                    (concatenate_sub_parameters, (('STRING', '-ccmin-mode='),           # 6 integer
                                                                  ('RANGE', 0, 2))),
                                    (concatenate_sub_parameters, (('STRING', '-phase-saving='),         # 7 integer
                                                                  ('RANGE', 0, 2))),
                                    (concatenate_sub_parameters, (('CNF', ), )),                        # 8
                                    (concatenate_sub_parameters, (('OUTPUT', ), ))),                    # 9
        'mipisat':                 ((concatenate_sub_parameters, (('BOOL', '-luby', '-no-luby'), )),    # 0
                                    (concatenate_sub_parameters, (('STRING', '-var-decay='),            # 1
                                                                  ('RANGE', 0, 1))),
                                    (concatenate_sub_parameters, (('STRING', '-cla-decay='),            # 2
                                                                  ('RANGE', 0, 1))),
                                    (concatenate_sub_parameters, (('STRING', '-rinc='),                 # 3
                                                                  ('RANGE', 1, sys.maxsize))),
                                    (concatenate_sub_parameters, (('STRING', '-gc-frac='),              # 4
                                                                  ('RANGE', 0, sys.maxsize))),
                                    (concatenate_sub_parameters, (('STRING', '-rfirst='),               # 5 integer
                                                                  ('RANGE', 1, sys.maxsize))),
                                    (concatenate_sub_parameters, (('STRING', '-ccmin-mode='),           # 6 integer
                                                                  ('RANGE', 0, 2))),
                                    (concatenate_sub_parameters, (('STRING', '-phase-saving='),         # 7 integer
                                                                  ('RANGE', 0, 2))),
                                    (concatenate_sub_parameters, (('CNF', ), )),                        # 8
                                    (concatenate_sub_parameters, (('OUTPUT', ), ))),                    # 9
        'minisat_ClauseSplit':     ((concatenate_sub_parameters, (('BOOL', '-luby', '-no-luby'), )),    # 0
                                    (concatenate_sub_parameters, (('STRING', '-var-decay='),            # 1
                                                                  ('RANGE', 0, 1))),
                                    (concatenate_sub_parameters, (('STRING', '-cla-decay='),            # 2
                                                                  ('RANGE', 0, 1))),
                                    (concatenate_sub_parameters, (('STRING', '-rinc='),                 # 3
                                                                  ('RANGE', 1, sys.maxsize))),
                                    (concatenate_sub_parameters, (('STRING', '-gc-frac='),              # 4
                                                                  ('RANGE', 0, sys.maxsize))),
                                    (concatenate_sub_parameters, (('STRING', '-rfirst='),               # 5 integer
                                                                  ('RANGE', 1, sys.maxsize))),
                                    (concatenate_sub_parameters, (('STRING', '-ccmin-mode='),           # 6 integer
                                                                  ('RANGE', 0, 2))),
                                    (concatenate_sub_parameters, (('STRING', '-phase-saving='),         # 7 integer
                                                                  ('RANGE', 0, 2))),
                                    (concatenate_sub_parameters, (('STRING', '-S-MCL='),                # 9 integer
                                                                  ('RANGE', 3, 2147483647))),
                                    (concatenate_sub_parameters, (('STRING', '-S-TMIN='),               # 10 integer
                                                                  ('RANGE', 0, 2147483647))),
                                    (concatenate_sub_parameters, (('STRING', '-S-TMAX='),               # 11 integer
                                                                  ('RANGE', 0, 2147483647))),
                                    (concatenate_sub_parameters, (('STRING', '-S-ACF='),                # 12 integer
                                                                  ('RANGE', 0, 1))),
                                    (concatenate_sub_parameters, (('CNF', ), )),                        # 13
                                    (concatenate_sub_parameters, (('OUTPUT', ), ))),                    # 14
        'minigolf':                ((concatenate_sub_parameters, (('CNF', ), )),
                                    (concatenate_sub_parameters, (('OUTPUT', ), ))),
        'pmcsat':                  ((concatenate_sub_parameters, (('BOOL', '-luby', '-no-luby'), )),    # 0
                                    (concatenate_sub_parameters, (('STRING', '-var-decay='),            # 1
                                                                  ('RANGE', 0, 1))),
                                    (concatenate_sub_parameters, (('STRING', '-cla-decay='),            # 2
                                                                  ('RANGE', 0, 1))),
                                    (concatenate_sub_parameters, (('STRING', '-rinc='),                 # 3
                                                                  ('RANGE', 1, sys.maxsize))),
                                    (concatenate_sub_parameters, (('STRING', '-gc-frac='),              # 4
                                                                  ('RANGE', 0, sys.maxsize))),
                                    (concatenate_sub_parameters, (('STRING', '-rfirst='),               # 5 integer
                                                                  ('RANGE', 1, sys.maxsize))),
                                    (concatenate_sub_parameters, (('STRING', '-ccmin-mode='),           # 6 integer
                                                                  ('RANGE', 0, 2))),
                                    (concatenate_sub_parameters, (('STRING', '-phase-saving='),         # 7 integer
                                                                  ('RANGE', 0, 2))),
                                    (concatenate_sub_parameters, (('CNF', ), )),                        # 8
                                    (concatenate_sub_parameters, (('OUTPUT', ), ))),                    # 9
        'plingeling':              ((separate_sub_parameters,    (('STRING', '-t'),
                                                                  ('STRING', str(get_solver_threads_number('plingeling', full_threads_number))))),
                                    (concatenate_sub_parameters, (('CNF', ), ))),
        'treengeling':             ((separate_sub_parameters,    (('STRING', '-t'),
                                                                  ('STRING', str(get_solver_threads_number('treengeling', full_threads_number))))),
                                    (concatenate_sub_parameters, (('CNF', ), ))),
        'lingeling_aqw':           ((separate_sub_parameters,    (('STRING', '-o'),
                                                                  ('OUTPUT', ))),
                                    (concatenate_sub_parameters, (('CNF', ), ))),
        'lingeling_ats1':          ((separate_sub_parameters,    (('STRING', '-o'),
                                                                  ('OUTPUT', ))),
                                    (concatenate_sub_parameters, (('CNF', ), )))
    }
    return __solvers_parameters[solver_name]


def get_handled_parameters_template(solver_name, full_threads_number, handled_params_indexes):
    parameter_template = get_parameters_template(solver_name, full_threads_number)
    result_template = list()
    handled_param_index = 0
    for index, params_tuple in enumerate(parameter_template):
        if index == handled_params_indexes[handled_param_index]:
            result_template.append(params_tuple)
            handled_param_index += 1
            if handled_param_index == len(handled_params_indexes):
                break
    return result_template


def get_active_parameters_indexes(solver_name, handled_params_indexes):
    result_indexes = list()
    template = get_parameters_template(solver_name, 1)
    handled_param_index = 0
    for index, parameter_template in enumerate(template):
        if index == handled_params_indexes[handled_param_index]:
            for sub_parameter in parameter_template[1]:
                if (sub_parameter[0] == 'BOOL') or (sub_parameter[0] == 'RANGE'):
                    result_indexes.append(index)
            handled_param_index += 1
            if handled_param_index == len(handled_params_indexes):
                return result_indexes
    return result_indexes


def get_start_parameters_values(solver_name, handled_parameters_indexes, values_list):
    result = list()
    parameters_templates = get_parameters_template(solver_name, 1)
    handled_params_index = 0
    active_parameter_index = 0
    for index, system_parameter_template in enumerate(parameters_templates):
        for concrete_parameter_template in system_parameter_template[1]:
            if (concrete_parameter_template[0] == 'BOOL') or (concrete_parameter_template[0] == 'RANGE'):
                if index == handled_parameters_indexes[handled_params_index]:
                    result.append(values_list[active_parameter_index])
                active_parameter_index += 1
                break
        if index == handled_parameters_indexes[handled_params_index]:
            handled_params_index += 1
            if handled_params_index == len(handled_parameters_indexes):
                return result
    return result


def get_default_parameters_values(solver_name):
    return DEFAULT_PARAMETERS_VALUES[solver_name]