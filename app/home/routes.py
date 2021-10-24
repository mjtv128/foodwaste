# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from app.home import blueprint
from flask import render_template, redirect, url_for, request
from flask_login import login_required, current_user
from app import login_manager
from jinja2 import TemplateNotFound
from google.cloud import bigquery
import json
import pandas as pd
import sys
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly
def waste_table():
    unitdict = {"lb":1, "cup":0.53,"tbsp":0.03,"tsp":0.013,"oz":0.06}
    client = bigquery.Client()
    demand = (
            'SELECT * FROM `food-waste-329921.Foodwaste.Demand`;'
        )
    inventory = (
        'SELECT * FROM `food-waste-329921.Foodwaste.Inventory`;'
    )
    predicted = (
            'SELECT * FROM `food-waste-329921.Foodwaste.Predicted`;'
        )
    recipe = (
            'SELECT * FROM `food-waste-329921.Foodwaste.Recipe`;'
        )

    Demand = client.query(demand).to_dataframe().sort_values(by=['Date', 'Recipe'])
    Inventory = client.query(inventory).to_dataframe()
    Predicted = client.query(predicted).to_dataframe().sort_values(by=['Date', 'ITEM'])
    Recipe = client.query(recipe).to_dataframe()
    diff=Predicted['Predicted_Servings']-Demand['Quantity']
    leftoverdf=Demand.copy()
    leftoverdf['Quantity']=diff
    qtyleft_dfs=[]

    for i in range(len(leftoverdf)):
        recipe_i = leftoverdf.Recipe[i]    
        recip=Recipe[Recipe['Recipe_Name']==recipe_i]
        divid=leftoverdf['Quantity'][i]/recip['Servings'].unique()[0]
        df_i = pd.DataFrame(data={"ingredient":recip['Ingredients'],"qtywasted":divid,"unit":recip['Unit']})
        qtyleft_dfs.append(df_i)
    dfwasted = pd.concat(qtyleft_dfs,ignore_index=True).sort_values(by=['ingredient'])
    dfwasted1=dfwasted.groupby('ingredient')['qtywasted'].sum().reset_index()
    dfwasted1['ingredient']=dfwasted1['ingredient'].str.lower()
    dfwasted1['unit']=dfwasted['unit']
    dfwasted1['qtywasted_converted'] = [dfwasted1['qtywasted'][i]*unitdict[dfwasted1['unit'][i]] for i in range(len(dfwasted1))]
    moneywasted=[]
    percentage=[]
    for i in range(len(dfwasted1)):
        #print(dfwasted1['ingredient'][i])
        tyu=Inventory[Inventory['Product']==dfwasted1['ingredient'][i]]
        moneywasted.append(float(dfwasted1['qtywasted_converted'][i]*tyu['Unit_Price__']))
        percentage.append(float((dfwasted1['qtywasted_converted'][i]*100)/tyu['Count_No']))
    moneyinvent=pd.DataFrame(data={'ingredient':dfwasted1.ingredient,'qtywasted':dfwasted1.qtywasted_converted,'moneywasted':moneywasted,'percentage':percentage})
    moneyinvent = moneyinvent.sort_values(by=["percentage"])
    moneyinvent = moneyinvent.round(2)
    return moneyinvent

def plot():
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
        title_text="Top 6 Food Wasted",
        # Add annotations in the center of the donut pies.
        annotations=[
        dict(text=df['ingredient'][0], x=0.12, y=0.8, font_size=10, showarrow=False),
        dict(text=df['ingredient'][1], x=0.50, y=0.8, font_size=10, showarrow=False),
        dict(text=df['ingredient'][2], x=0.89, y=0.8, font_size=10, showarrow=False),
        dict(text=df['ingredient'][3], x=0.12, y=0.2, font_size=10, showarrow=False),
        dict(text=df['ingredient'][4], x=0.50, y=0.2, font_size=10, showarrow=False),
        dict(text=df['ingredient'][5], x=0.89, y=0.2, font_size=10, showarrow=False)        
                    ])
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON

@blueprint.route('/index')
@login_required
def index():
    graphJSON = plot()
    return render_template('index.html', segment='index',graphJSON = graphJSON)

@blueprint.route('/table')
@login_required
def table():
    try:
        # if not template.endswith( '.html' ):
        #     template += '.html'

        # Detect the current page
        print("here")
        segment = get_segment( request )
        table = waste_table()
  
    # parsing the DataFrame in json format.
        json_records = table.reset_index().to_json(orient ='records')
        data = []
        data = json.loads(json_records)
        print(data)
        # context = {'d': data}
        return render_template('table.html', table=data)

    except TemplateNotFound:
        return render_template('page-404.html'), 404
    
    except:
        return render_template('page-500.html'), 500

@blueprint.route('/chart')
@login_required
def chart():
    try:
        # if not template.endswith( '.html' ):
        #     template += '.html'

        # Detect the current page
        segment = get_segment( request )

        # # Serve the file (if exists) from app/templates/FILE.html
        return render_template('chartjs.html', segment=segment )

    except TemplateNotFound:
        return render_template('page-404.html'), 404
    
    except:
        return render_template('page-500.html'), 500


# Helper - Extract current page name from request 
def get_segment( request ): 
    try:
        segment = request.path.split('/')[-1]
        if segment == '':
            segment = 'index'

        return segment    
    except:
        return None  
