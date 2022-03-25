import json
import hashlib
import numpy as np
from skopt.space.space import Integer, Space, Real
from opt_config import FIXED_PARAMS, FIXED_RANGES


def FCN(W, Sxi2, _, Params):
    W_star = 1915820.*25/30.

    return (1 + np.exp(10. * (W - W_star) / W_star)) * (1. + 2*Sxi2) if W <= 3e6 and sum(Params) < 1250. else 1e13

def StripFixedParams(point):
    #removes absober data from the point

    stripped_point = []
    pos = 0
    for low, high in FIXED_RANGES:
        stripped_point += point[:low-pos]
        point = point[high-pos:]
        pos = high
    _, high = FIXED_RANGES[-1]
    stripped_point += point[high-pos:]
    return stripped_point

def CreateSpace(nMagnets=8):
    dZgap = 10
    zGap = dZgap / 2  # halflengh of gap
    old_dimensions = nMagnets * [
        Integer(170 + zGap, 300 + zGap)  # magnet lengths
        ] + nMagnets * (
            2 * [
                Integer(10, 100)  # dXIn, dXOut
            ] + 2 * [
                Integer(20, 200)  # dYIn, dYOut
            ] + 2 * [
                Integer(2, 70)  # gapIn, gapOut
            ])
    dimensions = nMagnets * [
        Real(170 + zGap, 310 + zGap)  # magnet lengths
        ] + nMagnets * (
            2 * [
                Real(3, 100)  # dXIn, dXOut
            ] + 2 * [
                Real(20, 234)  # dYIn, dYOut
            ] + 2 * [
                Real(0.5, 70)  # gapIn, gapOut
            ])

    return Space(StripFixedParams(dimensions))
    #return dimensions
def ParseParams(params_string):
    return [float(x) for x in params_string.strip('[]').split(',')]


def AddFixedParams(point):
    _fixed_params = FIXED_PARAMS
    for low, high in FIXED_RANGES:
        point = point[0:low] + _fixed_params[:high-low] + point[low:]
        _fixed_params = _fixed_params[high-low:]
    return point

def create_id(params):
    params_json = json.dumps(params)
    h = hashlib.md5()
    h.update(params_json)
    return h.hexdigest()


if __name__ == '__main__':
    print(CreateSpace)
