MINOA double-click runner
=========================

Use the files in this order. Choose the folder for your operating system:

- macOS files are in launchers/macos/
- Windows files are in launchers/windows/

macOS:
1. Double-click launchers/macos/01_setup.command
2. Double-click launchers/macos/02_run_sml.command for Small, Medium, and Large
3. Double-click launchers/macos/03_run_all.command for all 12 Senior instances
4. Double-click launchers/macos/04_print_final_table.command to print the retained thesis table
5. Double-click launchers/macos/05_validate_all_outputs.command to re-check all generated all-instance outputs
6. Double-click launchers/macos/06_run_lower_bounds.command to compute lower-bound diagnostics
7. Double-click launchers/macos/07_generate_lower_bound_figures.command to create lower-bound figures
8. Double-click launchers/macos/08_run_tests.command to run the Python tests

Windows:
1. Double-click launchers/windows/01_setup.bat
2. Double-click launchers/windows/02_run_sml.bat for Small, Medium, and Large
3. Double-click launchers/windows/03_run_all.bat for all 12 Senior instances
4. Double-click launchers/windows/04_print_final_table.bat to print the retained thesis table
5. Double-click launchers/windows/05_validate_all_outputs.bat to re-check all generated all-instance outputs
6. Double-click launchers/windows/06_run_lower_bounds.bat to compute lower-bound diagnostics
7. Double-click launchers/windows/07_generate_lower_bound_figures.bat to create lower-bound figures
8. Double-click launchers/windows/08_run_tests.bat to run the Python tests

Notes:
- Run setup first. The other files check for .venv and will tell you to run setup if it is missing.
- Each launcher uses the virtual environment's Python interpreter directly, so
  activation does not need to persist between separate launcher windows.
- Java is required for the MINOA desktop validator.
- The Small/Medium/Large run is the faster demonstration run.
- The all-instance run can take longer because it solves all Senior benchmark files.
- Lower-bound figures require step 6 first.
- Generated outputs are written under outputs/minoa/ and data/processed/minoa/.
