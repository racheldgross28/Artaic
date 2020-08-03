import numpy as np
from object_definition import generate_jobs, machine_info
import realizations as real

p_rate_conv = {'hour':1}
hour_per_day = 10
day_per_week = 5
p_rate_conv['day'] = p_rate_conv['hour'] * hour_per_day
p_rate_conv['week'] = p_rate_conv['day'] * day_per_week

def make_parameters(num_cert=10, num_cont=5, num_fixed=5, machine_types=[1,1,2,2],
                    num_scen=1, scen_method='random', conf_int=0.95,
                    identical=False, time_gran='day', ):
    jobs = generate_jobs(num_cert, num_cont, identical, time_gran, machine_types)
    param = {'Continuous':continuous_parameters(jobs=jobs,
                                                num_scen=num_scen,
                                                num_fixed=num_fixed,
                                                machine_types=machine_types,
                                                scen_method=scen_method,
                                                conf_int=conf_int),
             'Discrete':discrete_parameters(jobs=jobs,
                                            num_scen=num_scen,
                                            num_fixed=num_fixed,
                                            time_gran=time_gran,
                                            scen_method=scen_method,
                                            conf_int=conf_int,
                                            machine_types=machine_types),
             'Special':special_parameters(jobs=jobs,
                                          num_scen=num_scen,
                                          num_fixed=num_fixed,
                                          time_gran=time_gran,
                                          scen_method=scen_method,
                                          conf_int=conf_int,
                                          machine_types=machine_types),
             'Bin':bin_parameters(jobs=jobs,
                                       num_scen=num_scen,
                                       num_fixed=num_fixed,
                                       time_gran=time_gran,
                                       scen_method=scen_method,
                                       conf_int=conf_int,
                                       machine_types=machine_types),
    }
    return param
    
def continuous_parameters(jobs, num_scen, num_fixed, machine_types=None,
                          scen_method='random', conf_int=0.95):
    jobs = list(jobs.values())
    J = [j.name for j in jobs]
    F = sorted([j.name for j in jobs if j.poa >= .99])[:num_fixed] #fixed job conditions
    NF = [j for j in J if j not in F]
    
    M = [m for m in range(len(machine_types))]
    K = [k for k in range(len(J))]
    q_s, b_js, S = make_scenarios(scen_method, jobs, num_scen, conf_int)
    
    w_jm = {(j.name,m): int(j.size * machine_info[m_type][j.mat])
            for j in jobs for m, m_type in enumerate(machine_types)}
    param = {'jobs':jobs, 'J':J, 'F':F, 'NF':NF, 'K':K, 'M':M, 'S':S,
             'w_jm':w_jm, 'b_js':b_js, 'q_s':q_s}
    return param

def special_parameters(jobs, num_scen, num_fixed, time_gran, scen_method='random',
                       conf_int=0.95, p_rate_conv=p_rate_conv, machine_types=[1,1,2,3]):
    work_content = len(jobs)
    jobs = list(jobs.values())
    
    J = [j.name for j in jobs] #job names
    F = sorted([j.name for j in jobs if j.poa >= .99])[:num_fixed] #fixed job conditions
    NF = [j for j in J if j not in F]
    M = [m for m in range(len(machine_types))]    # machine names
    K = [k for k in range(1,work_content)] # name of bins  
    q_s, b_js, S = make_scenarios(scen_method, jobs, num_scen, conf_int)
    w = {m: jobs[0].size * machine_info[m_type][jobs[0].mat] for m, m_type in enumerate(machine_types)} 
    t_mk = {(m,k): k * w[m] / hour_per_day for m in M for k in K}
    p_jmk = {(j.name,m,k): j.c_j * max(0, t_mk[m,k] - j.d_j) +
             j.h_j * max(0, j.e_j - t_mk[m,k]) + j.p_j * max(0, t_mk[m,k] - j.g_j)
             for m in M for k in K for j in jobs}
    param = {'jobs':jobs, 'J':J, 'M':M, 'F':F, 'NF':NF, 'S':S, 'K':K,
             't_mk':t_mk, 'p_jmk':p_jmk, 'b_js':b_js,  'q_s':q_s}
    return param

