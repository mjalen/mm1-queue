import numpy as np
import pandas as pd
import math as math
import sys as sys
from tqdm import tqdm

# the queue class
class MM1Queue:
    def __init__(self, interarrival, service_time):
        # the functions for finding the next arrival/service times, given the current time.
        self.next_arrival = lambda t: t + np.random.exponential(1/interarrival) 
        self.next_service =  lambda t: t + np.random.exponential(1/service_time)

    def run(self, hours=500):
        # stores the actual M/M/1 simulation parameters for the _current_ iteration
        system = {
            'current_time': 0,
            'next_arrival': self.next_arrival(0),
            'next_service': np.infty,
            'utilization': 0,
            'queue': 0,
            'ratio_of_simulation': 0,
            'queue_time': 0,
            'system_time': 0
        }

        results = pd.DataFrame([system])

        # simulation loop, ends after 500 hours has passed.
        while system['current_time'] <= hours:
            dt = 0 # time delta between last and current system. calculated later.

            # maintain a copy of the last system iteration. 
            # done this way as opposed to indexing the results table to avoid misindexing errors 
            last_system = system.copy()

            # if next action is new arrival
            is_an_arrival_next = (system['next_arrival'] < system['next_service']) 
            if is_an_arrival_next:
                dt = system['next_arrival'] - system['current_time'] 

                system['current_time'] = system['next_arrival']
                system['next_arrival'] = self.next_arrival(system['current_time'])

                # if the server is not busy, assign them to the new arrival. 
                is_server_busy = (system['utilization'] == 0)
                if is_server_busy:
                    system['utilization'] = 1
                    system['next_service'] = self.next_service(system['current_time'])

                # if the server is busy, assign the arrival to the queue
                else:
                    system['queue'] = system['queue'] + 1

            # otherwise, serve next in queue.
            else:
                dt = system['next_service'] - system['current_time'] 
                system['current_time'] = system['next_service']

                # if there is no customer in either the queue or being served
                is_queue_empty = (system['queue'] == 0)
                if is_queue_empty:
                    system['utilization'] = 0
                    system['next_service'] = np.infty

                # otherwise, there must be a customer to serve.
                else: 
                    system['queue'] = system['queue'] - 1
                    system['next_service'] = self.next_service(system['current_time'])

            # ratio of simulation from the previous iteration to the current. 
            # this is the ratio for the PREVIOUS iteration, and will be rolled-back after simulation.
            system['ratio_of_simulation'] = dt / 500

            # calculate the wait times from the previous to current iteration, using the time delta. 
            system['queue_time'] = 2 * dt * last_system['queue']
            system['system_time'] = 2 * dt * (last_system['queue'] + last_system['utilization'])

            # store the current system state as a new row in the results table.
            results = pd.concat([results, pd.DataFrame([system])])

        # roll the ratio of simulation back one row, where the first row ratio becomes the ratio of the last row.
        # ie. [ 0.1 0.2 0.3 0.4 ] becomes [ 0.2 0.3 0.4 0.1 ]
        results['ratio_of_simulation'] = np.roll(results['ratio_of_simulation'], -1)

        # return the entire history of the simulation.
        return results

if __name__ == "__main__":
    if not "-f" in sys.argv and not "-r" in sys.argv:
        sys.exit(100) # terminate if an output file is not defined        

    # retrieve the number of desired replications from program arguments.
    n_replications = int(sys.argv[sys.argv.index("-r") + 1])

    # a critical value lookup table used later.
    critical_value = {
        30: 2.045,
        100: 1.984,
        1000: 1.962
    }

    # instantiate a new queue simulation.
    sim = MM1Queue(3, 4)

    # instantiate a new table for storing the data of each replication. 
    repls = pd.DataFrame(columns=np.array(["queue length", "system length", "queue wait", "system wait", "utilization"]))

    # execute replications
    for r in tqdm(range(n_replications)):
        # get results of the current replication
        res = sim.run(hours=500)

        # find averages from the current replication
        params = {
            "queue length": np.dot(res['ratio_of_simulation'], res["queue"]), # expected value of queue length
            "system length": np.dot(res['ratio_of_simulation'],  (res["queue"] + res['utilization'])), # expected value of system length
            "queue wait": np.average(res["queue_time"]), # expected queue wait time
            "system wait": np.average(res["system_time"]), # expected system wait time
            "utilization": np.dot(res['ratio_of_simulation'], res["utilization"]) # expected % time the server is busy.
        }

        # store replication data in a new row.
        repls = pd.concat([repls, pd.DataFrame([params])])

    # define vector-valued functions for calculating confidence intervals.
    up_conf = np.vectorize(lambda m, v: m + critical_value[n_replications] * math.sqrt(v / n_replications))
    low_conf = np.vectorize(lambda m, v: m - critical_value[n_replications] * math.sqrt(v / n_replications))

    # assume a null hypothesis that mu = mu_theory and an alternate hypothesis that mu != mu_theory.
    # this is done by checking if a given mean vector is within the input upper/lower boundary vectors. 
    is_null_rejected = np.vectorize(lambda m, low, up: (m < low) or (up < m))

    # calculate mean and variance of each replication average parameters.
    averages = repls[:].mean()
    variance = repls[:].var()
    averages.name = "average"
    variance.name = "variance"

    # calculate confidence intervals
    lower_bound_confidence = pd.Series(low_conf(averages, variance), name="lower bound confidence", index=averages.index)
    upper_bound_confidence = pd.Series(up_conf(averages, variance), name="upper bound confidence", index=averages.index)

    # store the theoretical mean values.
    theory_mean = pd.Series([2.25, 3, 0.75, 1, 0.75], name="theory", index=averages.index)

    buffer = {
        30: [2.23, 2.98, 0.75, 0.99, 0.75],
        100: [2.199, 2.949, 0.733, 0.983, 0.75],
        1000: [2.23, 2.98, 0.74, 0.99, 0.75]
    }
    anylogic_mean = pd.Series(buffer[n_replications], name=f'anylogic ({n_replications} repls)', index=averages.index)

    # hypothesis check confidence intervals with the theoretical values.
    reject_theory = pd.Series(is_null_rejected(theory_mean, lower_bound_confidence, upper_bound_confidence), name="reject theory", index=averages.index)
    reject_anylogic = pd.Series(is_null_rejected(anylogic_mean, lower_bound_confidence, upper_bound_confidence), name="reject anylogic", index=averages.index) 

    # store all final data in a new table.
    results = pd.DataFrame([averages, theory_mean, anylogic_mean, variance, lower_bound_confidence, upper_bound_confidence, reject_theory, reject_anylogic])

    # save the table to an Excel spreadsheet with the provided program argument PATH.
    results.T.to_excel(sys.argv[sys.argv.index("-f") + 1])


