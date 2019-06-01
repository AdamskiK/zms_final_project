import numpy as np
import simpy

from random import randint


HORIZON = 3*365  # days
KONTRAKT_VALUE = 3*10**7  # contract value in PLN
SLEEP_TIME = 10  # sleeping time
AVERAGE_LORRY_WEIGHT = 2000  # kg
AVERAGE_LOAD_WEIGHT = 1200  # kg
AVERAGE_LOAD_WEIGHT_STD = 500  # kg
AVERAGE_HOURLY_WAGE = 20  # PLN
AVERAGE_HOURLY_WAGE_STD = 0.02  # PLN


# slower route
SLOW_WAY_DISTANCE = 620  # km
SLOW_WAY_DRIVE_TIME = 10  # hours
SLOW_WAY_STD = 1  # hours
SLOW_WAY_PETROL_COST = 5.12  # PLN
SLOW_WAY_FINE = 0  # PLN
SLOW_WAY_PETROL_USAGE = 10/100  # liters per 100 km
SLOW_WAY_REFUELING_FREQUENCY = 10  # every 10 runs
SLOW_REFUELING_LITER_RANGE = (15, 30)


# faster route
FAST_WAY_DISTANCE = 450
FAST_WAY_DRIVE_TIME = 7.5
FAST_WAY_STD = 0.5
FAST_WAY_PETROL_COST = 5.43
FAST_WAY_FINE = 400
FAST_WAY_PETROL_USAGE = 8/100
FAST_WAY_REFUELING_FREQUENCY = 8
FAST_REFUELING_LITER_RANGE = (10, 20)


class DriverSimulation:
    """
    Create a driver simulation
    """
    def __init__(self, driving_time, driving_time_std, distance, petrol_cost, petrol_usage, fine, refueling_frequency,
                 refueling_liter_range, hourly_wage, hourly_wage_std):
        self.driving_time = driving_time
        self.driving_time_std = driving_time_std
        self.distance = distance
        self.petrol_cost = petrol_cost
        self.petrol_usage = petrol_usage
        self.hourly_wage = hourly_wage
        self.hourly_wage_std = hourly_wage_std
        self.fine = fine
        self.refueling_frequency = refueling_frequency
        self.refueling_liter_range = refueling_liter_range
        self.total_cost = []
        self.total_penalty_points = 0
        self.counter = 0

    def run_simulation(self):
        """
        Run a simulation of a single driver

        :return: a total cost
        :rtype: float
        """
        env = simpy.Environment()
        print(type(env))
        env.process(self._simulation(env))
        env.run(until=24 * HORIZON)
        return sum(self.total_cost)

    def _simulation(self, env):
        """
        Run different steps of a simulation

        :param env: simpy.Environment
        :type env: simpy.core.Environment
        :return: yield different timeouts
        :rtype: env.timeout type
        """
        while True:
            # calculate fixed-driving costs
            self.total_cost.append(self._calculate_costs())
            self.total_penalty_points += self._add_penalty_points()
            yield env.timeout(self.driving_time)

            # check if a number of penalty points has been exceeded
            if self.total_penalty_points >= 24:
                cought_by_police = env.process(self._sentence_serving(env))
                yield cought_by_police
                self.total_penalty_points = 0

            # the driver must rest after driving
            free_time = np.random.normal(SLEEP_TIME, 2)
            yield env.timeout(free_time)
            self.counter += 1

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
        cost += self._refueling_cost()
        return cost

    def _refueling_cost(self):
        """
        Calculate refueling costs during a course

        :return: a refueling cost
        :rtype: integer
        """
        if self.counter % self.refueling_frequency == 0:
            lowest_amount = self.refueling_liter_range[0]  # take a minimum value
            highest_amount = self.refueling_liter_range[1]  # take a maximum value
            refueled_petrol = randint(lowest_amount, highest_amount)
            cost = refueled_petrol * self.petrol_cost
            return cost
        else:
            return 0

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
        return avg_drive_time * hourly_wage

    @staticmethod
    def _sentence_serving(env):
        """
        Simulate sentence serving by driver after exceeding maximum number of 24 penalty points

        :param env: simpy.Environment
        :type env: simpy.core.Environment
        :return: a time out of 365 days
        :rtype: yields a sentence time
        """
        print(f"started serving a sentence at {env.now/24}")
        yield env.timeout(24*365)
        print(f"finished serving a sentence at {env.now/24}")

    @staticmethod
    def _add_penalty_points():
        """
        Calculate penalty points

        :return: a number of penalty points
        :rtype: integer
        """
        return randint(1, 3)


class Simulate:
    """
    Run a simulation with N drivers
    """
    def __init__(self, n_drivers):
        self.n_drivers = n_drivers

    def generate_cost(self):
        """
        Generate a cost while doing simulations for n drivers

        :return:
        :rtype:
        """
        i = 1
        total_cost = 0
        while i <= self.n_drivers:
            inst = DriverSimulation(FAST_WAY_DRIVE_TIME,
                                    FAST_WAY_STD,
                                    FAST_WAY_DISTANCE,
                                    FAST_WAY_PETROL_COST,
                                    FAST_WAY_PETROL_USAGE,
                                    FAST_WAY_FINE,
                                    FAST_WAY_REFUELING_FREQUENCY,
                                    FAST_REFUELING_LITER_RANGE,
                                    AVERAGE_HOURLY_WAGE,
                                    AVERAGE_HOURLY_WAGE_STD)
            total_cost += inst.run_simulation()
            i += 1
        return total_cost


def main():
    simulation = Simulate(n_drivers=2)
    t_cost = simulation.generate_cost()
    print(f"total cost equals to: {round(t_cost, 2)}")


if __name__ == '__main__':
    main()
