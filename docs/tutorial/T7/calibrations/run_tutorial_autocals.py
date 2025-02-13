# This file produces calibrations of each YAML file shown in T7: YAML autocalibration tutorial.
# Output files will be saved locally in the outputs folder.
# Desirable results must be manually moved to the calibrations folder so that they can be plotted by the
# YAML_tutorial_plots_final.ipynb notebook. This is to avoid crowding the final results folder (calibrations) when
# re-running the calibrations or trying out new versions of the model.

import sys
in_path = '../inputs'
sys.path.append(in_path)
import atomica as at
import atomica.yaml_calibration
import os
from os.path import isfile
import time
import shutil
import winsound

yaml_dir = os.getcwd()
fnames = [f for f in os.listdir(yaml_dir) if isfile(f"{yaml_dir}/{f}")]
yaml_files = [f for f in fnames if ".yaml" in f and "T7_YAML" in f]
yaml_files += 'WE_8'

testing = False  #<------------
savecals = True
out_path = 'outputs'

#make project   ------------------------------------------------
inputs = '../assets'
F = at.ProjectFramework(f'{inputs}/T7_framework.xlsx')
D = at.ProjectData.from_spreadsheet(f'{inputs}/T7_databook.xlsx', framework=F)

P = at.Project(framework=F, databook=D, do_run=False)
P.settings.update_time_vector(start=2000, end=2050, dt=1 / 52)
cal = P.make_parset()
# starting calibration (if needed)
# cal.load_calibration(out_path + "/PAK_typh_YAML_autocalibrations_2024-04-25_1941_reinitialising/PAK_typh_YAML-autocalibration_2024-04-25_1959.xlsx")
# print('Existing calibration loaded')

for yaml_fname in yaml_files:
    yaml_path = f'{yaml_dir}/{yaml_fname}'

    # new folder to put calibrations in
    date = time.strftime("%Y-%m-%d_%H%M")
    calspath = f'{out_path}/cals_{yaml_fname[8]}'
    if savecals:
        #save everything in folder
        try:
            os.makedirs(calspath)
        except FileExistsError:
            calspath += f'_{date}'
            os.makedirs(f'{calspath}')

        # save yaml file for reference
        new_fname = f'{yaml_fname}_{date}.yaml'
        shutil.copy(yaml_path, calspath)
        shutil.move(f'{calspath}/{yaml_fname}', f'{calspath}/{new_fname}') #renaming file

        #save logfile
        at.start_logging(f'{calspath}/logfile_{date}.txt')

        # save current runfile for reference
        runfile_name = f'{os.path.basename(__file__)}_{date}'
        shutil.copy(__file__, f'{calspath}/{runfile_name}')

    # display tree
    cal_tree = at.yaml_calibration.build(yaml_path)
    print(cal_tree)

    #run calibration w yaml instructions # <--------------------------
    newcal = P.calibrate(parset = cal, yaml=yaml_path, quiet=False, savedir=calspath, save_intermediate=False, verbose=0)

    #save final calibration
    newcal.save_calibration(f'{calspath}/cal_{yaml_fname[8]}')  #newcal.save_calibration(f'{calspath}/cal_{yaml_fname}')
    at.stop_logging()


#Notification - calibration finished
winsound.Beep(frequency = 2500, duration = 200)
winsound.Beep(frequency = 2750, duration = 200)
winsound.Beep(frequency = 3050, duration = 200)
