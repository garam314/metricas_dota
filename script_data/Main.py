"""
Usage:
  Main.py --config <YAML>
  Main.py (-h | --help)

Options:
  -h --help   Muestra esta ayuda.
  --config <YAML>     Archivo YAML de configuracion.
"""

import opendota
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import yaml
from docopt import docopt
from Dota import Dota

def main():
    args = docopt(__doc__, version="Matches 2.0")
    if os.path.exists(args['--config']):
        with open(args['--config'], "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    dota = Dota(config)
    dota.get_graph()

if __name__ == '__main__':
    main()