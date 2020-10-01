PLUGIN_VERSION=1.0.2
PLUGIN_ID=open-weather-map

all:
	cat plugin.json|json_pp > /dev/null
	rm -rf dist
	mkdir dist
	zip -r dist/dss-plugin-${PLUGIN_ID}-${PLUGIN_VERSION}.zip code-env custom-recipes parameter-sets python-connectors python-lib plugin.json
	
