#!/usr/bin/env python
#
############################################################################
#
# MODULE:	   r.in.landsat8
# AUTHOR(S):   	Micha Silver 
#				micha@arava.co.il  Arava Drainage Authority	
# PURPOSE:	  Import bands of Landsat8 and perform transform to relectivity   
# COPYRIGHT: 	This program is free software under the GNU General Public
#			   License (>=v2). Read the file COPYING that comes with GRASS
#			   for details.
# REVISIONS:	April 2015, compatible with GRASS 7.0
#############################################################################
#%module
#% description: Import bands from directory containing Landsat8 tiles in GeoTIFF format, and create from each band the TOA reflectivity
#% keywords: raster
#% keywords: Landsat8
#% keywords: Reflectivity
#%end
#% option
#% key: input 
#% description: Name of top level directory which contains the directories of Landsat tiles 
#% required: yes
#%end
#%option
#% key: bands
#% type: integer
#% multiple : yes
#% description: Comma separated list of band numbers to be processed
#%end

import sys, os
import grass.script as grass

def cleanup():
    grass.message("Finished")

def get_metadata(dir, bands):
    """
    Read the Metadata file (*_MTL.txt) from directory dir
    Scan for the REFLECTANCE values and save into a dict
    Also get the Sun Elevation value
    """
    
    mtl_dict = {}
    mtl_file = os.path.basename(dir)+"_MTL.txt"
    #grass.message("Metadata file: %s" % mtl_file)
    mtl_path = os.path.join(dir, mtl_file)
    grass.message("Reading metadata file: %s" % mtl_path)
    with open(mtl_path, 'r') as m:
        lines = m.readlines()
        m.close()
    
    # Populate the dict with values from the MTL file.
    # Use the float() function to read Scientific notation as real numbers
    cnt = 0
    for i in range(len(lines)):
        if "REFLECTANCE_MULT_" in lines[i]:
            key, val = lines[i].split('=')
            mtl_dict[key.strip()] = float(val)
            cnt += 1
        if "REFLECTANCE_ADD_" in lines[i]:
            key, val = lines[i].split('=')
            mtl_dict[key.strip()] = float(val)
            cnt += 1
        if "SUN_ELEVATION" in lines[i]:
            key, val = lines[i].split('=')
            mtl_dict[key.strip()] = float(val)
            cnt += 1
    
    for key in mtl_dict:
        grass.message("Key:%s=Value:%f" % (key, mtl_dict[key]))
        
    return mtl_dict
    
def dn_to_reflectance(dir, dict, bands):
    """
    Convert Digital Number values to reflectance for each band in the directory dir
    using the metadata values from dict
    See http://landsat.usgs.gov/Landsat8_Using_Product.php for details
    """
    basedir = os.path.basename(dir)
    cnt = 0
    for b in bands:
        tif_file = basedir+"_B"+str(b)+".TIF"
        tif_path = os.path.join(dir, tif_file)
        grass.message("Working on %s " % tif_path)
        # Import the tile
        rast = basedir.lower()+"_b"+str(b)
        grass.run_command('r.in.gdal', input=tif_path, output=rast, overwrite=True)
        grass.run_command('g.region', rast=rast, flags='p')
        rho = rast+"_reflect"
        # Get metadata values from the dict
        mult = '{:f}'.format(dict["REFLECTANCE_MULT_BAND_"+str(b)])
        add = '{:f}'.format(dict["REFLECTANCE_ADD_BAND_"+str(b)])
        sun = dict["SUN_ELEVATION"]
        zenith = '{:f}'.format(90.0-sun)
        # Prepare mapcalc expression
        expr = rho+" = ("+str(mult)+"*"+rast+"+("+str(add)+"))/cos("+zenith+")"
        grass.message("Calculating expression: %s" % expr)
        grass.mapcalc(expr, overwrite=True)
        grass.message("Created reflectance raster: %s" % rho)
        cnt += 1
        
    grass.message("Completed %s reflectance rasters" % cnt)
    
def main():
    top_dir = options['input']
    band_list = options['bands'].split(',')
    dirs = os.listdir(top_dir)
    for d in dirs:
        tile_path = os.path.join(top_dir, d)
        if os.path.isdir(tile_path):
            grass.message("Working in %s" % tile_path)
            metadata = get_metadata(tile_path, band_list)
            dn_to_reflectance(tile_path, metadata, band_list)
    
if __name__ == "__main__":
	options, flags = grass.parser()
	sys.exit(main())
