from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from os import path
import pandas as pd
from datetime import datetime



driver = webdriver.Chrome('c:\\Users\\okolafa\\Downloads\\chromedriver.exe')  # Optional argument, if not specified will search path.
driver.get('https://www.alza.cz/televize-55-palcu/18862379.htm');




def start_check(driver):

    WebDriverWait(driver, 200).until(
        EC.presence_of_element_located((By.ID, "boxc"))
    )

    print("FOUND!")


def get_items(driver, df_items_new, current_date):

    boxes_block = driver.find_element_by_id('boxc')

    boxes = boxes_block.find_elements_by_class_name('box')

    print(f"Nalazeno jednotek: {len(boxes)}")

    for i, box in enumerate(boxes, start=1):
        name = box.find_element_by_class_name("name")
        price = box.find_element_by_class_name("c2")
        try:
            price_int = int(''.join(filter(str.isdigit, price.text)))
        except:
            print(f"Divná cena: {price.text}")
            price = box.find_element_by_class_name("bigPrice price_withVat")
            price_int = int(''.join(filter(str.isdigit, price.text)))
        print(f'{i}. NAZEV: {name.text}, CENA: {price_int}')
        df_items_new = df_items_new.append({'url':name.get_attribute('href'),'name':name.text, current_date:price_int}, ignore_index=True)

    print(df_items_new.tail())
    return df_items_new


def click_next(driver, page_num):
    next_id = f"pgby{page_num}"
    print(f"Hledám id {id}.")
    next = driver.find_element_by_id(next_id)
    print(f"Klikám na id: {next_id}")
    next.click()


# WAIT FOR presence_of_element_located https://selenium-python.readthedocs.io/waits.html
try:
    filename = 'ALZA_TVs.csv'
    page_num = 1
    current_date = datetime.today().strftime('%Y-%m-%d')

    if path.exists(filename):
        df_items = pd.read_csv(filename, index_col='url')
    else:
        df_items = pd.DataFrame(columns=["url","name", current_date])

    df_items_new = pd.DataFrame(columns=["url","name", current_date])

    while True:
        start_check(driver)
        df_items_new = get_items(driver, df_items_new, current_date)
        page_num = page_num + 1

        try:
            click_next(driver, page_num)
        except:
            print('Next nenalezeno - konec')
            break


finally:
    driver.quit()
    pass


df_merge = df_items.merge(df_items_new, on=["url", "name"], how="outer")
df_merge = df_merge.set_index('url')
df_merge.to_csv(filename)


#%%

import pandas as pd
import re
import plotly.graph_objects as go
import plotly.io as pio

pio.renderers.default = 'browser'


filename = 'ALZA_TVs.csv'

df = pd.read_csv(filename, index_col='url')


def manufacturer(row):
    try:
        pattern = r"^\S*\s(\S*)\s.*$"
        re_manufacturer = re.match(pattern, row['name'])
        manufacturer = re_manufacturer[1]
    except:
        manufacturer = 'DNK'

    return manufacturer

df['manufacturer'] = df.apply(manufacturer, axis=1)
df = df.sort_values(by="name")


#%%


# Data columns only
date_cols_names = []
for col in df.columns:
    if col.startswith('2020-'):
        date_cols_names.append(col)
print(f'Date names columns: {date_cols_names}')


# plotly figure setup
fig = go.Figure()

df_lowcost = df[df[date_cols_names[-1]] < 25000 ]

# one trace for each df column
for index, row in df_lowcost.iterrows():

    fig.add_trace(go.Scatter(
        x=date_cols_names,
        y=[row[date] for date in date_cols_names],
        name=row['name'],
        mode="lines+markers",
    ))

# one button for each df column
updatemenu= []
dropdown_list=[]
# one button for all
dropdown_list.append(dict(method='restyle',
                        label='ALL',
                        args=[{'y':df_lowcost[date_cols_names].values}] )
                  )
# one button for each df row
for manufacturer in df_lowcost.manufacturer.unique():
    dropdown_list.append(dict(method='restyle',
                        label=manufacturer,
                        args=[{'y':df_lowcost[df_lowcost.manufacturer == manufacturer][date_cols_names].values,
                               'text':df_lowcost[df_lowcost.manufacturer == manufacturer]["name"].values
                               }])
                  )

# some adjustments to the updatemenu
updatemenu=[]
your_menu=dict()
updatemenu.append(your_menu)
updatemenu[0]['buttons']=dropdown_list
updatemenu[0]['direction']='down'
updatemenu[0]['showactive']=True

# update layout and show figure
fig.update_layout(updatemenus=updatemenu)
fig.show()


# %%

previous_date = date_cols_names[len(date_cols_names) - 2:len(date_cols_names) - 1][0]
last_date = date_cols_names[len(date_cols_names) - 1:][0]


df_compare = df.copy(deep=True)

df_compare['dif_abs'] = df_compare[previous_date] - df_compare[last_date]
df_compare['dif_rel'] = df_compare[previous_date] / df_compare[last_date]

df_compare = df_compare[df_compare.dif_abs > 0].sort_values(by=['dif_rel'], ascending = False)
