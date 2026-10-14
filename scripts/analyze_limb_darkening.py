"""Reproducible synthetic FSPL sensitivity, smearing and quadrature diagnostics."""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
import numpy as np
from romanmlr.limb_darkening import (
    linear_source_magnification, exposure_averaged_magnification, quadrature_convergence
)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,default=Path('results/limb_darkening_pilot'))
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    rho=0.04
    u=np.array([0.0,0.01,0.02,0.04,0.08,0.2])
    with (args.out/'source_sensitivity.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['u','rho','linear_coefficient','magnification'])
        for c in (0.0,0.3,0.6):
            a=linear_source_magnification(u,rho,c,n_radial=64,n_angular=256)
            for ui,ai in zip(u,a):w.writerow([ui,rho,c,ai])
    times=np.linspace(-0.04,0.04,33)
    with (args.out/'exposure_smearing.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['time_days','exposure_seconds','magnification'])
        for seconds in (0,25,1800):
            a=exposure_averaged_magnification(times,t0=0,t_e=0.25,u0=0.025,
                rho=rho,coefficient=0.5,exposure_days=seconds/86400,n_time=7)
            for t,ai in zip(times,a):w.writerow([t,seconds,ai])
    conv=quadrature_convergence(np.array([0.0,0.02,0.08]),rho,0.5,orders=(24,48,96))
    result={'model':'synthetic single point lens, linear limb darkening',
            'rho':rho,'coefficients':[0.0,0.3,0.6],
            'quadrature_orders':conv['orders'].tolist(),
            'quadrature_u':[0.0,0.02,0.08],
            'relative_change_between_orders':conv['relative_change'].tolist(),
            'warning':'Quadrature differences are not rigorous error bounds; u≈rho requires extra care.'}
    (args.out/'convergence.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'out':str(args.out),'max_last_relative_change':float(conv['relative_change'][-1].max())}))

if __name__=='__main__':main()
