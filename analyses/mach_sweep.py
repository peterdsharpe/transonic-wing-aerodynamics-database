import os, sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import aerosandbox as asb
import aerosandbox.numpy as np
from main import SU2_aero
from tqdm import tqdm
import pathos.multiprocessing as mp
import pandas as pd
import time
import json

airfoil = asb.Airfoil("rae2822")

# def SU2_aero(airfoil, Re, mach, alpha, verbose):
#     time.sleep(2 * np.random.rand())
#     return {'x2': mach ** 2, 'x3': mach ** 3}

def run(mach):
    print(f"Running mach = {mach}")
    output = SU2_aero(
        airfoil=airfoil,
        Re=6.5e6,
        mach=mach,
        alpha=1.0,
        verbose=False,
    )
    output = {
        "mach": mach,
        **output
    }
    print(output)
    return output

if __name__ == '__main__':

    machs = np.arange(0.1, 1.3, 0.02)

    with mp.Pool(np.minimum(mp.cpu_count() // 2 - 1, len(machs))) as pool:

        for output in pool.imap(
                lambda mach: run(mach=mach),
                iterable=machs
        ):
            with open("mach_sweep.csv", "a+") as f:
                f.write(json.dumps(output) + "\n")
