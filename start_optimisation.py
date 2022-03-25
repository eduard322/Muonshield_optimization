#!/usr/bin/env python3
import time
import argparse
import json
import copy
import pickle
import os
import shutil
import numpy as np
from comet_ml import Experiment
from Magn_vis import Shielddrawer
from matplotlib import colors
import matplotlib.patches as patches
import matplotlib.gridspec as gridspec
import matplotlib
import matplotlib.pyplot as plt
from sklearn.ensemble import GradientBoostingRegressor
from skopt import Optimizer
from skopt.learning import GaussianProcessRegressor, RandomForestRegressor, GradientBoostingQuantileRegressor

from commons import FCN, CreateSpace, StripFixedParams, AddFixedParams, ParseParams

from opt_config import (RUN, POINTS_IN_BATCH, RANDOM_STARTS, MIN, METADATA_TEMPLATE)
from run_kub import run_batch

SLEEP_TIME = 60
DEFAULT_POINT = [70,170,200,200,200,200,200,200,40,40,150,150,2,2,80,80,150,150,2,2,67.1,49.7,27.5,37.1,35.6,7.1,54.9,18,78.1,175.3,23.2,9.4,32.9,24.2,28,40.4,40.8,2.6,3.9,26.4,77,38.4,0.7,8.8,13.3,41.1,219.5,67.6,6.7,0.5,15.4,68.1,92.3,233.6,5.8,36.9]


def fig(Y, name):
    fig, ax = plt.subplots(figsize=(14, 12), dpi=100)
    plt.grid()
    ax.plot(Y, color = 'blue')
    ax.set_xlabel("Points", fontsize=14)
    ax.set_ylabel(name, fontsize=14)
    ax.set_yscale("log")
    plt.legend()
    return fig

def magn(X):
    Data = X
    fig = plt.figure(figsize=(15,10))
#plt.grid()
    drawer = Shielddrawer(np.array(Data))
    gs1 = gridspec.GridSpec(1, 1)
    gs1.update(wspace=0.025, hspace=0.25)
    drawer.plot_frame(0, fig, gs1)
    return fig
    

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(NpEncoder, self).default(obj)


def StripFixedParams_multipoint(points):
    return [StripFixedParams(p) for p in points]

def ExtractParams(metadata):
    params = json.loads(metadata)['user']['params']
    return ParseParams(params)

def get_result(jobs):
    results = []
    weights = []
    #print(jobs)
    for i in range(len(jobs['jobs'])):
        with open(os.path.join(jobs['path'], str(i), 'optimise_input.json')) as result_file:
          result = json.load(result_file)
          rWeights = [k[7] for k in result['kinematics']]
          weights = weights + rWeights
          results.append(result)
          #print('result is: ', jobs['path'])
    # Only one job per machine calculates the weight and the length
    # -> take first we find
    weight = float(results[0]['w'])
    if weight < 3e6:
        muons_w = sum(np.array(weights, dtype=float))
    else:
        muons_w =  0
    return weight, 0, muons_w


def ProcessPoint(jobs):
    print("process Point: ", jobs)
    try:
        weight, _, muons_w = get_result(jobs)
        #LOGS[1] += [muons_w]
        #LOGS[2] += [weight]
        #print(X_new[0], "!!!!!!!!!!!!!!   " + str(sum(X_new[0][2:8])) + "   !!!!!!!!!!!!!!!!!!!!!!!")       
        #experiment.log_figure("Magnet weight dynamics", fig(LOGS[2], "Total weight of magnets"), overwrite=True)
        #experiment.log_figure("Flux dynamics", fig(LOGS[1], "Total weighted flux"), overwrite=True)
        #print('obtained weights: ', weight, length, muons_w)
        X = ExtractParams(jobs['metadata'])
        y = FCN(weight, muons_w, 0, X[2:8])
        print('Magnets length: ', sum(X[2:8]))
        #print("!!!!!!!", X, "!!!!!!")
        

        #LOGS[0] += [y]
        #LOGS[3] += [2*sum(X[2:8])]
        #experiment.log_figure("Optimization dynamic", fig(LOGS[0], "Loss function"), overwrite=True)
        #experiment.log_figure("Magnet length dynamics", fig(LOGS[3], "Length of the muon shield, cm"), overwrite=True)
        #experiment.log_metric("loss", y, step = tag)
        



        # print('X: ', X)
        # print(X, y)
        return X, (y, weight, muons_w)
    except Exception as e:
        print(e)


def ProcessJobs(jobs, tag, space):
    print('[{}] Processing jobs...'.format(time.time()))
    results = [ProcessPoint(point) for point in jobs]
    print(f'Got results {results}')
    results = [result for result in results if result]
    results = [result for result in results if space.__contains__(StripFixedParams(result[0]))]

    return zip(*results) if results else ([], [])


