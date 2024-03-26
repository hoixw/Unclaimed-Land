import pandas as pd
import requests
import zipfile
import os
import subprocess
import re
import geopandas as gpd

# Function to download and unzip INSPIRE files, then convert GML to GeoJSON
def get_inspire(row):
    num, inspire_url = row["Number"], row["INSPIRE Download"]
    inspire_zip_path = f"{num}.zip"
    inspire_response = requests.get(inspire_url)
    with open(inspire_zip_path, "wb") as f:
        f.write(inspire_response.content)
    
    with zipfile.ZipFile(inspire_zip_path, "r") as zip_ref:
        zip_ref.extractall(f"./{num}")
    
    os.remove(inspire_zip_path)  # delete the zip file after extracting
    os.remove(f"./{row["Number"]}/INSPIRE Download Licence.pdf")  # delete the PDF file
    
    gml_file = f"./{num}/Land_Registry_Cadastral_Parcels.gml"
    geojson_file = f"./{num}/{num}.geojson"


    # Clean dead IP links from GML file (causes massive delays)
    with open(gml_file, "r", encoding="utf-8") as file:
        gml_contents = file.read()
    
    gml_contents = re.sub(r' http:\/\/192\S*?(?=[\s"])', "", gml_contents)
    
    with open(gml_file, "w", encoding="utf-8") as file:
        file.write(gml_contents)
    
    ## Convert GML to GeoJSON, delete old GML + .gfs output from ogr2ogr
    subprocess.run(["ogr2ogr", "-f", "GeoJSON", geojson_file, gml_file, "-s_srs", "EPSG:27700", "-t_srs", "EPSG:4326"])
    os.remove(gml_file)  # delete original GML file
    os.remove(gml_file[:-2] + "fs") # remove .gfs file

    
    # Clean redundant info from the  GeoJSON file
    with open(geojson_file, "r", encoding="utf-8") as file:
        file_contents = file.read()

    file_contents = re.sub(r'"crs":(.*?)\n', "", file_contents)
    file_contents = re.sub(r'"name":(.*?)\n', "", file_contents)
    file_contents = re.sub(r'"properties"([^}]*)\}, ', "", file_contents)
    
    with open(geojson_file, "w", encoding="utf-8") as file:
        file.write(file_contents)


# Function to download MapIt files and rename
def get_mapit(row):
    num, mapit_url = row["Number"], row["MapIt Download"]
    mapit_response = requests.get(mapit_url)
    mapit_path = f"./{num}/{num}_boundary.geojson"
    with open(mapit_path, "wb") as f:
        f.write(mapit_response.content)


def dissolve_and_shape(row):
    num = row["Number"]
    polygons = gpd.read_file(f"./{num}/{num}.geojson")
    district_boundary = gpd.read_file(f"./{num}/{num}_boundary.geojson")

    # Merge all polygons into one. If an error is thrown, fix INSPIRE file. 
    # (many of the provided geometries are invalid)
    try:
        merged_polygons = polygons.dissolve()
    except Exception as e:
        polygons_valid = polygons.make_valid()
        polygons_valid.to_file(f"./{num}/{num}.geojson")
        polygons = gpd.read_file(f"./{num}/{num}.geojson")
        merged_polygons = polygons.dissolve()

    # Find the difference
    not_covered = gpd.overlay(district_boundary, merged_polygons, how="difference").dissolve()
    
    not_covered.to_file(f"./{num}/{num}_dissolved.geojson", driver="GeoJSON")
    os.remove(f"./{num}/{num}.geojson")
    os.remove(f"./{num}/{num}_boundary.geojson")


    """
    This mapshaper simplifies the file by removing slivers and running Douglas-Peucker simplification.
    It then cleans the file and outputs it as a topoJSON, a variant of geoJSON. 

    If you would like to remove the simplification, this can easily be done by deleting the following commands:
    "-filter-slivers", "-simplify", "rdp", "percentage=0.4",
    The simplification is necessary for internet viewing, but it does reduce precision. 

    If you would like to change the file output type, it is derived implicitly by mapshaper, with the possible
    options being: shapefile|geojson|topojson|json|dbf|csv|tsv|svg 
    """
    subprocess.run(["mapshaper", "-i", f"files=./{num}/{num}_dissolved.geojson", "no-topology",
                   "-filter-slivers", "-simplify", "rdp", "percentage=0.4", "-clean",
                   "-o", f"./Final/{num}.topojson"])
    
    ## Remove remaining non-Final files and folder
    os.remove(f"./{num}/{num}_dissolved.geojson")
    os.rmdir(f"./{num}")


# Main function to iterate through the CSV
def main(csv_path):
    df = pd.read_csv(csv_path)  # Assuming the CSV is tab-separated
    for index, row in df.iterrows():
        try:
            get_inspire(row)
            get_mapit(row)
            dissolve_and_shape(row)
        except Exception as e:
            print("Error: ", repr(e))
            print("Row: ", row)
            exit(2)

csv_path = "main.csv"
main(csv_path)