MINOA macOS double-click launchers
==================================

Double-click the files in this exact order:

1. 01_setup.command
   Creates .venv, installs all Python packages from requirements.txt, activates
   the environment, and checks Python, packages, Java, validator, and raw data.

2. 02_run_sml.command
   Runs the final method for Small, Medium, and Large.

3. 03_run_all.command
   Runs the final method for all 12 Senior instances.

4. 04_print_final_table.command
   Prints the retained final thesis result table.

5. 05_validate_all_outputs.command
   Re-checks all generated all-instance outputs using the pipeline manifest.

6. 06_run_lower_bounds.command
   Computes lower-bound diagnostics. Run step 3 first.

7. 07_generate_lower_bound_figures.command
   Creates lower-bound figures. Run step 6 first.

8. 08_run_tests.command
   Runs the Python test suite.

If a file is opened too early, it prints the required previous step.
