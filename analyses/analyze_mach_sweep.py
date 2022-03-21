import pandas as pd
import aerosandbox as asb
import aerosandbox.numpy as np
import json

with open("mach_sweep.csv") as f:
    raw_data = f.readlines()

dicts = [
    json.loads(line)
    for line in raw_data
]