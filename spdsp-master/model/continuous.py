import gurobipy as gp
from gurobipy import GRB


import parameters
param = parameters.make_parameters(num_cert=5, num_cont=5, num_scen=2, num_fixed=2)

gap = 0.01
max_time = 60

def continuous(p=param['Continuous'], gap=gap, max_time=max_time):
    output = {'runtime':'infeasible', 'status':'infeasible', 'var':'infeasible',
              'obj':'infeasible', 'results':'infeasible',  'gantt':'infeasible',
              'prop_gantt':'infeasible', 'dist_completed':'infeasible', 'param':p,
              'gap':'infeasible'}
 
    try:
    
        # Create a new model
        m = gp.Model("Continuous")
    
        dvX = [(j,m,k) for j in p['F'] for m in p['M'] for k in p['K']]
        dvY = [(j,m,k,s) for j in p['NF'] for m in p['M'] for k in p['K'] for s in p['S']]
        
        x = m.addVars(dvX, vtype=GRB.BINARY, name='x')
        y = m.addVars(dvY, vtype=GRB.BINARY, name='y')

        E = [(j,s) for j in p['J'] for s in p['S']]
        D = [(j,s) for j in p['J'] for s in p['S']]
        G = [(j,s) for j in p['J'] for s in p['S']]
        t = [(m,k,s) for m in p['M'] for k in p['K'] for s in p['S']]
        
        
        E = m.addVars(E, vtype=GRB.CONTINUOUS, name='E')
        D = m.addVars(D, vtype=GRB.CONTINUOUS, name='D')
        G = m.addVars(G, vtype=GRB.CONTINUOUS, name='G')
        t = m.addVars(t, vtype=GRB.CONTINUOUS, name='t')

        Z = 100000
   
        jobs = p['jobs']
        
        m.setObjective(gp.quicksum([jobs[j-1].h_j * E[j,s] + 
                                    jobs[j-1].c_j * D[j,s] + 
                                    jobs[j-1].p_j * G[j,s] for j in p['J'] for s in p['S']]),
                       sense=GRB.MINIMIZE)
    
        m.addConstrs((gp.quicksum([x[(j,m,k)] for m in p['M'] for k in p['K']]) == 1
                      for j in p['F']), name='assignmentX')

        m.addConstrs((gp.quicksum([y[(j,m,k,s)] for m in p['M'] for k in p['K']]) == 1
                      for j in p['NF'] for s in p['S']
                      if p['b_js'][j][s] == 1), name='assignmentY')
        
        m.addConstrs((gp.quicksum([x[(j,m,k)] for j in p['F']]) +
                      gp.quicksum([y[(j,m,k,s)] for j in p['NF']]) <= 1
                      for m in p['M'] for k in p['K'] for s in p['S']),
                      name='resource')

        m.addConstrs((t[(m,k,s)] == t[(m,k-1,s)] + 
                      gp.quicksum([p['w_jm'][(j,m)] * x[(j,m,k)] for j in p['F']]) + 
                      gp.quicksum([p['w_jm'][(j,m)] * y[(j,m,k,s)] for j in p['NF']]) 
                      for m in p['M'] for s in p['S'] for k in p['K'] if k > 2),
                     name = 'calcTime')

        m.addConstrs((t[(m,1,s)] == gp.quicksum([p['w_jm'][(j,m)] * x[(j,m,1)] for j in p['F']]) + 
                      gp.quicksum([p['w_jm'][(j,m)] * y[(j,m,1,s)] for j in p['NF'] if j]) 
                      for m in p['M'] for s in p['S']),
                     name = 'calcTime0')

        
        m.addConstrs((D[j,s] >= t[(m,k,s)] - jobs[j-1].d_j - Z * (1 - x[(j,m,k)])
                      for j in p['F'] for m in p['M'] for s in p['S'] for k in p['K']),
                     name = 'calcDelayX')
        
        m.addConstrs((D[j,s] >= t[(m,k,s)] - jobs[j-1].d_j - Z * (1 - y[(j,m,k,s)])
                      for j in p['NF'] for m in p['M'] for k in p['K'] for s in p['S']),
                     name = 'calcDelayY')

        m.addConstrs((E[j,s] >= jobs[j-1].e_j - t[(m,k,s)] - Z * (1 - x[(j,m,k)])
                      for j in p['F'] for m in p['M'] for s in p['S'] for k in p['K']),
                     name = 'calcEarlyX')

        m.addConstrs((E[j,s] >= jobs[j-1].e_j - t[(m,k,s)] - Z * (1 -y[(j,m,k,s)])
                      for j in p['NF'] for m in p['M'] for k in p['K'] for s in p['S']),
                     name = 'calcEarlyY')

        m.addConstrs((G[j,s] >= t[(m,k,s)] - jobs[j-1].g_j - Z * (1 - x[(j,m,k)])
                      for j in p['F'] for m in p['M'] for s in p['S'] for k in p['K']),
                     name = 'calcDelayX')
        
        m.addConstrs((G[j,s] >= t[(m,k,s)] - jobs[j-1].g_j - Z * (1 - y[(j,m,k,s)])
                      for j in p['NF'] for m in p['M'] for k in p['K'] for s in p['S']),
                     name = 'calcDelayY')

        m.addConstrs((t[(m,0,s)] == 0 for m in p['M'] for s in p['S']),
                     name = 'startTime')
                
        m.addConstrs((gp.quicksum([x[(j,m,k-1)] for j in p['F']]) +
                      gp.quicksum([y[(j,m,k-1,s)] for j in p['NF']])
                      <= 
                      gp.quicksum([x[(j,m,k)] for j in p['F']]) + 
                      gp.quicksum([y[(j,m,k,s)] for j in p['NF']])
                      for m in p['M'] for s in p['S'] for k in p['K'] if k >= 1),
                     name='utilize')
        
        # Optimize model
        m.Params.mipgap = gap
        m.Params.timelimit = max_time
        m.optimize()
        
        runtime = m.runtime
        status = m.Status
        objective = m.objVal
        mipGap = m.MIPGap

        xVar = [v.varName for v in m.getVars() if v.x  > 0 and 'x' in v.varName]
        yVar = [v.varName for v in m.getVars() if v.x  > 0 and 'y' in v.varName]
        Evar = {v.varName: v.x for v in m.getVars() if 'E' in v.varName}
        Dvar = {v.varName: v.x for v in m.getVars() if 'D' in v.varName}
        Gvar = {v.varName: v.x for v in m.getVars() if 'G' in v.varName}
        tvar = {v.varName: v.x for v in m.getVars() if 't' in v.varName}
        tvar = {tuple(k[2:-1].split(',')):v for k,v in tvar.items()}
        output = {'runtime':runtime, 'status':status, 'obj':objective,
                  't':tvar, 'gap':mipGap, 'x':xVar, 'y':yVar, 
                  'E':Evar, 'D':Dvar, 'G':Gvar,}


    except gp.GurobiError as e:
        print('Error code ' + str(e.errno) + ': ' + str(e))
    
    except AttributeError:
        print('Encountered an attribute error')
        
    return output