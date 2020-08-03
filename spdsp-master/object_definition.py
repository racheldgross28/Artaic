import numpy as np
import pandas as pd


job_columns = ['name', 'size', 'mat', 'set', 'poa', 'r_j', 'e_j', 'd_j', 'g_j', 'c_j', 'h_j']
probs = [.25, .75, .9, .95]
materials = ['.375-VG', '.5-CG', '.5-SG', '.5-UP', '.75-VG', '1-CG', '1-GP', '1-SG', '1-UP']


machine_info = {m:{material:int(m/float(material.split('-')[0])) for material in materials} for m in [1,2,3,4]}

machine_base = {1:1, 2:2, 3:3}

# unit of time == hours
hour_per_day = 10
day_per_week = 5
hour_per_week = hour_per_day * day_per_week


class Job(object):
    
    def __init__(self, info):
        self.name = info['name']
        self.size = info['size']        # measured in units
        self.mat = info['mat']          # material type
        self.set = info['set']          # Accepted, Contingent, etc.
        self.poa = info['poa']          # probability of acceptance
        self.c_j = info['c_j']          # cost for time period tardy
        self.h_j = info['h_j']          # cost for time period early
        self.r_j = info['r_j']          # release date
        self.e_j = info['e_j']          # earliest acceptable delivery date
        self.d_j = info['d_j']          # desired due date
        self.g_j = info['g_j']          # guaranteed delivery date
        self.p_j = 10                   # penalty for delivery after guaranteed date

class Machine(object):
    
    def __init__(self, info):
        self.name = info['name']
        self.base_rate = info['base_rate']


def generate_jobs(num_cert, num_cont, identical=False, time_gran='day', machine_types=[1,1,2,3]):
    num_jobs = num_cert + num_cont
    size_set_partition = num_cert - num_cont
    variable_partition = ['J', 'C'] * num_cont
    np.random.shuffle(variable_partition)
    set_partition = ['J'] * size_set_partition
    job_sets = set_partition + variable_partition
    data = pd.DataFrame(index=[i for i in range(1,num_jobs+1)], columns=job_columns)
    data.name = data.index
    if identical == False:
        data.size = np.round(np.random.randint(1,5, num_jobs))
        data.mat = np.random.choice(materials, num_jobs)
    elif identical == True:
        data.size = np.random.randint(1,5)
        data.mat = np.random.choice(materials)  
    data.set = job_sets
    data.poa = [1 if j_set == 'J' else np.random.choice(probs) for j_set in data.set]

    period = {'week':day_per_week, 'day':1}
    
    
    relative_wc = sum([machine_info[1][j.mat] * j['size'] for i,j in data.iterrows()])
    capacity = sum([1/m for m in machine_types])
    T = int(relative_wc / capacity) 
    
    print(relative_wc, '//', capacity, '=', T)
    
    data.r_j = sorted((np.random.randint(0, np.ceil(T/3), num_jobs) / period[time_gran]).astype(int))
    data.e_j = data.r_j + np.ceil(np.random.randint(0, T/4, num_jobs) / period[time_gran]).astype(int)
    data.d_j = data.e_j + np.ceil(np.random.randint(3, 3+T/3, num_jobs) / period[time_gran]).astype(int)
    data.g_j = data.d_j + np.ceil(np.random.randint(5, 5+T/2, num_jobs) / period[time_gran]).astype(int)
    data.c_j = np.random.randint(1, 10, num_jobs) * period[time_gran]
    data.h_j = data['size'] * period[time_gran]
    data_dict = data.to_dict(orient='index')
    jobs = {key: Job(values) for key,values in data_dict.items()}
    return jobs





