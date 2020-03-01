# gis-scripts
This project will contain most of my general purposes Python or R scripts related to GIS stuff.

The scripts require a virtual env:
```
conda create -n gis-scripts_env python=3.7
conda activate scripts_env
pip freeze > requirements.txt
```

## Project **proj-lstfd20**:

This script is optimized only for **Thailand** as of now. Follow the steps to get the script running:

1. Downlaod this [project](https://github.com/eusojk/gis-scripts/archive/master.zip) 
2. Downlaod [layers.zip](https://www.dropbox.com/s/74hpv9d56a8s461/layers.zip?dl=0)
3. Unzip layers.zip
4. Copy 'layers' directory into the 'proj-lstfd20' directory
5. 'proj-lstfd20' should only have two directories now
6. Run summary_soil_property.py from proj-lstfd20/scripts/ 
7. Please disregard any warning about "pj_obj_create*"

Example of simulation:
> $ (gis-scripts_env) python summary_soil_property.py
>
>This script is currently only supporting Thailand. Using geo coordinates not associated with this country will give misleading results!

> Enter 'R' to (re)start or 'Q' to quit: R

> Enter longitude: 102.765
>
> Enter latitude: 13.369
>
> Enter window size (e.g. enter '3' for 3x3): 3
>
> Enter soil depth (mm): 100
>
> Check directory for the following file:  taw-102.765-13.369-100mm.csv
