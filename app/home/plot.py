from merge import waste_table
import plotly.graph_objects as go
from plotly.subplots import make_subplots

df = waste_table()
df.sort_values(by=['percentage'], inplace=True,ascending=False)

df['percentage']= df['percentage'].astype(float)
df['unused'] = 100 -df['percentage']

labels = ["Wasted","Used"]
# Create subplots: use 'domain' type for Pie subplot
fig = make_subplots(rows=2, cols=3, specs=[[{'type':'domain'},{'type':'domain'},{'type':'domain'}],[{'type':'domain'},{'type':'domain'},{'type':'domain'}]])
value = [[float(df['percentage'][i]),float(df['unused'][i])] for i in range(6)]

for i in range(6):
    row = 1 if i<3 else 2
    column = 1+i if i<3 else i-2    
    fig.add_trace(go.Pie(labels=labels, values=value[i], name=df['ingredient'][i]), row, column)

fig.update_traces(hole=.4, hoverinfo="label+percent+name")
fig.update_layout(
    title_text="Global Emissions 1990-2011",
    # Add annotations in the center of the donut pies.
    annotations=[
    dict(text=df['ingredient'][0], x=0.12, y=0.8, font_size=10, showarrow=False),
    dict(text=df['ingredient'][1], x=0.50, y=0.8, font_size=10, showarrow=False),
    dict(text=df['ingredient'][2], x=0.89, y=0.8, font_size=10, showarrow=False),
    dict(text=df['ingredient'][3], x=0.12, y=0.2, font_size=10, showarrow=False),
    dict(text=df['ingredient'][4], x=0.50, y=0.2, font_size=10, showarrow=False),
    dict(text=df['ingredient'][5], x=0.89, y=0.2, font_size=10, showarrow=False)        
                 ])
fig.show()