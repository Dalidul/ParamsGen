BLACKLISTED_SOLVERS = ('march_rw', 'SatELite_release')

import os.path

def remove_blacklisted_solvers_names(solvers_names):
    for solver_name in solvers_names:
        if solver_name in BLACKLISTED_SOLVERS:
            solvers_names.remove(solver_name)
    return solvers_names


def remove_blacklisted_solvers_paths(solvers_paths):
    for solver_path in solvers_paths:
        if os.path.basename(solver_path) in BLACKLISTED_SOLVERS:
            solvers_paths.remove(solver_path)
    return solvers_paths