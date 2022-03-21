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

if __name__ == '__main__':

    machs = np.arange(0.1, 1.3, 0.5)

    with mp.Pool(mp.cpu_count() // 2) as pool:
        # raw_outputs = [
        #     # SU2_aero(
        #     #     airfoil=airfoil,
        #     #     Re=6.5e6,
        #     #     mach=mach,
        #     #     alpha=1.0
        #     # )
        #     {'x2': mach ** 2, 'x3': mach ** 3}
        #     for mach in machs
        # ]

        for mach, output in pool.imap(
                lambda mach: (mach, SU2_aero(
                    airfoil=airfoil,
                    Re=6.5e6,
                    mach=mach,
                    alpha=1.0,
                    verbose=False,
                )),
                # lambda mach: (mach, f(mach)),
                iterable=machs
        ):
            output = {
                "mach": mach,
                **output
            }
            print(output)
            with open("mach_sweep.csv", "a+") as f:
                f.write(json.dumps(output) + "\n")

    # df = pd.DataFrame(
    #     data=raw_outputs, index=machs
    # )
    # df.index.name = "Machs"
    #
    # df.to_csv('mach_sweep.csv')
    #
    # print(df)

    # outputs = {
    #     'machs': machs,
    #     'outputs': raw_outputs
    # }
    # with open('mach_sweep.json', 'w+') as f:
    #     json.dump(outputs, f)
