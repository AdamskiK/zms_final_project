import numpy as np
import simpy
import statistics as stat
import pandas as pd
from random import randint

# fixed variables
HORIZON = 3*365  # days
COST_OF_LORRY = 10**5  # PLN
AVERAGE_HOURLY_WAGE = 20  # PLN
AVERAGE_HOURLY_WAGE_STD = 5  # PLN
AVERAGE_LORRY_WEIGHT = 2000  # kg
AVERAGE_LOAD_WEIGHT = 2000  # kg
AVERAGE_LOAD_WEIGHT_STD = 1500  # kg
PRICE_PER_KG = 10  # PLN
SLEEP_TIME = 10  # sleeping time
LORRY_MALFUNCTION_DISTANCE = 10**5
LORRY_MALFUNCTION_DISTANCE_STD = 2*10**4
LORRY_REPAIR_COST = 5000
LORRY_REPAIR_COST_STD = 2000

# slower route
SLOW_WAY_DISTANCE = 620  # km
SLOW_WAY_DRIVE_TIME = 10  # hours
SLOW_WAY_STD = 1  # hours
SLOW_WAY_PETROL_COST = 5.12  # PLN
SLOW_WAY_FINE = 0  # PLN
SLOW_WAY_PETROL_USAGE = 10/100  # liters per 100 km
SLOW_WAY_REFUELING_FREQUENCY = 6
SLOW_WAY_REFUELING_LITER_RANGE = (15, 30)  # litres
SLOW_WAY_WEIGHT_LIMIT = 4500  # kg
SLOW_WAY_FINE_FREQ = 3
SLOW_WAY_FINE_PAID_BY_DRIVER_FREQ = 10
SLOW_WAY_LOAD_THEFT = 0.1


# faster route
FAST_WAY_DISTANCE = 450
FAST_WAY_DRIVE_TIME = 7.5
FAST_WAY_STD = 0.5
FAST_WAY_PETROL_COST = 5.43
FAST_WAY_FINE = 400
FAST_WAY_PETROL_USAGE = 8/100
FAST_WAY_REFUELING_FREQUENCY = 8
FAST_WAY_REFUELING_LITER_RANGE = (10, 20)
FAST_WAY_WEIGHT_LIMIT = 3500
FAST_WAY_FINE_FREQ = 0
FAST_WAY_FINE_PAID_BY_DRIVER_FREQ = 0
FAST_WAY_LOAD_THEFT = 0


