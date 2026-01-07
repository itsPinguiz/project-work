import time
from .problem import Problem

# Professor's Baseline Results
# Format: (N, Density, Alpha, Beta): Cost
BASELINES = {
    # N=100 Baselines
    (100, 0.2, 1, 1): 25266.41,
    (100, 0.2, 2, 1): 50425.31,
    (100, 0.2, 1, 2): 5334401.93,
    (100, 1, 1, 1): 18266.19,
    (100, 1, 2, 1): 36457.92,
    (100, 1, 1, 2): 5404978.09,
    
    # N=1000 Baselines
    (1000, 0.2, 1, 1): 195402.96,
    (1000, 0.2, 2, 1): 390028.72,
    (1000, 0.2, 1, 2): 37545927.70,
    (1000, 1, 1, 1): 192936.23,
    (1000, 1, 2, 1): 385105.64,
    (1000, 1, 1, 2): 57580018.87
}

def run_tests(solution_func):
    """
    Runs the solution function against the standard test cases 
    and compares with baselines.
    """
    test_cases = [
        # N=100
        (100, 0.2, 1, 1), (100, 0.2, 2, 1), (100, 0.2, 1, 2),
        (100, 1, 1, 1),   (100, 1, 2, 1),   (100, 1, 1, 2),
        
        # N=1000
        (1000, 0.2, 1, 1), (1000, 0.2, 2, 1), (1000, 0.2, 1, 2),
        (1000, 1, 1, 1),   (1000, 1, 2, 1),   (1000, 1, 1, 2)
    ]
    
    print(f"{'N':<6} | {'Dens':<5} | {'Alpha':<5} | {'Beta':<5} | {'Cost':<15} | {'vs Base %':<10} | {'Time':<8} | {'Status'}")
    print("-" * 100)
    
    total_diff = 0
    count = 0
    
    for n, dens, alpha, beta in test_cases:
        # Create a specific problem instance
        # Note: We use a fixed seed (42) here for reproducibility during testing
        p = Problem(n, density=dens, alpha=alpha, beta=beta, seed=42)
        
        start = time.time()
        try:
            path = solution_func(p)
            elapsed = time.time() - start
            
            # Validate and calculate cost
            cost, status = p.evaluate_path(path)
            
            # Compare with baseline
            baseline = BASELINES.get((n, dens, alpha, beta), None)
            if baseline and cost != float('inf'):
                diff_pct = ((cost - baseline) / baseline) * 100
                diff_str = f"{diff_pct:+.2f}%"
                total_diff += diff_pct
                count += 1
            else:
                diff_str = "N/A"
                
            print(f"{n:<6} | {dens:<5} | {alpha:<5} | {beta:<5} | {cost:<15.2f} | {diff_str:<10} | {elapsed:<8.2f} | {status}")
            
        except Exception as e:
            print(f"{n:<6} | {dens:<5} | {alpha:<5} | {beta:<5} | {'ERROR':<15} | {'N/A':<10} | {0.0:<8} | {e}")
            import traceback
            traceback.print_exc()

    if count > 0:
        print("-" * 100)
        print(f"Average Improvement vs Baseline: {total_diff/count:+.2f}% (Negative is better)")