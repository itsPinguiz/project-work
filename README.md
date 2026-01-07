## The Project Work Challenge

### Problem Specification
The final project involves a variation of the **Vehicle Routing Problem (VRP)** with dynamic costs.

* **Environment:** $N$ cities arranged on a grid.
* **Home Base:** City 0, located at the center (coordinates 0, 0).
* **Resource:** Each city contains a specific amount of **Gold** (float value, e.g., $1 + \text{random} \times 999$).
* **Goal:** Collect all gold from all cities and bring it back to base.
* **Partial Collection:** You are **not required** to collect all the gold in a city during a single visit. You may collect a portion of the gold, leave, and return later for the remainder, provided that eventually 100% of the gold is collected.
* **Graph:** Cities are not fully connected (variable edge density).

#### Cost Dynamics
The cost of travel increases with the weight (gold) you are carrying, not just distance.

$$ \text{Cost}(i, j) = d(i, j) + {(d(i, j) \cdot \text{CurrentGold} \cdot \alpha)}^{\beta} $$

* $\alpha, \beta$: Constants defining the weight penalty.
* **Strategic Implication:** The optimal strategy might involve **multiple trips** back to base to unload, or picking up only small amounts from specific cities to keep travel costs low.

---

### Implementation Requirements
Your submission must follow a strict structure for automated testing:

* **Repository Name:** `project-work`
* **Main File:** `s<studentID>.py` (e.g., `s123456.py`) containing a `solution` function.
* **Source Folder:** `src/` for all auxiliary code.
* **Entry Point:** The test script will dynamically import: `from s123456 import solution`.
* **Output:** The function must return a list of tuples representing the path and item choices.

**Project Structure Example:**

```python
# Folder: project-work/
#   |- src/
#       |- algorithm.py
#       |- utils.py
#   |- s123456.py

# Content of s123456.py
from src.algorithm import my_genetic_algorithm

def solution(problem_instance):
    # Setup problem
    # Run optimization
    path = my_genetic_algorithm(problem_instance)
    return path
```

---

### Submission Guidelines
* **Deadline:** 168 hours (7 days) before the exam date.
* **No Reports:** Do not upload PDFs or logs to the repository.

# Algorithm Description: Evolutionary Route-First, Cluster-Second

To solve the Vehicle Routing Problem (VRP) with dynamic costs, we implemented a state-of-the-art strategy known as **"Route-First, Cluster-Second."** This approach decouples the complex problem into two manageable sub-problems:
1.  **Ordering (Hard):** Determining the optimal sequence of city visits.
2.  **Segmentation (Easy):** Determining the optimal points to return to the depot within that sequence.

---

## 1. Core Logic: The "Split" Procedure
The heart of the solution is the `split_procedure`, a deterministic algorithm that acts as the phenotype decoder.

* **Input:** A TSP-like permutation of all cities (e.g., `[5, 2, 8, 1, ...]`).
* **Process:** The algorithm treats this sequence as a giant tour and builds a Directed Acyclic Graph (DAG) of potential trips.
    * It evaluates every possible sub-segment (e.g., `Depot -> 5 -> 2 -> Depot`).
    * It calculates the cost of these segments using the specific problem formula: $Cost = d + (d \cdot \text{Gold} \cdot \alpha)^\beta$.
    * It uses a **Shortest Path algorithm** (dynamic programming) to find the optimal set of trips that covers the entire sequence with minimal cost.
* **Output:** The exact set of trips (routes) and the total fitness cost.

This reduces the search space significantly: instead of searching for complex VRP schedules, the Evolutionary Algorithm only needs to search for a good permutation of cities ($N!$), which is a well-studied problem (TSP).

## 2. Evolutionary Components
We utilize a Genetic Algorithm (GA) to evolve the city permutations.

* **Genotype:** A simple list of integers representing the city IDs (excluding the depot).
* **Crossover Operator:** We use **Inver-Over Crossover**. Unlike standard crossovers (OX, PMX), Inver-Over focuses on preserving **adjacency information** (edges). If City A is geographically close to City B, the operator attempts to keep them connected in the offspring. This is critical for spatial routing problems.
* **Initialization (Seeding):** To accelerate convergence, the initial population is seeded with **one Greedy Individual**. This individual is generated using a Nearest Neighbor heuristic. This ensures the algorithm starts with a "good" baseline and evolves towards "perfect," rather than starting from randomness.

## 3. Technical Optimizations
To handle the large-scale instances ($N=1000$) under the strict time limit (1 minute), two critical optimizations were applied:

### A. The "Virtual Graph" (SciPy Pre-computation)
The provided problem involves a sparse graph, meaning direct edges between cities often do not exist. Standard pathfinding (Dijkstra) inside the GA loop would be prohibitively slow ($O(E \log V)$ per fitness check).

* **Optimization:** We use `scipy.sparse.csgraph` to pre-calculate the All-Pairs Shortest Path matrix at the start.
* **Benefit:** This transforms the distance calculation from a slow graph traversal into an **$O(1)$ matrix lookup**. This speeds up the fitness evaluation by approximately **100x**, allowing for more generations and larger population sizes.

### B. Lazy Path Reconstruction
During the evolutionary process, we only track the *cost* and the *logical sequence* of cities. We do not reconstruct the actual physical path (the specific streets/nodes visited).

* **Optimization:** The detailed physical path (e.g., `Node 0 -> Node 5 -> Node 12 -> Node 0`) is reconstructed **only once** for the single best individual after the algorithm terminates.
* **Benefit:** This drastically reduces memory overhead and processing time during the evolution loop.