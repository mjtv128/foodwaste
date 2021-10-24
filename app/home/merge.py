import pandas as pd
from flask import Flask
from flask import render_template,request,url_for,redirect
from google.cloud import bigquery
import json

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

a = waste_table()
print(a)