def CreateMetaData(point, tag):
    metadata = copy.deepcopy(METADATA_TEMPLATE)
    metadata['user'].update([
        ('tag', tag),
        ('params', str(point)),
    ])
    return json.dumps(metadata)

def SubmitKubJobs(point, tag):
    return run_batch(CreateMetaData(point, tag))

def WaitCompleteness(mpoints):
    uncompleted_jobs = mpoints
    work_time = 0
    restart_counts = 0
    while True:
        time.sleep(SLEEP_TIME)
        print(uncompleted_jobs)
        uncompleted_jobs = [any([job.is_alive() for job in jobs['jobs']]) for jobs in mpoints]

        if not any(uncompleted_jobs):
            return mpoints

        print('[{}] Waiting...'.format(time.time()))
        work_time += 60

        if work_time > 60 * 30 * 1:
            restart_counts+=1
            if restart_counts>=3:
                print("Too many restarts")
                raise SystemExit(1)
            print("Job failed!")
            #raise SystemExit(1)
            for jobs in mpoints:
                if any([job.is_alive() for job in jobs['jobs']]):
                    jobs = run_batch(jobs['metadata'])
            #for job in [[for job in jobs['jobs']] for jobs in mpoints]]:
            #    job = run_batch(job['metadata'])
            work_time = 0

def CalculatePoints(points, tag, cache, space, LOGS, experiment):
    tags = {json.dumps(points[i], cls=NpEncoder):str(tag)+'-'+str(i) for i in range(len(points))}
    shield_jobs = [
        SubmitKubJobs(point, tags[json.dumps(point, cls=NpEncoder)])
        for point in points if json.dumps(point, cls=NpEncoder) not in cache
    ]
    print("submitted: \n", points)

    if shield_jobs:
        shield_jobs = WaitCompleteness(shield_jobs)
        #print(ProcessJobs(shield_jobs, tag, space))
        X_new, output_y = ProcessJobs(shield_jobs, tag, space)
        print("!!!!!!!!!!!!!!!", output_y, "!!!!!!!!!!!!!!")
        output_y = np.array(output_y)
        print("!!!!!!!!!!!!!!!", output_y, output_y.shape, "!!!!!!!!!!!!!!", output_y[:,0], "!!!!!!!!!!!!", output_y[:,1])
        print(LOGS)
        LOGS["weight"] += output_y[:,1].tolist()
        LOGS["flux"] += output_y[:,2].tolist()
        #print(X_new[0], "!!!!!!!!!!!!!!   " + str(sum(X_new[0][2:8])) + "   !!!!!!!!!!!!!!!!!!!!!!!")       
        experiment.log_figure("Magnet weight dynamics", fig(LOGS["weight"], "Total weight of magnets"), overwrite=True)
        experiment.log_figure("Flux dynamics", fig(LOGS["flux"], "Total weighted flux"), overwrite=True)
        #print('obtained weights: ', weight, length, muons_w)
        #print('Magnets length: ', sum(X_new[0][2:8]))
        #print("!!!!!!!", X, "!!!!!!")
        

        LOGS["y"] += output_y[:,0].tolist()
        LOGS["mag_len"] += [2*sum(X_new[0][2:8])]
        experiment.log_figure("Optimization dynamic", fig(LOGS["y"], "Loss function"), overwrite=True)
        experiment.log_figure("Magnet length dynamics", fig(LOGS["mag_len"], "Length of the muon shield, cm"), overwrite=True)
 
        experiment.log_figure("Magnets", magn(X_new[0]), overwrite=True)
        #experiment.log_metric("length", sum(X_new[:6]), step = tag)
    return X_new, output_y[:,0].tolist()

def load_points_from_dir(db_name='db.pkl'):
    with open (db_name, 'rb') as f:
        return pickle.load(f)

def CreateOptimizer(clf_type, space, random_state=None):
    if clf_type == 'rf':
        clf = Optimizer(
            space,
            RandomForestRegressor(n_estimators=500, max_depth=7, n_jobs=-1),
            random_state=random_state)
    elif clf_type == 'gb':
        clf = Optimizer(
            space,
            GradientBoostingQuantileRegressor(
                base_estimator=GradientBoostingRegressor(
                    n_estimators=100, max_depth=4, loss='quantile')),
            random_state=random_state)
    elif clf_type == 'gp':
        clf = Optimizer(
            space,
            GaussianProcessRegressor(
                alpha=1e-7, normalize_y=True, noise='gaussian'),
            random_state=random_state)
    else:
        clf = Optimizer(
            space, base_estimator='dummy', random_state=random_state)

    return clf

