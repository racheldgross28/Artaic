import numpy as np
import pandas as pd
import itertools

np.random.seed(0) #setting random variables so they are the same everytime the code is run

def reduce_realizations(poa, realizations):
    """
    The purpose of this function is to:
       the following block of code removes the portion of realizations which
       describe a realization which contains two jobs with a poa greater than .95
       to be declined
    """
    r = pd.DataFrame(realizations)
    poa_remove = list(np.where(poa >= .95)[0])
    remove_couples = [[i, j] for i in poa_remove for j in poa_remove if i != j]
    for couple in remove_couples:
        r = r.drop(r.loc[(r[couple[0]] == 0) & (r[couple[1]] == 0)].index)
    return r.values

def get_realizations(jobs, conf_int=0.95):
    if type(jobs) != list:
        if type(jobs) == dict:
            jobs = list(jobs.values())
        else:
            jobs = list(jobs)
    counter = [1 if job.poa < .999 else 0 for job in jobs]
    trunc_poa = np.array([job.poa for job in jobs if job.poa < .999])
    poa = np.array([job.poa for job in jobs])
    n = len(trunc_poa) # get the size of the job set
    realizations = load_realization(n) # load realizations based on size of job set
    realizations = reduce_realizations(trunc_poa, realizations)
    # the following merges the outcome of the contingent jobs for each realization
    # with the known confirmed jobs
    for i,j in enumerate(counter):
        if j == 0: # if the job is certain, insert it into the realization matrix
            realizations = np.insert(realizations, i, 1, axis=1)
    results = realization_probabilities(poa, realizations)
    cut = results[results['Cum PoO'] <= conf_int]
    return cut

def realization_probabilities(poa, realizations):
    prob_of_occs = [] # initilize data set
    inv_poa = poa - 1 # get probabilities of each job getting declined
    real_probs = realizations * poa # wap
    real_probs[np.where(real_probs==0)] = 1
    pr = np.array([np.prod(i) for i in real_probs])
    inv_real = realizations - 1
    inv_probs = inv_real * inv_poa
    inv_probs[np.where(inv_probs==0)] = 1
    ir = np.array([np.prod(i) for i in inv_probs])
    prob_of_occs = pr * ir
    results = pd.DataFrame(index=[i for i in range(len(prob_of_occs))], columns=['PoO', 'Cum PoO'])
    results['PoO'] = prob_of_occs
    results['realization'] = realizations.tolist()
    results = results.sort_values(by='PoO', ascending=False)
    results['Cum PoO'] = results.PoO.cumsum()
    return results

def mc_realizations(jobs, num_samples=20000):
    """
    Takes LIST of job objects
    
    The purpose of this function is to:
       Randomly generate a large set of realizations based on a set of jobs and
       their respective prob of acceptances. For each realization, the list of
       the job names that are realized in that are returned 
    """
    if type(jobs) != list:
        if type(jobs) == dict:
            jobs = list(jobs.values())
        else:
            jobs = list(jobs)
    poa = np.array([job.poa for job in jobs])
    results = {}
    for sample in range(num_samples):
        randoms = np.random.random(len(poa))
        realization = [j for j,p,r in zip(jobs, poa, randoms) if p > r]
        results[sample] = realization
    return results

def prep_bjs(jobs, num_samples=1000):
    """
    The purpose of this function is to:
        Create an array of binary variables which represent if job j exists in
        realization s. 1 means it exists, 0 means it doesn't. This is based on
        each job's probability of acceptance
    """
    if type(jobs) != list:
        if type(jobs) == dict:
            jobs = list(jobs.values())
        else:
            jobs = list(jobs)
    poa = np.array([job.poa for job in jobs])
    results = {}
    for sample in range(num_samples):
        randoms = np.random.random(len(poa))
        realization = [1 if p > r else 0 for j,p,r in zip(jobs, poa, randoms)]
        results[sample] = realization
    results = pd.DataFrame.from_dict(results, 'index')
    results.columns = [j.name for j in jobs]
    return results

def b_js_from_CI(jobs, conf_int=0.9):
    cut = get_realizations(jobs, conf_int=conf_int)
    q_s = {}
    b_js= {}
    for k,v in cut.iterrows():
        for j,b in enumerate(v.realization):
            if j+1 not in b_js.keys():
                b_js[j+1] = {}
            b_js[j+1][len(b_js[j+1])] = b
        q_s[len(q_s)] = np.round(v.PoO,6)
    return q_s, b_js


def b_js_from_most_likely(jobs, num_scen):
    cut = get_realizations(jobs, conf_int=1.01).iloc[:num_scen]
    q_s = {}
    b_js= {}
    for k,v in cut.iterrows():
        for j,b in enumerate(v.realization):
            if j+1 not in b_js.keys():
                b_js[j+1] = {}
            b_js[j+1][len(b_js[j+1])] = b
        q_s[len(q_s)] = np.round(v.PoO,6)
    return q_s, b_js
    

def preprocess(max_template=21):
    """
    The purpose of this function is to:
        Create an arroy of binary variables which represents the mapping
        of all possible realizations. An array of this mapping is created for
        each number of possible contingent jobs within the range of the input
        variable, max_template. These arrays are stored so they can be quickly
        retrieved, when needed.
    """
    for n in range(1,max_template):
        realizations = np.array([list(i) for i in itertools.product([0, 1], repeat=n)])
        save_as = '\\real' + str(n) + '.npy'
        np.save(r'C:\Users\malla\OneDrive\Artaic\Code\real'+save_as, realizations)

def load_realization(num_cont):
    filename = 'real' + str(num_cont) + '.npy'
    realizations = np.load(r'real\\' + filename)
    return realizations



