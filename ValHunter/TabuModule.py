import copy
from decimal import Decimal

class TabuModule(object):
    def __init__(self):
        self.__areas = list()
        self.__current_area = None
        self.__current_best_point = None
        self.__current_best_time = None

    def get_current_best_parameters_and_time(self):
        return self.__current_best_point, self.__current_best_time

    def add_area(self, new_area):
        if self.__current_area is not None:
            b = new_area.intersects(self.__areas[0])
        for area in self.__areas:
            if area.is_superset(new_area):
                return False
        intersected_areas = list()
        for area in self.__areas:
            if area.intersects(new_area):
                intersected_areas.append(area)
        self.__fill_area(new_area, intersected_areas)
        self.__areas.append(new_area)
        self.__current_area = self.__areas[len(self.__areas)-1]
        return True

    def get_solving_time(self, point):
        solving_time = self.__current_area.get_time(point)
        return solving_time

    # Устанавливает время для точки в последней добавленной области
    def set_solving_time(self, point, solving_time):
        if self.__current_area is None:
            raise RuntimeError("TabuModule.set_solving_time: no areas added.")
        self.__current_area.set_time(point, solving_time)
        if (self.__current_best_point is not None) and (solving_time > -1):
            if self.__current_best_time > solving_time:
                self.__current_best_point = copy.deepcopy(point)
                self.__current_best_time = solving_time
        else:
            self.__current_best_point = copy.deepcopy(point)
            self.__current_best_time = solving_time

# ----------------------------------------------------------------------------------------------------------------------
    @staticmethod
    def __fill_area(area, intersected_areas):
        for intersected_area in intersected_areas:
            for point in intersected_area.get_next_valued_point():
                if area.contains(point):
                    time_val = intersected_area.get_time(point)
                    if time_val != Area.INVALID_TIME_VALUE:
                        area.forced_set_time(point, intersected_area.get_time(point))


########################################################################################################################
class Area(object):
    INVALID_TIME_VALUE = -2

    def __init__(self, coords_tuples):
        self.__mins = list()
        self.__maxs = list()
        self.__steps = list()
        for coord in coords_tuples:
            self.__mins.append(coord[0])
            self.__maxs.append(coord[1])
            self.__steps.append(coord[2])
        if not self.__is_valid():
            raise RuntimeError("Area.__init__: invalid area initialisations parameters values.")
        self.__points_and_time = dict()

    def get_next_valued_point(self):
        for point in self.__points_and_time:
            yield self.__points_and_time[point][0]

    def is_equal(self, other):
        for index in range(len(self.__mins)):
            self_min = self.__mins[index]
            other_min = other.__mins[index]
            self_max = self.__maxs[index]
            other_max = other.__maxs[index]
            self_step = self.__steps[index]
            other_step = other.__steps[index]
            if self_min != other_min:
                return False
            if self_max != other_max:
                return False
            if self_step != other_step:
                return False
        return True

    def is_subset(self, other):
        for index in range(len(self.__mins)):
            self_min = self.__mins[index]
            other_min = other.__mins[index]
            self_max = self.__maxs[index]
            other_max = other.__maxs[index]
            self_step = self.__steps[index]
            other_step = other.__steps[index]
            if self_min < other_min:
                return False
            if self_max > other_max:
                return False
            if self_step != other_step:
                if self_min != self_max:
                    return False
        return True

    def is_superset(self, other):
        return other.is_subset(self)

    def intersects(self, other):
        for index in range(len(self.__mins)):
            self_min = self.__mins[index]
            other_min = other.__mins[index]
            self_max = self.__maxs[index]
            other_max = other.__maxs[index]
            self_step = self.__steps[index]
            other_step = other.__steps[index]
            if self_min > other_max:
                return False
            if other_min > self_max:
                return False
            if self_step == other_step:
                if abs(other_min-self_min) % self_step != 0:
                    return False
            else:
                self_val = self_min
                other_val = other_min
                intersection_finded = False
                while True:
                    if self_val < other_val:
                        self_val += self_step
                    elif self_val > other_val:
                        other_val += other_step
                    else:
                        intersection_finded = True
                        break
                if not intersection_finded:
                    return False
        return True

    def contains(self, point):
        for index in range(len(self.__mins)):
            self_min = self.__mins[index]
            self_max = self.__maxs[index]
            self_step = self.__steps[index]
            coord_val = point.get_coord_val(index)
            if (coord_val < self_min) or (coord_val > self_max):
                return False
            if ((coord_val-self_min) % self_step) != 0:
                return False
        return True

    def get_time(self, point):
        if not self.__point_is_valid(point):
            raise RuntimeError("Area.set_time: the point may not belong to the area (point = " + point.__str__() + ")")
        if not self.contains(point):
            raise RuntimeError("Area.set_time: the point does not in the area (point = " + point.__str__() + ")")
        if point.__str__() in self.__points_and_time:
            return self.__points_and_time[point.__str__()][1]
        else:
            return Area.INVALID_TIME_VALUE

    def set_time(self, point, time_value):
        if not self.__point_is_valid(point):
            raise RuntimeError("Area.set_time: the point may not belong to the area (point = " + point.__str__() + ")")
        if not self.contains(point):
            raise RuntimeError("Area.set_time: the point does not in the area (point = " + point.__str__() + ")")
        if point.__str__() in self.__points_and_time:
            raise RuntimeError("Area.set_time: point value is already set (point: " + point.__str__()
                               + ", new_value = " + str(time_value) + ", previous value = " + str(self.get_time())
                               + ")")
        self.__points_and_time[point.__str__()] = (point, time_value)

    def forced_set_time(self, point, time_value):
        self.__points_and_time[point.__str__()] = (point, time_value)

