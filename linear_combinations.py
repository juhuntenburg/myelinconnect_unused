import numpy as np
from vtk_rw import read_vtk
from sklearn import linear_model
import scipy.stats as stats
import pickle
import pandas as pd
import pdb

mesh_file = '/scr/ilz3/myelinconnect/new_groupavg/surfs/lowres/%s_lowres_new.vtk'
mask_file="/scr/ilz3/myelinconnect/new_groupavg/masks/fullmask_lh_rh_new.npy"
embed_dict_file="/scr/ilz3/myelinconnect/new_groupavg/embed/both_smooth_3_embed_dict.pkl"
t1_file = '/scr/ilz3/myelinconnect/new_groupavg/t1/smooth_1.5/%s_t1_avg_smooth_1.5.npy'
model_file = '/scr/ilz3/myelinconnect/new_groupavg/model/linear_combination/t1avg/smooth_1.5/both_t1avg_by_fc_maps_%s.pkl'


all_maps = [[0], [0,4,5], 
            [0,5], 
            [0,4,5,6], 
            [0,4,5,6,9], 
            [0,1,4,5,6,9],
            [0,1,4,5,6,8,9], 
            [0,1,4,5,6,8,9,15], 
            [0,1,4,5,6,8,9,15,17],
            [0,1,4,5,6,8,9,14,15,17], 
            [0,1,4,5,6,7,8,9,14,15,17],
            [0,1,4,5,6,7,8,9,10,14,15,17],
            [0,1,4,5,6,7,8,9,10,12,14,15,17], 
            [0,1,4,5,6,7,8,9,10,12,13,14,15,17],
            [0,1,4,5,6,7,8,9,10,11,12,13,14,15,17],
            [0,1,4,5,6,7,8,9,10,11,12,13,14,15,17,19],
            [0,1,2,4,5,6,7,8,9,10,11,12,13,14,15,17,19],
            [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,17,19],
            [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,19],
            [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19],
             ]
all_maps_str = ['0', 'best', 
                '2p', '4p', '5p', '6p', '7p', '8p', '9p', '10p', '11p', '12p',
                '13p', '14p', '15p', '16p', '17p', '18p', '19p', '20p']

#v,f,d = read_vtk(mesh_file%hemi)
t1_left = np.load(t1_file%('lh'))
t1_right = np.load(t1_file%('rh'))
t1 = np.concatenate((t1_left, t1_right))

mask = np.load(mask_file)
# extend mask to nodes that have a t1avg < 1500
bigmask = np.unique(np.concatenate((mask,np.where(t1<=1500)[0])))
bigmask = np.asarray(bigmask, dtype='int64')
#bigmask = np.copy(mask)
# define "nonmask" for both
idcs=np.arange(0,t1.shape[0])
nonmask=np.delete(idcs, mask)
nonmask_bigmask=np.delete(idcs, bigmask)

# prepare embedding (normalized from entry in dict)
pkl_in = open(embed_dict_file, 'r')
embed_dict=pickle.load(pkl_in)
pkl_in.close()

embed_masked = np.zeros((embed_dict['vectors'].shape[0], embed_dict['vectors'].shape[1]-1))
for comp in range(100):
    embed_masked[:,comp]=(embed_dict['vectors'][:,comp+1]/embed_dict['vectors'][:,0])

# unmask the embedding, that has been saved in masked form
embed = np.zeros((t1.shape[0],100))
embed[nonmask] = embed_masked

# delete masked values
masked_t1 = np.delete(t1, bigmask)
masked_embed = np.delete(embed, bigmask, axis=0)

# run linear models
for m in range(len(all_maps)):
    
    maps = all_maps[m]
    maps_str = all_maps_str[m]  
    
    print maps

    clf = linear_model.LinearRegression()
    clf.fit(masked_embed[:,maps], masked_t1)
    
    modelled_fit = clf.predict(masked_embed[:,maps])
    residuals = masked_t1 - clf.predict(masked_embed[:,maps])
    
    # write data back into cortex dimensions to avoid confusion
    modelled_fit_cortex = np.zeros((t1.shape[0])) 
    modelled_fit_cortex[nonmask_bigmask]=modelled_fit
    residuals_cortex = np.zeros((t1.shape[0]))  
    residuals_cortex[nonmask_bigmask]=residuals
    t1_cortex = np.zeros((t1.shape[0]))
    t1_cortex[nonmask_bigmask]=masked_t1
    
    model_dict = dict()
    model_dict['maps']=maps
    model_dict['coef']=clf.coef_
    model_dict['intercept']=clf.intercept_
    model_dict['modelled_fit']=modelled_fit_cortex
    model_dict['residuals']=residuals_cortex
    model_dict['t1']=t1_cortex
    model_dict['score'] = clf.score(masked_embed[:,maps], masked_t1)
    model_dict['corr'] = stats.pearsonr(modelled_fit, masked_t1)
    
    print 'coeff', clf.intercept_, clf.coef_
    print 'score',model_dict['score']
    print 'corr', model_dict['corr']
    
    pkl_out = open(model_file%(maps_str), 'wb')
    pickle.dump(model_dict, pkl_out)
    pkl_out.close()
        
    
    