def discrete_parameters(jobs, num_scen, num_fixed, time_gran,machine_types=[1,1,2,3],
                        scen_method='random', conf_int=0.95, p_rate_conv=p_rate_conv):
    work_content = int(sum([job.size for job in jobs.values()]))
    jobs = list(jobs.values())
    J = [j.name for j in jobs]
    F = sorted([j.name for j in jobs if j.poa >= .99])[:num_fixed] #fixed job conditions
    NF = [j.name for j in jobs if j.name not in F]

    M = [m for m in range(len(machine_types))]
    K = [k for k in range(0,work_content)]
    q_s, b_js, S = make_scenarios(scen_method, jobs, num_scen, conf_int)

    w_jm = {(j.name,m): j.size * machine_info[m_type][j.mat]
            for j in jobs for m, m_type in enumerate(machine_types)}
    t_mk = {(m,k): k / hour_per_day for m in M for k in K}
    p_jmk = {(j.name,m,k): j.c_j * max(0, t_mk[m,k] - j.d_j) +
             j.h_j * max(0, j.e_j - t_mk[m,k]) + j.p_j * max(0, t_mk[m,k] - j.g_j)
             for m in M for k in K for j in jobs}
    param = {'jobs':jobs, 'J':J, 'M':M, 'F':F, 'NF':NF, 'S':S, 'K':K, 'q_s':q_s,
             'w_jm':w_jm, 't_mk':t_mk, 'p_jmk':p_jmk, 'b_js':b_js}
    return param

def bin_parameters(jobs, num_scen, num_fixed, time_gran, conf_int=0.95,
                   scen_method='random', p_rate_conv=p_rate_conv, machine_types=None):
    
    work_content = int(sum([job.size * machine_info[2][job.mat] for job in jobs.values()]) /p_rate_conv[time_gran]) #!!!!!
    
    jobs = list(jobs.values())
    J = [j.name for j in jobs]              # job names
    F = sorted([j.name for j in jobs if j.poa >= .99])[:num_fixed] #fixed job conditions
    NF = [j.name for j in jobs if j.name not in F]

    M = [m for m in range(len(machine_types))]    # machine names
    K = [k for k in range(1,work_content)]# name of bins  
    q_s, b_js, S = make_scenarios(scen_method, jobs, num_scen, conf_int)

    C = {m:p_rate_conv[time_gran] for m in M}    # units of work a machine can handle per "bin" time period  

    w_jm = {(j.name,m): j.size * machine_info[m_type][j.mat] for j in jobs for m, m_type in enumerate(machine_types)}  
    
    t_mk = {(m,k): k * p_rate_conv[time_gran] for m in M for k in K}
    
    p_jmk = {(j.name,m,k): j.c_j * max(0, t_mk[m,k] - j.d_j) +
             j.h_j * max(0, j.e_j - t_mk[m,k]) + j.p_j * max(0, t_mk[m,k] - j.g_j)
             for m in M for k in K for j in jobs}
    param = {'jobs':jobs, 'J':J, 'M':M, 'F':F, 'NF':NF, 'S':S, 'K':K,
             'C':C, 'w_jm':w_jm, 't_mk':t_mk, 'p_jmk':p_jmk, 
             'b_js':b_js, 'q_s':q_s}
    return param

def make_scenarios(scen_method, jobs, num_scen, conf_int):
    if scen_method == 'random':
        b_js = real.prep_bjs(jobs, num_samples=num_scen).to_dict() # realization data
        S  = [i for i in range(num_scen)] # scenario names
        q_s = {s: 1/num_scen for s in S}
    elif scen_method =='conf_int':
        q_s, b_js = real.b_js_from_CI(jobs, conf_int=conf_int)
        S = [i for i in range(len(b_js[1]))]
    elif scen_method =='most_likely':
        q_s, b_js = real.b_js_from_most_likely(jobs, num_scen=num_scen)
        S = [i for i in range(num_scen)]          
    return q_s, b_js, S


