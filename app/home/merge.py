import pandas as pd
from flask import Flask
from flask import render_template,request,url_for,redirect
from google.cloud import bigquery
import json


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
    print(moneyinvent.head())
    # moneyinvent = moneyinvent.sort_values(by="percentage")
    moneyinvent = moneyinvent.round(2)   
    return moneyinvent

#percentage=(dfwasted1['qtywasted']*100)/tyu['Count_No']
#a = waste_table()
#print(a)
#print(a.dtypes)
