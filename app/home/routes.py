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


def waste_table():
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
        df_i = pd.DataFrame(data={"ingredient":recip['Ingredients'],"qtywasted":divid})
        
        qtyleft_dfs.append(df_i)
    dfwasted = pd.concat(qtyleft_dfs,ignore_index=True).sort_values(by=['ingredient'])
    dfwasted1=dfwasted.groupby('ingredient')['qtywasted'].sum()
    return dfwasted1


@blueprint.route('/index')
@login_required
def index():

    return render_template('index.html', segment='index')

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
