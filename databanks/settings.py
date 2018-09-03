import os
script_dir = os.path.dirname(os.path.realpath(__file__))

settings = {}
# Load settings
filename = os.path.join(script_dir, 'default_settings.py')
with open(filename) as config_file:
    exec(compile(config_file.read(), filename, 'exec'), settings)