class DriverSimulation:
    """
    Create a driver simulation
    """
    def __init__(self, driving_time, driving_time_std, distance, petrol_cost, petrol_usage, fine, refueling_frequency,
                 refueling_liter_range, weight_limit, fine_frequency, fine_frequency_paid_by_driver, theft_probability):
        self.driving_time = driving_time
        self.driving_time_std = driving_time_std
        self.distance = distance
        self.petrol_cost = petrol_cost
        self.petrol_usage = petrol_usage
        self.fine = fine
        self.refueling_frequency = refueling_frequency
        self.refueling_liter_range = refueling_liter_range
        self.weight_limit = weight_limit
        self.fine_frequency = fine_frequency
        self.fine_frequency_paid_by_driver = fine_frequency_paid_by_driver
        self.theft_probability = theft_probability
        self.hourly_wage = AVERAGE_HOURLY_WAGE
        self.hourly_wage_std = AVERAGE_HOURLY_WAGE_STD
        self.total_cost = 0
        self.total_profit = 0
        self.total_penalty_points = 0
        self.number_of_courses = 0
        self.fine_paid_number_of_courses = 0
        self.total_distance_after_repair = 0

    def run_simulation(self):
        """
        Run a simulation of a single driver

        :return: a total cost
        :rtype: float
        """
        env = simpy.Environment()
        env.process(self._simulation(env))
        env.run(until=24 * HORIZON)
        return self.total_cost, self.total_profit, self.number_of_courses

    def _simulation(self, env):
        """
        Run different steps of a simulation

        :param env: simpy.Environment
        :type env: simpy.core.Environment
        :return: yield different timeouts
        :rtype: env.timeout type
        """
        while True:
            # calculate costs, profits and a distance
            self.total_cost += self._calculate_costs()
            self.total_profit += self._calculate_profits()
            self.total_distance_after_repair += self.distance
            yield env.timeout(self.driving_time)

            self.number_of_courses += 1
    
    def _calculate_profit_weight(self):
        lorry_weight = np.random.normal(AVERAGE_LORRY_WEIGHT + AVERAGE_LOAD_WEIGHT, AVERAGE_LOAD_WEIGHT_STD)
        if lorry_weight > self.weight_limit:
            lorry_weight = self.weight_limit
        profit_weight = lorry_weight - AVERAGE_LORRY_WEIGHT
        return profit_weight
        
    def _calculate_profits(self):
        """
        Calculate total profits

        :return: a profit value
        :rtype: float
        """
        profit_weight = self._calculate_profit_weight()
        profit = profit_weight * PRICE_PER_KG
        profit -= self._cost_load_theft()  # loss on a theft - has to be here to be coherent
        return profit
    
    def _calculate_costs(self):
        """
        Sum up a whole cost per one run

        :return: a cost
        :rtype: float
        """
        cost = 0
        cost += self._cost_route_fine()
        cost += self._cost_petrol()
        cost += self._cost_wage()
        cost += self._cost_refueling()
        cost += self._cost_caught_by_police()
        cost += self._cost_vehicle_malfunction()
        return cost

    def _cost_route_fine(self):
        """
        Calculate a fine cost

        :return: a fine cost
        :rtype: integer
        """
        return self.fine

    def _cost_petrol(self):
        """
        Calculate a petrol cost

        :return: a petrol cost
        :rtype: float
        """
        return self.distance * self.petrol_usage * self.petrol_cost

    def _cost_wage(self):
        """
        Calculate a wage cost

        :return: a wage cost
        :rtype: float
        """
        avg_drive_time = np.random.normal(self.driving_time, self.driving_time_std)
        hourly_wage = np.random.normal(self.hourly_wage, self.hourly_wage_std)
        total = avg_drive_time * hourly_wage
        return total

    def _cost_refueling(self):
        """
        Calculate refueling costs during a course

        :return: a refueling cost
        :rtype: integer
        """
        if self.number_of_courses % self.refueling_frequency == 0 & self.number_of_courses != 0:
            lowest_amount = self.refueling_liter_range[0]  # take a minimum value
            highest_amount = self.refueling_liter_range[1]  # take a maximum value
            refueled_petrol = randint(lowest_amount, highest_amount)
            cost = refueled_petrol * self.petrol_cost
            return cost
        else:
            return 0

    def _cost_caught_by_police(self):
        """
        Calculate a cost and penalty points if a driver has been caught by police

        :return: a fine value
        :rtype: integer
        """
        if self.fine_frequency != 0:
            if self.number_of_courses % self.fine_frequency == 0 and self.number_of_courses != 0:
                if self.number_of_courses % self.fine_frequency_paid_by_driver == 0 and self.number_of_courses != 0:
                    self.fine_paid_number_of_courses += 1
                    fine_value = np.random.choice([100, 200, 500], p=[0.25, 0.4, 0.35])
                    self.total_penalty_points += self._add_penalty_points()  # adding penalty points
                    return fine_value
                else:
                    return 0
            else:
                return 0
        else:
            return 0

    def _cost_vehicle_malfunction(self):
        malfunction_distance = np.random.normal(LORRY_MALFUNCTION_DISTANCE, LORRY_MALFUNCTION_DISTANCE_STD)
        if self.total_distance_after_repair > malfunction_distance:
            repair_cost = np.random.normal(LORRY_REPAIR_COST, LORRY_REPAIR_COST_STD)
            return repair_cost
        else:
            return 0

    def _cost_load_theft(self):
        """
        Calculate a theft loss

        :return: a loss
        :rtype: integer
        """
        theft_prob = self.theft_probability
        theft = np.random.choice([0, 1], p=[1-theft_prob, theft_prob])
        if theft == 1:
            cost = self._calculate_profit_weight() * PRICE_PER_KG
            return cost
        else:
            return 0

    @staticmethod
    def _add_penalty_points():
        """
        Calculate penalty points

        :return: a number of penalty points
        :rtype: integer
        """
        return randint(1, 5)


