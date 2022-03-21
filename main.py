from pathlib import Path
import os, sys
import json
import aerosandbox as asb
import aerosandbox.numpy as np
from aerosandbox.library.aerodynamics.viscous import Cf_flat_plate
import subprocess
import tempfile

this_dir = Path(__file__).parent

pyaero_path = Path(this_dir / "PyAero")


def SU2_aero(
        airfoil=asb.Airfoil("rae2822"),
        Re=6.5e6,
        mach=0.76,
        alpha=1.0,
        working_directory=None,
        verbose=True,
):
    with tempfile.TemporaryDirectory() as directory:

        ##### Paths
        if working_directory is not None:
            directory = working_directory

        directory = Path(directory)

        ##### Write Airfoil .dat
        airfoil.write_dat(
            filepath=directory / "airfoil.dat",
            include_name=False
        )

        ##### Make a mesh
        with open(pyaero_path / "data" / "Batch" / "batch_control.json") as f:
            pyaero_json = json.load(f)

        ### Determine mesh sizing
        Cf = Cf_flat_plate(Re_L=Re)
        V = mach * 343
        rho = 1.225
        q = 0.5 * rho * V ** 2
        tau_w = q * Cf
        u_tau = (tau_w / rho) ** 0.5
        target_yplus = 3
        nu = 1.51e-5
        y_1 = target_yplus * nu / u_tau
        y_1 = np.maximum(y_1, 4e-6)

        d_99 = 10 * 5.0 * Re ** -0.5
        growth_rate = 1.15
        n_inflation_layers = np.log(1 - d_99 * (1 - growth_rate) / y_1) / np.log(growth_rate)

        pyaero_json['Airfoils'].update({
            'path'          : str(directory),
            'names'         : ['airfoil.dat'],
            'trailing_edges': ["yes" if airfoil.TE_thickness() >= 1e-5 else "no"]
        })
        pyaero_json['Output formats'].update({
            'path'   : str(directory),
            'formats': ['SU2', 'VTK']
        })
        pyaero_json['Airfoil contour refinement'].update({
            # 'Refinement tolerance': 175,
            # 'Number of points on spline': 400
        })
        pyaero_json['Airfoil contour mesh'].update({
            'Divisions normal to airfoil': int(np.round(n_inflation_layers)),
            '1st cell layer thickness'   : y_1,
            'Cell growth rate'           : 1.15
        })
        pyaero_json['Airfoil trailing edge mesh'].update({
            'Divisions at trailing edge': int(np.round(np.minimum(airfoil.TE_thickness() / y_1, 15))),
            'Divisions downstream'      : 15,
            '1st cell layer thickness'  : 0.002,
            'Cell growth rate'          : 1.05
        })
        pyaero_json['Windtunnel mesh airfoil'].update({
            'Windtunnel height'   : 15,
            'Cell thickness ratio': 100,
        })
        pyaero_json['Windtunnel mesh wake'].update({
            'Divisions in the wake'         : 200,
            'Windtunnel wake'               : 15,
            'Cell thickness ratio'          : 200,
            'Equalize vertical wake line at': 80,
        })

        with open(directory / "batch_control.json", "w+") as f:
            json.dump(pyaero_json, f, indent=4)

        sys.path.append(str(pyaero_path / "src"))
        import BatchMode, PyAero

        if 'app' not in locals():
            app = PyAero.QtCore.QCoreApplication(['-no-gui'])

        batchmode = BatchMode.Batch(
            app=app,
            batch_controlfile=directory / "batch_control.json",
            __version__=PyAero.__version__
        )
        batchmode.run_batch()

        ##### Write CFD Config File
        with open(this_dir / "su2_config_template.cfg") as f:
            su2_config = f.readlines()

        tags = {
            "MACH_NUMBER"    : mach,
            "AOA"            : alpha,
            "REYNOLDS_NUMBER": Re,
            "OUTPUT_WRT_FREQ": 1000,
        }

        for k, v in tags.items():
            for i, line in enumerate(su2_config):
                if k in line:
                    break
                elif i == len(su2_config):
                    raise ValueError

            su2_config[i] = f"{k}= {v}\n"

        with open(directory / "su2_config.cfg", "w+") as f:
            f.writelines(su2_config)

        ##### Run CFD

        process = subprocess.run(
            "SU2_CFD su2_config.cfg",
            cwd=directory,
            shell=True,
            text=True,
            stdout=subprocess.DEVNULL if not verbose else None
        )
        # output = []
        # while True:
        #     next_line = process.stdout.readline()
        #     if next_line:
        #         output.append(str(next_line))
        #         print(next_line.replace("\n", ""))
        #     if process.poll() != None:
        #         break

        ##### Read CFD Output
        with open(directory / "forces_breakdown.dat") as f:
            forces_breakdown = f.readlines()

        output = {}
        for line in forces_breakdown[104:110]:
            line = line.split("|")[0]
            k, v = line.split(":")
            k = k.replace("Total", "").strip()
            v = float(v)
            output[k] = v

        return output


if __name__ == '__main__':
    output = SU2_aero(
        airfoil=asb.Airfoil("rae2822"),
        Re=6.5e6,
        alpha=1,
        mach=0.64,
        # working_directory=Path(os.path.abspath(".")) / "working_directory"
    )