def main():
    parser = argparse.ArgumentParser(description='Start optimizer.')
    parser.add_argument('--opt', help='Write an optimizer.', default='rf')
    parser.add_argument('--db', help='Data base file', default='db.pkl')
    parser.add_argument('--state', help='Random state of Optimizer', default=None)
    parser.add_argument('--olddb', help='use existing db', default=False)
    parser.add_argument('--tag', help='to save resutls', default=False)

    args = parser.parse_args()
 
    tag = 0#args.tag

    space = CreateSpace()
    clf = CreateOptimizer(args.opt, space, random_state=int(args.state) if args.state else None)
    experiment = Experiment(
    api_key="dDolDoCEM7Pf3sXP1G7pporUI",
    project_name="bo-project",
    workspace="eursov",)
    experiment.log_figure("Magnets", magn(DEFAULT_POINT), overwrite=True)
    experiment.log_figure("Magnet length dynamics", fig(sum(DEFAULT_POINT[2:6]), "Length of the muon shield, cm"), overwrite=True)        
    print("!!!!!!!!!!!!!!   " + str(sum(DEFAULT_POINT[2:8])) + "   !!!!!!!!!!!!!!!!!!!!!!!")
    if args.olddb:
        cache = load_points_from_dir(args.db)
    else:
        cache = {}

    tag = len(cache.keys())
#Load calculated points from DB
    if len(cache.keys())>0:
        print('Received previous points ', len(cache.keys()))
        try:
            for key in cache.keys():
                loc_x = json.loads(key)
                loc_y = cache[key]
                if space.__contains__(StripFixedParams(loc_x)):
                    print(loc_x, loc_y)
                    clf.tell(StripFixedParams(loc_x), loc_y)
        except ValueError:
            print('None of the previous points are contained in the space.')
    Y_data = []
    FLUX = []
    WEIGHT = []
    MAGNET_LENGTH = [] 
    LOGS = {"y": [], "flux": [], "weight": [], "mag_len": []}

#calculate the first point if DB is empty:
    if len(cache.keys())==0:
        X_1, y_1 = CalculatePoints([DEFAULT_POINT], tag, cache, space, LOGS, experiment)
        print("default start point scorring: \n", X_1, y_1)
        cache[json.dumps(X_1[0], cls=NpEncoder)] = y_1
        clf.tell(StripFixedParams(X_1[0]), y_1[0])
        with open(args.db, 'wb') as db:
                 pickle.dump(cache, db, pickle.HIGHEST_PROTOCOL)

    while not (cache and len(cache.keys()) > RANDOM_STARTS):
        tag = tag + 1
        points = [AddFixedParams(p) for p in space.rvs(n_samples=POINTS_IN_BATCH)]
        # points = [transform_forward(p) for p in points]
        # print(points)
        X_new, y_new = CalculatePoints(points, tag, cache, space, LOGS, experiment)
        print('Received new points ', X_new, y_new)
        #Y_data += y_new
        #experiment.log_figure("Optimization dynamic", fig(Y_data), overwrite=True)
        if X_new and y_new:
            for x, loss in zip(X_new, y_new):
                cache[json.dumps(x,cls=NpEncoder)] = loss
            # X_new = [transform_backward(point) for point in X_new]
            shutil.copy2(args.db, 'old_db.pkl')
            with open(args.db, 'wb') as db:
                 pickle.dump(cache, db, pickle.HIGHEST_PROTOCOL) 
            clf.tell([p for p in StripFixedParams_multipoint(X_new)], y_new)

    
    while True:
        tag = tag+1
        points = [AddFixedParams(p) for p in clf.ask(n_points=POINTS_IN_BATCH, strategy='cl_mean')]
        X_new, y_new = CalculatePoints(
            points, tag, cache, space, LOGS, experiment)

        print('Received new points ', X_new, y_new)
        if X_new and y_new:
                        for x, loss in zip(X_new, y_new):
                            cache[json.dumps(x,cls=NpEncoder)] = loss
                        shutil.copy2(args.db, 'old_db.pkl')
                        with open(args.db, 'wb') as db:
                            pickle.dump(cache, db, pickle.HIGHEST_PROTOCOL)

        # X_new = [transform_backward(point) for point in X_new]
        #Y_data += y_new
        #experiment.log_figure("Optimization dynamic", fig(Y_data), overwrite=True)
        result = clf.tell(StripFixedParams_multipoint(X_new), y_new)

        with open(f'/mnt/eursov/optimiser_{args.tag}.pkl', 'wb') as f:
            pickle.dump(clf, f)

        with open(f'/mnt/eursov/result_{args.tag}.pkl', 'wb') as f:
            pickle.dump(result, f)


if __name__ == '__main__':
    matplotlib.use('Agg')
    #global FLUX, WEIGHT, MAGNET_LENGTH

    main()
