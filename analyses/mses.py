import aerosandbox as asb
import aerosandbox.numpy as np

airfoil = asb.Airfoil("rae2822")
Re = 6.5e6
alpha = 1

machs = np.concatenate([
    # np.arange(0.1, 0.5, 0.05),
    # np.arange(0.5, 0.6, 0.01),
    # np.arange(0.6, 0.8, 0.003),
    np.arange(0.74, 0.8, 0.003),
])

# machs = [0.1, 0.2, 0.3]

##### MSES
ms = asb.MSES(
    airfoil=airfoil,
    behavior_after_unconverged_run="terminate",
    mset_n=280,
    mset_io=40,
    verbosity=1,
    mses_mcrit=0.90,
)
mses = ms.run(
    alpha=alpha,
    Re=Re,
    mach=machs,
)

import json
s = [json.dumps({k: v[i] for k, v in mses.items()}) + "\n" for i in range(len(mses['mach']))]

with open("mach_sweep_data/mses.csv", "a") as f:
    f.writelines(s)