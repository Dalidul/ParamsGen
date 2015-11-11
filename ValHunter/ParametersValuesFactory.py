import sys
import copy
from Enum import enum
from decimal import Decimal
import random


########################################################################################################################
class RangeParameter(object):
    def __init__(self, start_val, min_val, max_val, step):
        if min_val >= max_val:
            raise RuntimeError('RangeParameter:__init__: invalid range (min_val >= max_val).')
        if (start_val < min_val) or (start_val > max_val):
            raise RuntimeError('RangeParameter:__init__: start value is out of range (< min OR > max).')
        if (step <= 0) or (step > (max_val-min_val)):
            raise RuntimeError('RangeParameter:__init__: invalid step value (step = ' + step + ').')
        self.__START_VAL = Decimal(start_val)
        self.__MIN = Decimal(min_val)
        self.__MAX = Decimal(max_val)
        self.__STEP = Decimal(step)

    def __str__(self):
        return "(start = " + str(self.__START_VAL) + " min = " + str(self.__MIN) + \
               " max = " + str(self.__MAX) + " step = " + str(self.__STEP) + ")"

    def get_start_value(self):
        return self.__START_VAL

    def get_min_value(self):
        return self.__MIN

    def get_max_value(self):
        return self.__MAX

    def get_step(self):
        return self.__STEP


########################################################################################################################
class BoolParameter(object):
    def __init__(self, start_val):  # bool start_val
        self.__START_VAL = start_val

    def get_start_value(self):
        return self.__START_VAL


########################################################################################################################
########################################################################################################################
class RandomParametersValuesFactory(object):
    def __init__(self, parameters):
        self.__parameters = parameters

    def create_random_parameters_tuple(self):
        result = list()
        for param_index, param in enumerate(self.__parameters):
            if isinstance(param, RangeParameter):
                max_delta = (param.get_max_value() - param.get_min_value()) / param.get_step()
                result.append(param.get_min_value() + param.get_step()*Decimal(random.randrange(0,
                                                                                                # включая max
                                                                                                max_delta+1,
                                                                                                1)))
            elif isinstance(param, BoolParameter):
                result.append(random.random() < 0.5)
            else:
                raise RuntimeError("ParametersFactory.__init__: Invalid type of parameter")
        print(result)
        return tuple(result)


########################################################################################################################
########################################################################################################################
class ParametersValuesFactory(object):
    def __init__(self, parameters, max_delta, max_hamming_distance, min_hamming_distance=1):
        self.__parameters_number = len(parameters)
        self.__created_tuples_count = 0
        hamming_parameters = list()
        for param_index, param in enumerate(parameters):
            if isinstance(param, RangeParameter):
                if param.get_start_value() + max_delta * param.get_step() >= param.get_max_value():
                    max_val = param.get_max_value()
                else:
                    max_val = param.get_start_value() + max_delta * param.get_step()
                if param.get_start_value() - max_delta * param.get_step() <= param.get_min_value():
                    min_val = param.get_min_value()
                else:
                    min_val = param.get_start_value() - max_delta * param.get_step()
                hamming_parameters.append(RangedBlock(param.get_start_value(), min_val, max_val, param.get_step()))
            elif isinstance(param, BoolParameter):
                hamming_parameters.append(BoolBlock(param.get_start_value()))
            else:
                raise RuntimeError("ParametersFactory.__init__: Invalid type of parameter")
        self.__hamming_unit = HammingUnit(hamming_parameters, max_hamming_distance, min_hamming_distance)

    def create_parameters_tuple(self):
        if self.__created_tuples_count < self.__hamming_unit.get_number_of_different_values():
            result_tuple = self.__hamming_unit.get_current_blocks_values()
            if self.__created_tuples_count < self.__hamming_unit.get_number_of_different_values()-1:
                self.__hamming_unit.create_new_parameters_values()
            self.__created_tuples_count += 1
            return tuple(result_tuple)
        else:
            raise RuntimeError("ParametersFactory.create_parameters_tuple: No more new parameters tuples")

    def get_last_tuple_index(self):
        return self.__created_tuples_count

    def get_number_of_parameters_tuples(self):
        return self.__hamming_unit.get_number_of_different_values()

    def has_new_parameters_tuples(self):
        return self.__created_tuples_count < self.__hamming_unit.get_number_of_different_values()


