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
6. Run summary_soil_property.py from your env
7. Please disregard any warning about "pj_obj_create*"

Usage:
> summary_soil_property.py [-h] --lon LON --lat LAT --win WIN --depth DEPTH

Example of simulation:
> $ (gis-scripts_env) python path/to/summary_soil_property.py --lon=103.84 --lat=15.76 --win=3 --depth=350
>
>Check directory for the following file: path/to/scripts/outputs/taw-103.84-15.76-350mm.csv

To get help, please run:
> $ (gis-scripts_env) python path/to/summary_soil_property.py -h
>
> This script interpolates TAW value for a specific location in Thailand
>
>   optional arguments:
>   -h, --help     show this help message and exit
>
>  --lon LON      longitude value, e.g. 103.98
>
>  --lat LAT      latitude value, e.g. 15.88
>
>  --win WIN      window size, e.g. enter '3' for a window size of 3x3
>
>  --depth DEPTH  depth value in mm, e.g. 350

