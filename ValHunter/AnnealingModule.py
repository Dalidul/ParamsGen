import math
import random


class AnnealingModule(object):
    def __init__(self, default_point_and_time):
        self.__points_and_time = list()
        self.__all_points_and_time = list()
        self.__best_point_and_time = default_point_and_time
        self.__thermometer = Thermometer(10)

    def get_best_point_and_time(self):
        return self.__best_point_and_time

    def get_top_of_points(self, number):
        result = list()
        for index, point_and_time in enumerate(self.__all_points_and_time):
            if index < number:
                result.append(point_and_time)
            else:
                break
        return result

    def add_point(self, point, solving_time):
        self.__save_point(point, solving_time)
        print("AnnealingModule.add_point: time = " + str(solving_time) + " , " + str(point))
        if self.__best_point_and_time is not None:
            if solving_time <= self.__best_point_and_time[1]:
                self.__best_point_and_time = (point, solving_time)
        else:
            self.__best_point_and_time = (point, solving_time)
        for index, point_and_time in enumerate(self.__points_and_time):
            if solving_time <= point_and_time[1]:
                print("index = " + str(index))
                self.__points_and_time.insert(index, (point, solving_time))
                return
        print("index = Last")
        self.__points_and_time.append((point, solving_time))

    def get_next_point_and_time(self, previous_point_time):
        result = None
        index_to_remove = -1
        print("SEARCH. previous point time = " + str(previous_point_time))
        for index, point_and_time in enumerate(self.__points_and_time):
            tested_time = point_and_time[1]
            print("tested time = " + str(tested_time))
            if previous_point_time > tested_time:
                result = point_and_time
                index_to_remove = index
                break
            else:
                if self.__thermometer.get_val() <= 0:
                    return None
                probability = math.exp(-1*(tested_time-previous_point_time)/self.__thermometer.get_val())
                if random.random() <= probability:
                    result = point_and_time
                    index_to_remove = index
                    print(print("Prob: " + str(probability) + " --- " + "(+)"))
                    break
                else:
                    print(print("Prob: " + str(probability) + " --- " + "(-)"))
        self.__thermometer.cool()
        if result is not None:
            self.__points_and_time.pop(index_to_remove)
        return result

# ----------------------------------------------------------------------------------------------------------------------
    def __save_point(self, point, solving_time):
        for index, point_and_time in enumerate(self.__all_points_and_time):
            if solving_time <= point_and_time[1]:
                self.__all_points_and_time.insert(index, (point, solving_time))
                return
        self.__all_points_and_time.append((point, solving_time))


########################################################################################################################
class Thermometer(object):
    def __init__(self, start_temperature):
        self.__temperature = start_temperature

    def get_val(self):
        return self.__temperature

    def cool(self):
        self.__temperature -= 1