########################################################################################################################
class HammingUnit(object):
    def __init__(self, blocks, max_distance, min_distance=1):
        if min_distance > len(blocks):
            raise RuntimeError("HammingUnit.__init__: Too big minimum distance value")
        self.__blocks = blocks          # list of Ranged or Bool Blocks
        self.__max_distance = max_distance
        if max_distance < min_distance:
            min_distance = max_distance
        self.__min_distance = min_distance
        self.__number_of_different_values = self.__calculate_number_of_nonstandard_values()
        self.__first_shift = True  # метка о том, что блоки ещё не сдвигались
        if len(self.__blocks) < self.__max_distance:
            print('Warning: HammingUnit.__init__: inefficient max distance.')

    def get_number_of_different_values(self):
        return self.__number_of_different_values

    def get_current_blocks_values(self):
        result = list()
        for block in self.__blocks:
            result.append(block.get_value())
        return result

    def create_new_parameters_values(self):
        if self.__first_shift:
            self.__first_shift = False
            for shifted_block_index in range(self.__min_distance):
                if not self.__blocks[shifted_block_index].shift():
                    raise RuntimeError("HammingUnit.create_new_parameters_values: Impossible block state)")
            return True
        else:
            for shifted_block_index in reversed(range(len(self.__blocks))):
                if not self.__blocks[shifted_block_index].is_start_now():
                    if self.__blocks[shifted_block_index].shift():
                        return True
                    else:
                        if shifted_block_index+1 < len(self.__blocks):
                            self.__blocks[shifted_block_index+1].shift()
                            return True
                        else:
                            return self.__move_active_blocks(1)
            return self.__move_active_blocks(0)

# ----------------------------------------------------------------------------------------------------------------------
    def __calculate_number_of_nonstandard_values(self):
        if len(self.__blocks) > 1:
            result = 0
            result += 1  # случай, когда все значения стартовые
            max_active_blocks_number = len(self.__blocks) \
                if len(self.__blocks) < self.__max_distance else int(self.__max_distance)
            for active_blocks_number in range(1, max_active_blocks_number+1):
                fixed_size_indexes_combinations = self.__get_indexes_combinations_list(active_blocks_number)
                for indexes_sequence in fixed_size_indexes_combinations:
                    subsequence_sum = 1
                    for index in indexes_sequence:
                        subsequence_sum *= self.__blocks[index].get_number_of_shifted_values()
                    result += subsequence_sum
            return int(result)
        elif len(self.__blocks) == 1:
            return self.__blocks[0].get_number_of_shifted_values() + 1
        else:
            raise RuntimeError('HammingUnit.__calculate_number_of_nonstandard_values: blocks did not initiated.')

    def __get_indexes_combinations_list(self, size):
        result = list()
        if size > 1:
            blank = self.__get_indexes_combinations_list(size-1)  # заготовка
            for indexes_sequence in blank:
                next_unused_index = indexes_sequence[len(indexes_sequence)-1] + 1
                if next_unused_index < len(self.__blocks):
                    for new_index in range(next_unused_index, len(self.__blocks)):
                        new_sequence = copy.deepcopy(indexes_sequence)
                        new_sequence.append(new_index)
                        result.append(new_sequence)
            return result
        elif size == 1:
            for index in range(0, len(self.__blocks)):
                result.append([index, ])  # возвращает список списков
            return result
        else:
            raise RuntimeError('HammingUnit.__get_indexes_combinations_list: size must be > 0.')

    def __move_active_blocks(self, moved_blocks_count):
        if len(self.__blocks) > moved_blocks_count:
            if moved_blocks_count < self.__max_distance:
                for block_index in reversed(range(len(self.__blocks)-moved_blocks_count)):
                    if not self.__blocks[block_index].is_start_now():
                        if self.__blocks[block_index].shift():
                            for reactivated_block_index in range(block_index+1, block_index+1+moved_blocks_count):
                                if not self.__blocks[reactivated_block_index].shift():
                                    raise RuntimeError("HammingUnit.__move_active_blocks: Impossible block state (1)")
                            return True
                        elif block_index != len(self.__blocks) - 1 - moved_blocks_count:
                            if not self.__blocks[block_index+1].shift():
                                raise RuntimeError("HammingUnit.__move_active_blocks: Impossible block state (2)")
                            for reactivated_block_index in reversed(range(1, moved_blocks_count+1)):
                                if not self.__blocks[block_index+1+reactivated_block_index].shift():
                                    raise RuntimeError("HammingUnit.__move_active_blocks: Impossible block state (3)")
                            return True
                        else:
                            return self.__move_active_blocks(moved_blocks_count+1)
                # все блоки в стартовом состоянии
                if moved_blocks_count != self.__max_distance:
                    for activated_block_index in range(moved_blocks_count+1):
                        if not self.__blocks[activated_block_index].shift():
                            raise RuntimeError("HammingUnit.__move_active_blocks: Impossible block state (4)")
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False


