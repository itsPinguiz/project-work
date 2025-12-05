# Gold Mining Optimization Project 
**Computational Intelligence Course | Giovanni Squillero**

## 1. Problem Overview
The objective is to design an algorithm to collect gold from $N$ cities scattered across a grid and transport it back to a home base (City 0) while minimizing the total movement cost. 

This is a variation of the Vehicle Routing Problem (VRP) with specific cost constraints related to payload weight.

## 2. Technical Specifications

### The Environment
* **Grid:** $N$ cities located on a 2D grid with coordinates in range $[0, 1]$.
* **City 0 (Base):** Located at coordinates `(0.5, 0.5)`. This is the starting point and the depot.
* **Gold:** All cities (except City 0) contain a randomized amount of gold (represented by node size in visualizations).
* **Connectivity:** The graph is **not** fully connected. Edge existence depends on a `density` parameter, though the graph is guaranteed to be connected (a path always exists between any two nodes).

### The Cost Function
Movement cost is non-linear and depends on the distance traveled and the weight of the gold currently being carried.

$$\text{Cost} = d + (d \cdot \alpha \cdot w)^\beta$$

Where:
* $d$: Geometric (Euclidean) distance between the two cities.
* $w$: Current weight of gold being carried.
* $\alpha$ (alpha): A positive coefficient parameter.
* $\beta$ (beta): A positive exponent parameter (influences penalty for heavy loads).

### Key Rules & Mechanics
1.  **Start/End:** You start at City 0.
2.  **Depositing:** Gold can be deposited at City 0. Once deposited, your carried weight ($w$) resets to 0.
3.  **Partial Collection:** You are **allowed** to collect only a fraction of the gold from a specific city, traverse to other nodes, and return later for the rest. You do not need to empty a node in one visit.
4.  **Goal:** Collect **all** gold from all nodes and deposit it at City 0 at the minimum possible cost.

## 3. The Provided Code (`Problem` Class)
A Python class is provided to simulate the environment.

**Initialization Parameters:**
```python
problem = Problem(
    num_cities=100,  # Total nodes (including City 0)
    density=0.5,     # Probability of edge existence
    alpha=1.0,       # Cost multiplier
    beta=1.0,        # Cost exponent
    seed=42          # RNG seed for reproducibility
)
