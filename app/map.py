import requests
import json
import pandas as pd
import textwrap
from bokeh.layouts import row, widgetbox
from bokeh.io import output_file, show, curdoc
from bokeh.models.callbacks import CustomJS
from bokeh.models import (GMapPlot,
                          GMapOptions,
                          ColumnDataSource,
                          Circle,
                          DataRange1d,
                          PanTool,
                          WheelZoomTool,
                          BoxSelectTool)
from bokeh.models import Slider, Select, HoverTool, Button


ENDPOINT = 'https://data.sfgov.org/resource/bbb8-hzi6.json'
api_key = 'AIzaSyCl8urIXqsxsBEfguHDIWqV27FvVfSzdrE'
DAYS_OF_THE_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
                    'Friday', 'Saturday', 'Sunday']

data = requests.get(ENDPOINT).json()
df = pd.DataFrame(data, dtype=float)

clean_hour = lambda s: int(s.split(':')[0])

df['end24int'] = df.apply(lambda row: clean_hour(row['end24']), axis=1)
df['start24int'] = df.apply(lambda row: clean_hour(row['start24']), axis=1)
df['locationdesc_wrapped'] = df.apply(
    lambda row: textwrap.fill(str(row['locationdesc']),
                              width=20), axis=1)

SF_COORDS = dict(lat=37.7568649,
                 lng=-122.4413791)

map_options = GMapOptions(**SF_COORDS,
                          map_type="roadmap",
                          zoom=12)

hover = HoverTool(
    tooltips="""
        Name: <br>@applicant</br>
        Details: <pre>@locationdesc_wrapped</pre>""")

plot = GMapPlot(x_range=DataRange1d(),
                y_range=DataRange1d(),
                map_options=map_options,
                tools=[hover])

plot.api_key = api_key
base_title = "San Francisco Mobile Food Schedule"

source = ColumnDataSource(df)

circle = Circle(x="longitude",
                y="latitude",
                size=5,
                fill_color="blue",
                fill_alpha=0.8,
                line_color=None)

plot.add_glyph(source, circle)

plot.add_tools(PanTool(), WheelZoomTool(), BoxSelectTool())

hour = Slider(title="hour",
              start=0,
              end=24,
              value=12,
              step=1)

day = Select(title="Day of the Week",
             value="Monday",
             options=DAYS_OF_THE_WEEK)

location_callback = CustomJS(args=dict(map_options=plot.map_options),
                             code="""
    var lat = map_options.lat;
    var long = map_options.long;
    var zoom = map_options.zoom;
    function success(pos) {
            map_options.lat = pos.coords.latitude;
            map_options.lng = pos.coords.longitude;
            map_options.zoom = 15;
            map_options.change.emit();
    };
    function error(err) {
        console.warn('No geolocator')
    };
    options = {enableHighAccuracy: true};
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(success, error, options);
    }
""")

current_location = Button(label='Current location',
                          button_type='success',
                          callback=location_callback)

### interactive
def update():
    day_val = day.value
    hour_val = hour.value

    plot.title.text = '{} on {} at {}'.format(base_title, day_val, hour_val)

    selected = df.loc[(df['dayofweekstr'] == day_val)
                       & (df['start24int'] <= hour_val)
                       & (hour_val <= df['end24int'])]
    source.data = selected.to_dict(orient='list')

    # GMapPlot broken right now
    plot.map_options.zoom = 11
    plot.map_options.zoom = 12


change_controls = [hour, day]
controls = [*change_controls, current_location]
for control in change_controls:
    control.on_change('value', lambda attr, old, new: update())

sizing_mode = 'fixed'
layout = row(
    plot,
    widgetbox(*controls, sizing_mode=sizing_mode)
)

update()
update()
curdoc().add_root(layout)
