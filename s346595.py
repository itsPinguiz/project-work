import networkx as nx
from tqdm import tqdm
from Problem import Problem

class GoldLogisticsSolver:
    def __init__(self, problem: Problem):
        self.graph = problem.graph
        self.alpha = problem.alpha
        self.beta = problem.beta
        
        # Initialize graph state
        self.gold_map = nx.get_node_attributes(self.graph, 'gold')
        self.nodes = list(self.graph.nodes())
        self.base_node = 0
        self.num_nodes = len(self.nodes)
        
        # Active Set: Tracks nodes with remaining gold for O(1) lookup
        self.active_nodes = {n for n, g in self.gold_map.items() if n != 0 and g > 0}
        
        # Pre-computation and Tuning
        self._cache_navigation_data()
        self.scan_radius = max(10, min(100, int(self.num_nodes * 0.15)))
        self._configure_parameters()

    def _cache_navigation_data(self):
        """Pre-compute distances and neighbor lists for fast lookups."""
        self.dist_matrix = {}
        self.proximity_map = {} 
        
        for node in self.nodes:
            dists = nx.single_source_dijkstra_path_length(self.graph, node, weight='dist')
            self.dist_matrix[node] = dists
            
            # Cache the closest 500 neighbors for efficient scanning
            sorted_neighbors = sorted(dists.keys(), key=lambda x: dists[x])
            self.proximity_map[node] = sorted_neighbors[1:501]

        self.base_dists = self.dist_matrix[self.base_node]

    def _configure_parameters(self):
        """Adjust load limits and penalties based on the Beta environment."""
        available = [val for k, val in self.gold_map.items() if k != self.base_node]
        peak = max(available) if available else 0
        
        if self.beta >= 1.5:
            self.load_limit = max(200.0, peak * 1.2)
            self.penalty_factor = 0.02
        elif self.beta >= 1.2:
            self.load_limit = max(300.0, peak * 1.5)
            self.penalty_factor = 0.015
        else:
            self.load_limit = max(500.0, peak * 2.0)
            self.penalty_factor = 0.01

    def _estimate_trip_cost(self, distance, load):
        if load <= 0: return distance
        return distance + (self.alpha * distance * load) ** self.beta

    def _compute_pickup_cap(self, dist_to_base):
        if self.beta <= 1.0: return float('inf')
        denom = (self.beta - 1) * self.alpha * self.beta * (dist_to_base ** (self.beta - 1))
        if denom <= 0: return float('inf')
        return max(1.0, (2.0 / denom) ** (1.0 / self.beta))

    def _identify_targets(self, current_pos):
        if not self.active_nodes:
            return []

        candidates = []
        valid_count = 0
        
        # 1. Fast Scan using pre-computed proximity map
        for node in self.proximity_map[current_pos]:
            if node in self.active_nodes:
                candidates.append(node)
                valid_count += 1
                if valid_count >= self.scan_radius:
                    break
        
        if not candidates:
            return list(self.active_nodes)[:self.scan_radius]

        # 2. Refined Selection (Mix of Efficiency and Greed)
        final_set = set()
        
        # Strategy A: Efficiency (Closest nodes)
        limit_idx = max(1, int(len(candidates) * 0.4))
        final_set.update(candidates[:limit_idx])
        
        # Strategy B: Greed (Richest nodes nearby)
        richest = sorted(candidates, key=lambda n: self.gold_map[n], reverse=True)
        rich_limit = max(1, int(len(candidates) * 0.3))
        final_set.update(richest[:rich_limit])
        
        # Strategy C: Safety (Base Gravity)
        curr_dists = self.dist_matrix[current_pos]
        for node in candidates[:10]:
            if curr_dists[node] <= 0.8 * self.base_dists[node]:
                final_set.add(node)
                
        return sorted(list(final_set), key=lambda x: curr_dists[x])

    def solve(self):
        full_path = [(0, 0)]
        current_node = 0
        current_load = 0.0
        
        # Initialize progress bar
        with tqdm(total=len(self.active_nodes), desc="Collecting Gold", unit="node", leave=False) as pbar:
            while self.active_nodes:
                
                # Safety Check: Force return if stranded outside with no active trip
                if current_node != 0:
                    route = nx.shortest_path(self.graph, current_node, 0, weight='dist')
                    for step in route[1:]:
                        full_path.append((step, 0))
                    current_node = 0
                    current_load = 0.0

                trip_active = True
                loop_safety = 0 
                
                while trip_active:
                    candidates = self._identify_targets(current_node)
                    
                    if not candidates:
                        trip_active = False
                        break

                    best_choice = None
                    best_metric = float('inf')
                    best_gain = 0
                    
                    for target in candidates:
                        available = self.gold_map[target]
                        dist_to_home = self.base_dists[target]
                        dist_from_curr = self.dist_matrix[current_node][target]
                        dist_curr_to_home = self.base_dists[current_node]

                        math_cap = self._compute_pickup_cap(dist_to_home)
                        pickup_amount = min(available, math_cap)
                        
                        if current_load + pickup_amount > self.load_limit:
                            pickup_amount = max(0, self.load_limit - current_load)
                            if pickup_amount < 1.0: continue

                        # Compare Return-First (A) vs Chain-Trip (B)
                        cost_a = (self._estimate_trip_cost(dist_curr_to_home, current_load) + 
                                  self._estimate_trip_cost(dist_to_home, 0) + 
                                  self._estimate_trip_cost(dist_to_home, pickup_amount))

                        cost_b = (self._estimate_trip_cost(dist_from_curr, current_load) + 
                                  self._estimate_trip_cost(dist_to_home, current_load + pickup_amount))

                        score = (cost_b - cost_a) + (self.penalty_factor * available * dist_to_home)

                        if score < best_metric:
                            best_metric = score
                            best_choice = target
                            best_gain = pickup_amount

                    if best_choice and best_metric < 0:
                        # Execute Move
                        route = nx.shortest_path(self.graph, current_node, best_choice, weight='dist')
                        for step in route[1:-1]:
                            full_path.append((step, 0))
                        
                        full_path.append((best_choice, int(best_gain)))
                        current_node = best_choice
                        current_load += best_gain
                        self.gold_map[best_choice] -= best_gain
                        
                        if self.gold_map[best_choice] <= 0:
                            if best_choice in self.active_nodes:
                                self.active_nodes.discard(best_choice)
                                pbar.update(1)
                        
                        loop_safety = 0
                    
                    elif current_node == 0 and candidates:
                        # Forced Move: Kickstart from base
                        nearest = candidates[0]
                        cap = self._compute_pickup_cap(self.base_dists[nearest])
                        amt = min(self.gold_map[nearest], cap)
                        
                        route = nx.shortest_path(self.graph, 0, nearest, weight='dist')
                        for step in route[1:-1]:
                            full_path.append((step, 0))
                        
                        full_path.append((nearest, amt))
                        current_node = nearest
                        current_load += amt
                        self.gold_map[nearest] -= amt
                        
                        if self.gold_map[nearest] <= 0:
                            if nearest in self.active_nodes:
                                self.active_nodes.discard(nearest)
                                pbar.update(1)
                    else:
                        trip_active = False
                    
                    loop_safety += 1
                    if loop_safety > 20:
                        trip_active = False

        # Final Return
        if current_node != 0:
            route = nx.shortest_path(self.graph, current_node, 0, weight='dist')
            for step in route[1:]:
                full_path.append((step, 0))
        
        # Ensure path validity
        if not full_path or full_path[-1] != (0, 0):
            full_path.append((0, 0))
        if full_path[0] != (0, 0):
            full_path.insert(0, (0, 0))
        
        return full_path

def solution(p: Problem):
    solver = GoldLogisticsSolver(p)
    return solver.solve()