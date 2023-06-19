import json
import subprocess
import time

# Load the template script
with open('template_script.py') as template_file:
    template_script = template_file.read()
    print('Template loaded')

# Load the county configurations
with open('county_config.json') as config_file:
    county_config = json.load(config_file)
    print('JSON loaded')

while True:  # This loop will cycle through the list of counties indefinitely
    # Generate county-specific scripts based on the template
    for county in county_config:
        county_name = county['name']
        county_script = template_script.replace('scrape_data(county_name, url, xpath1, xpath2, start_date_offset, end_date_offset)',
                                                f'scrape_data("{county_name}", "{county["url"]}", "{county["xpath1"]}", "{county["xpath2"]}", "{county["start_date_offset"]}", "{county["end_date_offset"]}")')
        print(f'Running county: {county_name}')

        # Write the county-specific script to a file
        script_file_name = f'{county_name}_script.py'
        with open(script_file_name, 'w') as county_script_file:
            county_script_file.write(county_script)

        # Run the county-specific script
        try:
            subprocess.check_call(['python', script_file_name])
        except subprocess.CalledProcessError:
            print(f'Error occurred in {county_name} script. Moving on to the next county.')

    # Sleep for a day before starting over
    time.sleep(60 * 15)

print('Scripts generated for all counties')
