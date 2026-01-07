import random
import networkx as nx
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import shortest_path

# ------------------------------------------------------------------------------
# 1. HELPER: SPLIT PROCEDURE
# ------------------------------------------------------------------------------
def split_procedure(permutation, problem_data):
    """
    Decodes a TSP permutation into a VRP solution using O(1) Matrix lookups.
    """
    dist_matrix = problem_data['dist_matrix']
    golds = problem_data['golds']
    alpha = problem_data['alpha']
    beta = problem_data['beta']
    
    n = len(permutation)
    V = [float('inf')] * (n + 1)
    P = [-1] * (n + 1)
    V[0] = 0
    
    # Lookahead limit
    MAX_TRIP_LENGTH = 32

    for i in range(n):
        if V[i] == float('inf'): continue
            
        current_gold = 0
        trip_cost = 0
        u = 0 # Start at Depot
        
        for j in range(i, min(n, i + MAX_TRIP_LENGTH)):
            v = permutation[j]
            
            # 1. TRAVEL u -> v
            d_uv = dist_matrix[u][v]
            step_cost = d_uv + (d_uv * current_gold * alpha) ** beta
            trip_cost += step_cost
            
            # 2. PICK UP GOLD
            current_gold += golds[v]
            
            # 3. RETURN COST v -> 0
            d_v0 = dist_matrix[v][0]
            return_cost = d_v0 + (d_v0 * current_gold * alpha) ** beta
            
            total_segment_cost = trip_cost + return_cost
            
            if V[i] + total_segment_cost < V[j+1]:
                V[j+1] = V[i] + total_segment_cost
                P[j+1] = i
            
            u = v

    # Reconstruct Virtual Path
    virtual_path = []
    curr = n
    while curr > 0:
        prev = P[curr]
        virtual_path.append(permutation[prev:curr])
        curr = prev
    virtual_path.reverse()
    
    return virtual_path, V[n]

# ------------------------------------------------------------------------------
# 2. HELPER: GENETIC OPERATORS
# ------------------------------------------------------------------------------
def inver_over_crossover(p1, p2):
    current = p1[:]
    if len(current) < 2: return current
    c = random.choice(current)
    
    for _ in range(15): 
        idx_c = current.index(c)
        next_idx = (idx_c + 1) % len(current)
        c_next = current[next_idx]
        
        if random.random() < 0.05:
            c_prime = random.choice(current)
        else:
            try:
                idx_p2 = p2.index(c)
                c_prime = p2[(idx_p2 + 1) % len(p2)]
            except ValueError:
                c_prime = random.choice(current)
            
        if c_prime == c_next:
            break
            
        idx_c_prime = current.index(c_prime)
        s, e = min(idx_c+1, idx_c_prime), max(idx_c+1, idx_c_prime)
        current[s:e+1] = current[s:e+1][::-1]
        c = c_prime
        
    return current

def greedy_initialization(dist_matrix, cities):
    unvisited = set(cities)
    current = 0 
    path = []
    
    while unvisited:
        best_city = -1
        min_dist = float('inf')
        
        candidates = unvisited
        if len(unvisited) > 100:
             candidates = random.sample(list(unvisited), 50)
        
        for city in candidates:
            d = dist_matrix[current][city]
            if d < min_dist:
                min_dist = d
                best_city = city
        
        if best_city == -1: best_city = list(unvisited)[0]

        path.append(best_city)
        unvisited.remove(best_city)
        current = best_city
        
    return path

# ------------------------------------------------------------------------------
# 3. MAIN ALGORITHM FUNCTION
# ------------------------------------------------------------------------------
def my_genetic_algorithm(problem_instance):
    """
    The main optimization pipeline.
    """
    # 1. SciPy Pre-computation
    graph_sparse = nx.to_scipy_sparse_array(problem_instance.graph, weight='dist')
    dist_matrix = shortest_path(graph_sparse, method='auto', directed=False, unweighted=False)
    golds = np.array([problem_instance.graph.nodes[i]['gold'] for i in range(problem_instance.n)])
    
    problem_data = {
        'dist_matrix': dist_matrix,
        'golds': golds,
        'alpha': problem_instance.alpha,
        'beta': problem_instance.beta
    }
    
    # 2. GA Loop
    POP_SIZE = 30
    GENERATIONS = 100 
    cities = list(range(1, problem_instance.n))
    population = []
    
    # Seeding
    greedy_geno = greedy_initialization(dist_matrix, cities)
    v_path, fit = split_procedure(greedy_geno, problem_data)
    population.append({'g': greedy_geno, 'f': fit, 'vp': v_path})
    
    for _ in range(POP_SIZE - 1):
        geno = cities[:]
        random.shuffle(geno)
        v_path, fit = split_procedure(geno, problem_data)
        population.append({'g': geno, 'f': fit, 'vp': v_path})
        
    population.sort(key=lambda x: x['f'])
    
    for gen in range(GENERATIONS):
        p1 = min(random.sample(population, 4), key=lambda x: x['f'])
        p2 = min(random.sample(population, 4), key=lambda x: x['f'])
        
        child_geno = inver_over_crossover(p1['g'], p2['g'])
        
        if random.random() < 0.15:
            i, j = random.sample(range(len(child_geno)), 2)
            child_geno[i], child_geno[j] = child_geno[j], child_geno[i]
            
        v_path, fit = split_procedure(child_geno, problem_data)
        
        if fit < population[-1]['f']:
            population[-1] = {'g': child_geno, 'f': fit, 'vp': v_path}
            population.sort(key=lambda x: x['f'])

    # 3. Path Reconstruction (Lazy)
    best_virtual_segments = population[0]['vp']
    final_physical_path = [0]
    current_node = 0
    
    for segment in best_virtual_segments:
        trip_targets = segment + [0]
        for target in trip_targets:
            if target == current_node: continue
            
            path_leg = nx.shortest_path(problem_instance.graph, source=current_node, target=target, weight='dist')
            final_physical_path.extend(path_leg[1:])
            current_node = target
            
    return final_physical_path