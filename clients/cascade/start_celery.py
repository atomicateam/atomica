import sys
import sciris as sc

orig_args = sc.dcp(sys.argv)
import atomica_apps.apptasks_cascade as atc

new_args = [orig_args[0], '-l', 'info']

sys.argv = new_args

if __name__ == "__main__":
    atc.celery_instance.worker_main(new_args)