# UnclaimedLand
Project that aims to visualise Unclaimed Land in the UK. Website is accessible at https://sachinthakrar.me/unclaimedland. Various files to recreate the underlying data are available here.

## Scraper
The scraper folder contains the files necessary to scrape and create the Council-by-Council data on Unclaimed Land in the UK. To recreate this, simply run the `scrape.py` file. The file has many dependencies: pandas, geopandas, mapshaper, ogr2ogr, and shapely. Additionally, it should be said that the file, by default, applies some simplification to the file. If you would like to remove this simplification or modify the output type, there is an explanation as to how to do so.

Note: the scraper uses mapit data, which has a low API limit (~50 downloads/day) without a paid plan. The scraper will stop working once that limit is hit. 

## Website
The website folder contains, well, the website. Additionally, the .topojson files of Council-by-Council unclaimed land are available here. They are kept in the assets folder, though the files themselves are compressed with .tar.gz. Uncompressing the files and placing them all in the assets directory will allow the website to work. Note that it requires a basic server, `python3 -m http.server` will suffice.

## To-Do
Currently, this project only displays data for England and Wales. I have been unable to find suitable boundary data for Scotland, as the Land Registry data available uses the historical 'Registration County' boundaries, which do not correspond well with current boundaries. Once this is found, I will update the site. 