"""
Version:
"""

import atomica.ui as au
P = au.demo(which='tb')
results = P.run_sim()
P.plot(results)