class Simulate:
    """
    Run a simulation with N drivers
    """
    def __init__(self,  driving_time, driving_time_std, distance, petrol_cost, petrol_usage, fine, refueling_frequency,
                 refueling_liter_range, weight_limit, fine_frequency, fine_frequency_paid_by_driver, theft_probability,
                 n_drivers):
        self.driving_time = driving_time
        self.driving_time_std = driving_time_std
        self.distance = distance
        self.petrol_cost = petrol_cost
        self.petrol_usage = petrol_usage
        self.fine = fine
        self.refueling_frequency = refueling_frequency
        self.refueling_liter_range = refueling_liter_range
        self.weight_limit = weight_limit
        self.fine_frequency = fine_frequency
        self.fine_frequency_paid_by_driver = fine_frequency_paid_by_driver
        self.theft_probability = theft_probability
        self.n_drivers = n_drivers

    def generate_cost(self):
        """
        Generate a cost/profit while doing simulations for n drivers

        :return: total_cost, total_profit, number_of_courses
        :rtype: float, float, integer
        """
        i = 1
        total_cost = 0
        total_profit = 0
        number_of_courses = 0
        while i <= self.n_drivers:
            inst = DriverSimulation(self.driving_time,
                                    self.driving_time_std,
                                    self.distance,
                                    self.petrol_cost,
                                    self.petrol_usage,
                                    self.fine,
                                    self.refueling_frequency,
                                    self.refueling_liter_range,
                                    self.weight_limit,
                                    self.fine_frequency,
                                    self.fine_frequency_paid_by_driver,
                                    self.theft_probability)
            result = inst.run_simulation()
            total_cost += result[0]
            total_profit += result[1]
            number_of_courses += result[2]
            i += 1
        return total_cost, total_profit, number_of_courses


def main():
    # slow way simulation
    slow_way_simulation = Simulate(SLOW_WAY_DRIVE_TIME,
                                   SLOW_WAY_STD,
                                   SLOW_WAY_DISTANCE,
                                   SLOW_WAY_PETROL_COST,
                                   SLOW_WAY_PETROL_USAGE,
                                   SLOW_WAY_FINE,
                                   SLOW_WAY_REFUELING_FREQUENCY,
                                   SLOW_WAY_REFUELING_LITER_RANGE,
                                   SLOW_WAY_WEIGHT_LIMIT,
                                   SLOW_WAY_FINE_FREQ,
                                   SLOW_WAY_FINE_PAID_BY_DRIVER_FREQ,
                                   SLOW_WAY_LOAD_THEFT,
                                   n_drivers=3)
    t_cost, t_profit, n_courses = slow_way_simulation.generate_cost()
    print(f"slow_way_simulation - total cost equals to: {round(t_cost, 2)}")
    print(f"slow_way_simulation - total profit equals to: {round(t_profit, 2)}")
    print(f"slow_way_simulation - n_courses equal to: {round(n_courses, 2)}")

    # fast way simulation
    fast_way_simulation = Simulate(FAST_WAY_DRIVE_TIME,
                                   FAST_WAY_STD,
                                   FAST_WAY_DISTANCE,
                                   FAST_WAY_PETROL_COST,
                                   FAST_WAY_PETROL_USAGE,
                                   FAST_WAY_FINE,
                                   FAST_WAY_REFUELING_FREQUENCY,
                                   FAST_WAY_REFUELING_LITER_RANGE,
                                   FAST_WAY_WEIGHT_LIMIT,
                                   FAST_WAY_FINE_FREQ,
                                   FAST_WAY_FINE_PAID_BY_DRIVER_FREQ,
                                   FAST_WAY_LOAD_THEFT,
                                   n_drivers=3)
    t_cost, t_profit, n_courses = fast_way_simulation.generate_cost()
    print(f"fast_way_simulation - total cost equals to: {round(t_cost, 2)}")
    print(f"fast_way_simulation - total profit equals to: {round(t_profit, 2)}")
    print(f"slow_way_simulation - n_courses equal to: {round(n_courses, 2)}")


if __name__ == '__main__':
    main()