########################################################################################################################
class RangedBlock(object):
    __INVALID = sys.maxsize
    __Directions = enum('NONE', 'RIGHT', 'LEFT')

    def __init__(self, start_value, min_val, max_val, step):
        if start_value > max_val or start_value < min_val:
            raise RuntimeError("RangedBlock.__init__: Invalid start value")
        self.__START = start_value
        # max и min посчитаны уже с учётом дельты
        self.__MIN = min_val
        self.__MAX = max_val
        self.__STEP = step
        self.__left_border = self.__START
        self.__right_border = self.__START
        self.__current = self.__START
        self.__next_shift_direction = self.__get_next_shift_direction()

    @staticmethod
    def is_ranged():
        return True

    def get_number_of_shifted_values(self):
        return int((self.__MAX - self.__START) // self.__STEP +
                   (self.__START - self.__MIN) // self.__STEP)

    def is_start_now(self):
        return self.__current == self.__START

    def get_value(self):
        return self.__current

    def shift(self):
        next_val, shift_direction = self.__get_next_val()
        if next_val != self.__INVALID:
            self.__current = next_val
            if shift_direction is self.__Directions.RIGHT:
                self.__right_border += self.__STEP
            elif shift_direction is self.__Directions.LEFT:
                self.__left_border -= self.__STEP
            else:
                raise RuntimeError("RangedBlock.shift: invalid shift direction")
            self.__next_shift_direction = self.__get_next_shift_direction(shift_direction)
            return True
        else:
            self.__left_border = self.__START
            self.__right_border = self.__START
            self.__current = self.__START
            self.__next_shift_direction = self.__get_next_shift_direction()
            return False

# ----------------------------------------------------------------------------------------------------------------------
    def __get_next_shift_direction(self, current_shift_direction=__Directions.NONE):
        if (current_shift_direction is self.__Directions.NONE) or (current_shift_direction is self.__Directions.RIGHT):
            if self.__left_border - self.__STEP >= self.__MIN:
                return self.__Directions.LEFT
            elif self.__right_border + self.__STEP <= self.__MAX:
                return self.__Directions.RIGHT
            else:
                return self.__Directions.NONE
        else:  # current_shift_direction is self.__Directions.LEFT
            if self.__right_border + self.__STEP <= self.__MAX:
                return self.__Directions.RIGHT
            elif self.__left_border - self.__STEP >= self.__MIN:
                return self.__Directions.LEFT
            else:
                return self.__Directions.NONE

    def __get_next_val(self):
        if self.__next_shift_direction is self.__Directions.RIGHT:
            return self.__right_border + self.__STEP, self.__Directions.RIGHT
        elif self.__next_shift_direction is self.__Directions.LEFT:
            return self.__left_border - self.__STEP, self.__Directions.LEFT
        else:
            return self.__INVALID, self.__Directions.NONE


########################################################################################################################
class BoolBlock(object):
    def __init__(self, start_value):
        self.__START = start_value
        self.__current = self.__START

    @staticmethod
    def is_ranged():
        return False

    def get_number_of_shifted_values(self):
        return 1

    def is_start_now(self):
        return self.__current == self.__START

    def get_value(self):
        return self.__current

    def shift(self):
        if self.__current == self.__START:
            self.__current = not self.__current
            return True
        else:
            self.__current = self.__START
            return False