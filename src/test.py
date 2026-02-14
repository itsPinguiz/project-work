import argparse
import os
import sys
import time
from datetime import datetime
import numpy as np
from tqdm import tqdm

# Add parent directory to path to import Problem and solution
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from Problem import Problem
    from s346595 import solution
except ImportError as e:
    print(f"Error: Could not import required modules. Make sure 'Problem.py' and 's346595.py' are in the parent directory.\nDetails: {e}")
    sys.exit(1)

# --- Configuration ---
TEST_RANGES = {
    'city': (10, 500),
    'alpha': (0.5, 5.0),
    'beta': (0.5, 5.0),
    'density': (0.3, 0.9)
}

def calculate_solution_cost(problem, path):
    """
    Calculate the total cost of a solution path strictly using the Problem definition.
    """
    if not path:
        return 0.0

    graph = problem.graph  # Cache property access
    total_cost = 0.0
    carried_gold = 0.0

    for i in range(len(path) - 1):
        u, pickup = path[i]
        v, _ = path[i + 1]

        # 1. Update load
        carried_gold += pickup

        if u == v:
            continue

        # 2. Validate Edge
        if not graph.has_edge(u, v):
             raise ValueError(f"Invalid segment: {u} -> {v} does not exist.")

        # 3. Calculate Cost
        # problem.cost handles the formula: dist + (alpha * dist * weight)^beta
        segment_cost = problem.cost([u, v], carried_gold)
        total_cost += segment_cost

        # 4. Drop gold if returned to base
        if v == 0:
            carried_gold = 0.0

    return total_cost

def generate_test_cases(num_cases=10):
    """Generate reproducible random test parameters."""
    np.random.seed(42)
    cases = []
    
    for i in range(num_cases):
        cases.append({
            'num_cities': np.random.randint(*TEST_RANGES['city']),
            'alpha': np.random.uniform(*TEST_RANGES['alpha']),
            'beta': np.random.uniform(*TEST_RANGES['beta']),
            'density': np.random.uniform(*TEST_RANGES['density']),
            'seed': i
        })
    return cases

def run_single_test(test_id, params, skip_baseline=False):
    """Execute a single test case and return metrics."""
    # 1. Setup
    problem = Problem(
        num_cities=params['num_cities'],
        alpha=params['alpha'],
        beta=params['beta'],
        density=params['density'],
        seed=params['seed']
    )

    # 2. Baseline (Optional)
    baseline_cost = None
    if not skip_baseline:
        try:
            baseline_cost = problem.baseline()
        except Exception:
            return None  # Baseline failure

    # 3. Solution Execution
    start_time = time.time()
    try:
        solution_path = solution(problem)
        duration = time.time() - start_time
        solution_cost = calculate_solution_cost(problem, solution_path)
    except Exception:
        return None  # Solution failure

    # 4. Metrics
    improvement = None
    status = "N/A"

    if baseline_cost is not None:
        if baseline_cost > 0:
            improvement = ((baseline_cost - solution_cost) / baseline_cost) * 100
        else:
            improvement = 0.0

        if solution_cost < baseline_cost - 1e-9:
            status = "Better"
        elif solution_cost > baseline_cost + 1e-9:
            status = "Worse"
        else:
            status = "Equal"

    return {
        'id': test_id,
        'params': params,
        'base_cost': baseline_cost,
        'sol_cost': solution_cost,
        'imp': improvement,
        'time': duration,
        'status': status
    }

def main():
    parser = argparse.ArgumentParser(description='Gold Routing Performance Test')
    parser.add_argument('--skip-baseline', action='store_true', help='Skip slow baseline calculation')
    parser.add_argument('--num-tests', type=int, default=50, help='Number of iterations')
    args = parser.parse_args()

    # Setup Output
    logs_dir = os.path.join(current_dir, 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Generate unique filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = os.path.join(logs_dir, f'results_{timestamp}.log')

    # Generate Data
    test_cases = generate_test_cases(args.num_tests)

    # Initialize Log File
    with open(output_path, 'w') as f:
        f.write("="*80 + "\n")
        f.write("VRP OPTIMIZATION TEST RESULTS\n")
        f.write("="*80 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Mode: {'Solution Only' if args.skip_baseline else 'Full Comparison with Baseline'}\n")
        f.write("Status: Running...\n")
        f.write("="*80 + "\n\n")

    # Run Loop
    valid_results = []
    
    # Use position=0 for the main bar
    with tqdm(total=len(test_cases), desc="Benchmarking", unit="test", position=0) as pbar:
        for i, params in enumerate(test_cases, 1):
            pbar.set_postfix(N=params['num_cities'], Alpha=f"{params['alpha']:.1f}, Beta={params['beta']:.1f}, Density={params['density']:.1f}")
            
            result = run_single_test(i, params, args.skip_baseline)
            
            if result:
                valid_results.append(result)
                
                # Append row to file immediately
                p = params
                with open(output_path, 'a') as f:
                    if args.skip_baseline:
                        f.write(f"Test #{result['id']:3d} | "
                               f"N={p['num_cities']:3d} | "
                               f"α={p['alpha']:5.2f} | "
                               f"β={p['beta']:5.2f} | "
                               f"density={p['density']:4.2f} | "
                               f"cost={result['sol_cost']:12.2e} | "
                               f"time={result['time']:7.4f}s\n")
                    else:
                        f.write(f"Test #{result['id']:3d} | "
                               f"N={p['num_cities']:3d} | "
                               f"α={p['alpha']:5.2f} | "
                               f"β={p['beta']:5.2f} | "
                               f"density={p['density']:4.2f} | "
                               f"baseline={result['base_cost']:12.2e} | "
                               f"solution={result['sol_cost']:12.2e} | "
                               f"improvement={result['imp']:6.2f}% | "
                               f"time={result['time']:7.4f}s | "
                               f"{result['status']}\n")
            
            pbar.update(1)

    # Final Summary Update
    if valid_results:
        avg_time = np.mean([r['time'] for r in valid_results])
        
        summary_lines = ["\nSUMMARY", "-"*80]
        summary_lines.append(f"Total Tests: {len(valid_results)}")
        summary_lines.append(f"Average Execution Time: {avg_time:.4f}s")
        
        if not args.skip_baseline:
            avg_imp = np.mean([r['imp'] for r in valid_results if r['imp'] is not None])
            summary_lines.append(f"Average Improvement: {avg_imp:.2f}%")
        
        summary_lines.append("-"*80)
        summary_text = "\n".join(summary_lines) + "\n"

        # Safe replace of the status line
        with open(output_path, 'r') as f:
            content = f.read()
        
        content = content.replace("Status: Running...\n", summary_text)
        
        with open(output_path, 'w') as f:
            f.write(content)
            
    print(f"\nDone! Results saved to: {output_path}")

if __name__ == "__main__":
    main()