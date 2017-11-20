
# coding: utf-8

#%%
#Importing requiredpackages

import pandas as pd
import numpy as np
from Tkinter import Tk
from tkFileDialog import asksaveasfilename
from tkFileDialog import askdirectory
from tkinter import messagebox
import os


#%%
#Executing the tkinter prompt the location of the resistivity data

root = Tk() # we don't want a full GUI, so keep the root window from appearing
root.lift()
messagebox.showinfo("Directions for processing of Ohm Mapper Data", "For this script to work, all csv and xyz files that you want to be processed must be included in a single folder.")
folder = askdirectory(title="Select folder that contains all resistivity files for processing...") # show an "Open" dialog box and return the path to the selected file
Tk().withdraw

#%%
#Defining the function to insert blank rows within the geospatial csv file

def pir(df):
    nans = np.where(np.empty_like(df.values), np.nan, np.nan)
    data = np.hstack([nans, df.values]).reshape(-1, df.shape[1])
    return pd.DataFrame(data, columns=df.columns)
    
#%%
# Looping through file import, merging, and reorganization
import glob
q=0
for filename in glob.glob('{}/*.csv'.format(folder)):
    csv = pd.read_csv(filename,skiprows=18)

    csv1=pir(csv)
    csv1 = csv1.interpolate(axis=0)
    
    base = os.path.splitext(os.path.basename(filename))[0]
    lines=[]
    xyz_path = '{}/{}.xyz'.format(folder,base)
    with open(xyz_path,'rt') as infile:
    #contents=infile.read()
        for line in infile:
            lines.append(line.rstrip('\n'))
            
    n = lines[1].find('/Number of blocks is ')
    stop = lines[1][n+21:]

    xyz = pd.read_table(xyz_path,skiprows=5,sep='\s+',nrows=int(stop),usecols=[0,1,2],names=['X','Depth','Resistivity'])
    xyz.sort_values('X', inplace=True)
    csv1.dropna(inplace=True)
    csv1.sort_values('distace',inplace=True)
    xyz2=pd.merge_asof(xyz, csv1, left_on='X', right_on='distace', direction='nearest')
    xyz2.sort_values('Depth', inplace=True)
    depths = xyz2['Depth'].unique()
    xyz2['X_error_abs']=np.abs(xyz2['X']-xyz2['distace'])
    xyz2['Depth_n']=''
    xyz2['Resistivity_n']=''

    t=1
    for x in depths:
        xyz2['Depth_n'][xyz2['Depth']==depths[t-1]]='Depth{}'.format(t)
        xyz2['Resistivity_n'][xyz2['Depth']==depths[t-1]]='Resistivity{}'.format(t)
        t+=1
    dep_names=['Depth1']
    res_names=['Resistivity1']
    for x in range(1,len(depths)):
        col_n = 'Depth{}'.format(x+1)
        res_n = 'Resistivity{}'.format(x+1)
        dep_names.append(col_n)
        res_names.append(res_n)
        total_names = dep_names+res_names
        total_ordered = sorted(total_names)
    xyz_pivot = pd.pivot_table(xyz2,index=['Xutm','Yutm','elev','X', 'X_error_abs'],columns=['Resistivity_n', 'Depth_n'],values=['Resistivity', 'Depth'])
    xyz_pivot.columns = xyz_pivot.columns.droplevel(level=[0,1])
    xyz_pivot.columns=[total_ordered]
    xyz_pivot.reset_index(inplace=True)
    xyz_pivot['Line']=q+1
    final_list = ['Xutm','Yutm','elev','X','X_error_abs','Line']
    final_list = final_list +total_ordered
    xyz_pivot = xyz_pivot[final_list]
    

    if q>0:
        xyz_final = xyz_final.append(xyz_pivot, ignore_index=True)

    else:
        xyz_final = xyz_pivot
    q+=1

#%%
# Exporting output to csv
savefile = asksaveasfilename(defaultextension='.csv',title="Select filename and location for output of resistivity data...", filetypes=[('csv file', '*.csv')])
xyz_final.to_csv(savefile, index=False)


