import sys
import sciris as sc
import atomica_apps.apptasks_tb as at

sys.argv = [__file__, '-l', 'info']

if __name__ == "__main__":
    at.celery_instance.worker_main(sys.argv)