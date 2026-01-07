from src.algorithm import my_genetic_algorithm

def solution(problem_instance):
    """
    Entry point for the assignment.
    Calls the optimization logic defined in src/algorithm.py
    """
    # Run optimization
    path = my_genetic_algorithm(problem_instance)
    return path

# Optional: Keep the test execution here if you want to run this file directly
if __name__ == "__main__":
    from src.utils import run_tests
    run_tests(solution)