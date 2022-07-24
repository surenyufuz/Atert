# Atert

######
Atert (**A** **T**est-**E**xtension Based GUI **R**egression **T**esting Method).

## Requirement

######
* Android SDK
* Appium 1.6.4
* Android devices or emulators
* Python 3.7.6
* Package listed in requirements.txt

## Connect devices
######
1. Connect devices via the adb tool.
2. Execute adb command in the terminal, e.g.,`adb connect`.
3. Start the appium service by default.

## GUI Test Repair
1. Prepare the source GUI test script.
2. Assure the appium parameters in the script is suitable for your device, e.g., `platformVersion`.
3. Set the 'script_path' and 'save_path' in the script file `repair/main.py`.
4. Install the base version of the app in the device.
5. Run the script `main.py` and record the source script, then we could get the following results in the 'save_path', 
which records the screens and  elements the source test script interacted with:
* **scenario_screens**
* **scenario_model**  
6. Install the updated version of the app in the device, and input the number 1 to the python terminal.
7. Then the repairing process is starting, and finally we could get the following results:
* **target_script**: which records the GUI test actions after repairing.
* **result_screens**: which records the screens and  elements the target test script interacted with.
* **search_screens**: which records the screens that the repairing process visited.

## Verify
Run the target script generated directly with appium to verify its  usability.

## Future Work
We could make it a command-line tool for ease of use.

  