# ----------------------------------------------------------------------------------------------------------------------
    def __is_valid(self):
        if not (len(self.__mins) and len(self.__maxs) and len(self.__steps)):
            return False
        for index in range(len(self.__mins)):
            self_min = self.__mins[index]
            self_max = self.__maxs[index]
            self_step = self.__steps[index]
            if self_min > self_max:
                return False
            if (self_max-self_min) % self_step != 0:
                return False
        return True

    def __point_is_valid(self, point):
        if point.get_coords_number() != len(self.__mins):
            return False
        for index in range(len(self.__mins)):
            self_min = self.__mins[index]
            self_max = self.__maxs[index]
            self_step = self.__steps[index]
            coord_val = point.get_coord_val(index)
            if (coord_val < self_min) or (coord_val > self_max):
                return False
            if (coord_val-self_min) % self_step != 0:
                return False
        return True


########################################################################################################################
class Point(object):
    def __init__(self, coords):
        self.coords_values = tuple(coords)

    def __str__(self):
        result = '('
        for coord_index, coord_value in enumerate(self.coords_values):
            result += str(coord_value)
            if coord_index != len(self.coords_values)-1:
                result += ', '
        return result + ')'

    def get_next_coord_val(self):
        for coord_value in self.coords_values:
            yield coord_value

    def get_coord_val(self, index):
        return self.coords_values[index]

    def get_coords_number(self):
        return len(self.coords_values)

















