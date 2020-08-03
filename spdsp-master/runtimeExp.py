import numpy as np
import pandas as pd
from parameters import make_parameters
from model.discrete import discrete
from model.continuous import continuous
from model.special import special
from model.binned import binned


def runtime_expirement(num_trials=1):
    models = ['Continuous', 'Discrete', 'Special', 'Binned']
    numCert = [15]
    numCont = [10]
    numScen = [1000]
    numFixed = [5]
    machine_types = [1,2,3]
    jobTypes = [True, False]
    time_grans = ['day', 'week']
    gap = 0.03
    max_time = 60
    trials = trial_dictionairy(numCert, numCont, numScen, numFixed, jobTypes,
                               time_grans, models, num_trials)
    for t, trial in trials.items():
        print('---------------------------')
        print(100 * np.round(t/len(trials), 2), '% Complete')
        print(trial)
        param = make_parameters(num_cert=trial['num_cert'], num_cont=trial['num_cont'],
                                num_fixed=trial['num_fixed'], machine_types=machine_types,
                                num_scen=trial['sSize'], identical=trial['isIdentical'],
                                time_gran=trial['time_gran'])
        if run_conditions('Continuous', trial):
            results = continuous(p=param['Continuous'], gap=gap, max_time=max_time)
            trial = save_trial_results(trial, results)
        if run_conditions('Discrete', trial):
            results = discrete(p=param['Discrete'], gap=gap, max_time=max_time)                        
            trial = save_trial_results(trial, results)
        if run_conditions('Special', trial):
            results = special(p=param['Special'], gap=gap, max_time=max_time)
            trial = save_trial_results(trial, results)
        if run_conditions('Binned', trial):
            results = binned(p=param['Bin'], gap=gap, max_time=max_time)
            trial = save_trial_results(trial, results)
        trials[t] = trial
    output = pd.DataFrame.from_dict(trials, 'index')
    return output

def run_conditions(model, details):
    run = False
    num_jobs = details['num_cert'] + details['num_cont']
    if (model == 'Continuous' and
        details['model'] == model and 
        details['sSize'] == 1 and 
        details['time_gran'] == 'day' and 
        num_jobs <= 10):
        run = True
    if (model == 'Special' and
        details['model'] == model and
        details['isIdentical'] == True and 
        details['time_gran'] == 'day'):
        run = True
    if (model == 'Discrete' and
        details['model'] == model and
        details['sSize'] <= 5 and
        details['time_gran'] == 'day'):
        run = True
    if model == 'Binned' and details['model'] == model:
        run = True
    return run

def trial_dictionairy(numCert, numCont, numScen, numFixed, jobTypes, time_grans, models, num_trials):
    trials = {}
    for num_trial in range(1, num_trials+1):
        for num_cert in numCert:
            for num_cont in numCont:
                for num_fixed in numFixed:
                    for isIdentical in jobTypes:
                        for sSize in numScen:
                            for time_gran in time_grans:
                                for model in models:
                                    trials[len(trials)] = {'trial':num_trial,
                                                           'num_cert':num_cert,
                                                           'num_cont':num_cont,
                                                           'num_fixed':num_fixed,
                                                           'isIdentical':isIdentical,
                                                           'sSize':sSize,
                                                           'time_gran':time_gran,
                                                           'model': model,
                                                           'runtime': '',
                                                           'status': '',
                                                           'objective':'',}
    return trials

def save_trial_results(trial, results):
    trial['runtime'] = results['runtime']
    trial['status'] = results['status']
    trial['objective'] = results['obj']
    return trial

def mean_of_result(result):
    df = result.loc[result['runtime'] != 'infeasible']
    df = df.loc[df['runtime'] != '']
    df['runtime'] = df['runtime'].astype(float)
    #df['mipgap'] = df['mipgap'].astype(float)
    df = df.groupby(by=['model', 'sSize', 'isIdentical', 'time_gran'])
    df = df.agg(['mean', 'count', 'max'])[['runtime']]
    return df
