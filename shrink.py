import os
import math
import numpy as np
import h5py
import glob
from tqdm import tqdm
import scipy

import matplotlib.pyplot as plt
from keras.utils.np_utils import to_categorical
dfiles = glob.glob('data/*.h5')

all_imgs = []
all_speedx = []
all_targets = []

# convert gas to categorical: forward, brake, reverse
def make_cat(gas_val):
    # drive forward
    if gas_val > 0.6:
        cat = 0
    # brake
    elif gas_val <= 0.6 and gas_val > 0.4:
        cat = 1
    # reverse
    else:
        cat = 2
    return cat

# determine scaling parameters
# speed and accel
speedmax = None
speedmin = None
accelmax = None
accelmin = None
for dfile in dfiles:
    with h5py.File(dfile,'r') as h5f:
        # raw data
        A = dict(h5f.items()) 
        smx = np.max(A['vehicle_states'].value[:,2])
        smn = np.min(A['vehicle_states'].value[:,2])
        amx = np.max(A['vehicle_states'].value[:,3])
        amn = np.min(A['vehicle_states'].value[:,3])
        if speedmax is None or smx > speedmax:
            speedmax = smx
        if speedmin is None or smn < speedmin:
            speedmin = smn
        if accelmax is None or amx > accelmax:
            accelmax = amx
        if accelmin is None or amn < accelmin:
            accelmin = amn

# steering is nominally -1 to 1, but doesn't go below zero?
throttlemax = None
throttlemin = None
steermax = None
steermin = None
for dfile in dfiles:
    with h5py.File(dfile,'r') as h5f:
        # raw data
        A = dict(h5f.items()) 
        smx = np.max(A['targets'].value[:,4])
        smn = np.min(A['targets'].value[:,4])
        tmx = np.max(A['targets'].value[:,5])
        tmn = np.min(A['targets'].value[:,5])
        if steermax is None or smx > steermax:
            steermax = smx
        if steermin is None or smn < steermin:
            steermin = smn
        if throttlemax is None or tmx > throttlemax:
            throttlemax = tmx
        if throttlemin is None or tmn < throttlemin:
            throttlemin = tmn


# activate the shrink ray!
for dfile in tqdm(dfiles):
    with h5py.File(dfile,'r') as h5f:
        # raw data
        A = dict(h5f.items()) 
        # extract images in 1-byte format
        B = np.array(A['images'].value,dtype=np.float16)/255.
        # change BGR to RGB
        B = B[:,::-1,:,:]
        # Scale down image size
        imgs = np.zeros((len(B),3,64,64),dtype=np.float16)
        for i,b in enumerate(B):
            imgs[i] = scipy.misc.imresize(b,(64,64),'cubic','RGB').transpose((2,0,1))
        # speed and accel scale
        speedx = A['vehicle_states'].value[:,2:4]
        speedx[:,0] = (speedx[:,0] - speedmin) / (speedmax-speedmin)
        speedx[:,1] = (speedx[:,1] - accelmin) / (accelmax-accelmin)
        # throttle and steering scale
        steer = A['targets'].value[:,4]
        gas_cat = list(map(make_cat, (A['targets'].value[:,5] + 1) / 2.))
        targets = np.zeros((len(steer),2), dtype=np.float16)
        targets[:,0] = (steer[:] + 1) / 2.
        targets[:,1] = gas_cat[:]
        all_imgs.extend(np.array(imgs,dtype=np.uint8))
        all_speedx.extend(np.array(speedx,dtype=np.float32))
        all_targets.extend(np.array(targets,dtype=np.float16))

imgs_arr = np.array(all_imgs)
speedx_arr = np.array(all_speedx)
targets_arr = np.array(all_targets)

np.savez('data/imgs_arr.npz',imgs_arr)
np.savez('data/speedx_arr.npz',speedx_arr)
np.savez('data/targets_arr.npz',targets_arr)