# ########################################################################################################################
# class Area(object):
#     INVALID_TIME_VALUE = -2
#
#     def __init__(self, coords_tuples):
#         self.__mins = list()
#         self.__maxs = list()
#         self.__steps = list()
#         for coord in coords_tuples:
#             self.__mins.append(coord[0])
#             self.__maxs.append(coord[1])
#             self.__steps.append(coord[2])
#         if not self.__is_valid():
#             raise RuntimeError("Area.__init__: invalid area initialisations parameters values.")
#         self.__points_values = list()
#         points_number = self.__calculate_points_number()
#         for point_index in range(points_number):
#             self.__points_values.append(Area.INVALID_TIME_VALUE)
#
#     def get_next_point(self):
#         coords = list()
#         for min in self.__mins:
#             coords.append(min)
#         yield Point(coords)
#         while self.__lol(coords, 0):
#             yield Point(coords)
#
#     def get_next_valued_point(self):
#         coords = list()
#         for minv in self.__mins:
#             coords.append(minv)
#         point = Point(coords)
#         if self.get_time(point) != Area.INVALID_TIME_VALUE:
#             yield point
#         while self.__lol(coords, 0):
#             point = Point(coords)
#             if self.get_time(point) != Area.INVALID_TIME_VALUE:
#                 yield Point(coords)
#
#
#     def __lol(self, coords, i):
#         if i < len(coords):
#             if coords[i] < self.__maxs[i]:
#                 coords[i] += self.__steps[i]
#                 return True
#             else:
#                 coords[i] = self.__mins[i]
#                 return self.__lol(coords, i+1)
#         else:
#             return False
#
#     def is_equal(self, other):
#         for index in range(len(self.__mins)):
#             self_min = self.__mins[index]
#             other_min = other.__mins[index]
#             self_max = self.__maxs[index]
#             other_max = other.__maxs[index]
#             self_step = self.__steps[index]
#             other_step = other.__steps[index]
#             if self_min != other_min:
#                 return False
#             if self_max != other_max:
#                 return False
#             if self_step != other_step:
#                 return False
#         return True
#
#     def is_subset(self, other):
#         for index in range(len(self.__mins)):
#             self_min = self.__mins[index]
#             other_min = other.__mins[index]
#             self_max = self.__maxs[index]
#             other_max = other.__maxs[index]
#             self_step = self.__steps[index]
#             other_step = other.__steps[index]
#             if self_min < other_min:
#                 return False
#             if self_max > other_max:
#                 return False
#             if self_step != other_step:
#                 if self_min != self_max:
#                     return False
#         return True
#
#     def is_superset(self, other):
#         return other.is_subset(self)
#
#     def intersects(self, other):
#         for index in range(len(self.__mins)):
#             self_min = self.__mins[index]
#             other_min = other.__mins[index]
#             self_max = self.__maxs[index]
#             other_max = other.__maxs[index]
#             self_step = self.__steps[index]
#             other_step = other.__steps[index]
#             if self_min > other_max:
#                 return False
#             if other_min > self_max:
#                 return False
#             if self_step == other_step:
#                 if abs(other_min-self_min) % self_step != 0:
#                     return False
#             else:
#                 self_val = self_min
#                 other_val = other_min
#                 intersection_finded = False
#                 while True:
#                     if self_val < other_val:
#                         self_val += self_step
#                     elif self_val > other_val:
#                         other_val += other_step
#                     else:
#                         intersection_finded = True
#                         break
#                 if not intersection_finded:
#                     return False
#         return True
#
#     def contains(self, point):
#         for index in range(len(self.__mins)):
#             self_min = self.__mins[index]
#             self_max = self.__maxs[index]
#             self_step = self.__steps[index]
#             coord_val = point.get_coord_val(index)
#             if (coord_val < self_min) or (coord_val > self_max):
#                 return False
#             if ((coord_val-self_min) % self_step) != 0:
#                 return False
#         return True
#
#     def get_time(self, point):
#         if not self.__point_is_valid(point):
#             raise RuntimeError("Area.set_time: the point may not belong to the area (point = " + point.__str__() + ")")
#         if not self.contains(point):
#             raise RuntimeError("Area.set_time: the point does not in the area (point = " + point.__str__() + ")")
#         point_index = self.__calculate_point_index(point)
#         if self.__time_already_set(point_index):
#             return self.__points_values[point_index]
#         else:
#             return Area.INVALID_TIME_VALUE
#
#     def set_time(self, point, time_value):
#         if not self.__point_is_valid(point):
#             raise RuntimeError("Area.set_time: the point may not belong to the area (point = " + point.__str__() + ")")
#         if not self.contains(point):
#             raise RuntimeError("Area.set_time: the point does not in the area (point = " + point.__str__() + ")")
#         index = self.__calculate_point_index(point)
#         if self.__time_already_set(index):
#             raise RuntimeError("Area.set_time: point value is already set (point: " + point.__str__()
#                                + ", new_value = " + str(time_value) + ", previous value = " + str(self.get_time(point))
#                                + ")")
#         self.__points_values[index] = time_value
#
#     def forced_set_time(self, point, time_value):
#         index = self.__calculate_point_index(point)
#         self.__points_values[index] = time_value
#
# # ----------------------------------------------------------------------------------------------------------------------
#     def __is_valid(self):
#         if not (len(self.__mins) and len(self.__maxs) and len(self.__steps)):
#             return False
#         for index in range(len(self.__mins)):
#             self_min = self.__mins[index]
#             self_max = self.__maxs[index]
#             self_step = self.__steps[index]
#             if self_min > self_max:
#                 return False
#             if (self_max-self_min) % self_step != 0:
#                 return False
#         return True
#
#     def __point_is_valid(self, point):
#         if point.get_coords_number() != len(self.__mins):
#             return False
#         for index in range(len(self.__mins)):
#             self_min = self.__mins[index]
#             self_max = self.__maxs[index]
#             self_step = self.__steps[index]
#             coord_val = point.get_coord_val(index)
#             if (coord_val < self_min) or (coord_val > self_max):
#                 return False
#             if (coord_val-self_min) % self_step != 0:
#                 return False
#         return True
#
#     def __calculate_points_number(self):
#         number = 1
#         for index in range(len(self.__mins)):
#             self_min = self.__mins[index]
#             self_max = self.__maxs[index]
#             self_step = self.__steps[index]
#             number *= int((self_max-self_min)/self_step + 1)
#         return number
#
#     def __calculate_point_index(self, point):  # FIXME: не учитывает хэмминг (выделяется много лишней памяти)
#         vals = list()
#         for index in range(len(self.__mins)):
#             self_min = self.__mins[index]
#             self_max = self.__maxs[index]
#             self_step = self.__steps[index]
#             coord_val = point.get_coord_val(index)
#             if len(vals) != 0:
#                 for val_index in range(len(vals)):
#                     vals[val_index] *= (int((self_max-self_min) / self_step) + 1)
#             vals.append(int((coord_val-self_min) / self_step))
#         return int(sum(vals))
#
#     def __time_already_set(self, point_index):
#         return self.__points_values[point_index] != Area.INVALID_TIME_VALUE