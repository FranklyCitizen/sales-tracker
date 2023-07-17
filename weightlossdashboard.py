import dash
from dash import dcc, html
import plotly.graph_objects as go
import os
import pandas as pd
from datetime import datetime, timedelta
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

# Import the keyword from the config file
from config import keyword

# Set the title of the webpage
app.title = f"Sales Analysis. {keyword}."

# List all product Excel files
excel_files = [f for f in os.listdir('.') if f.endswith('.xlsx')]

# Define the layout
app.layout = html.Div([
    
    html.H1([html.Span("Sales Analysis.", style={"color": "#EDEFF8"}), f" {keyword}"], className="headline"),

    dcc.Graph(id='total-sales-graph'),
    html.Div(id='total-sales'),
    html.Div([
        dcc.Dropdown(
            id='sort-dropdown',
            options=[
                {'label': '24 hours', 'value': '24h'},
                {'label': '7 days', 'value': '7d'},
                {'label': '30 days', 'value': '30d'},
            ],
            value='24h',
            className='sort-by-sales'
        )
    ], style={'display': 'flex', 'justifyContent': 'center'}),  # Inline styling to center the dropdown

    html.Div(id='cards-container', className='my-4'),
])

@app.callback(
    [Output('total-sales', 'children'),
     Output('cards-container', 'children'),
     Output('total-sales-graph', 'figure')],
    Input('sort-dropdown', 'value')
)
def update_page(sort_value):
    cards = []

    total_sales_24h = 0
    total_sales_7d = 0
    total_sales_30d = 0

    all_sales_df = pd.DataFrame()

    for excel_file in excel_files:
        df = pd.read_excel(excel_file)
        product_name = df['Product Name'].iloc[-1]
        review_count = df['Review Count'].iloc[-1]
        avg_rating = df['Average Rating'].iloc[-1]
        price = df['Price'].iloc[-1]

        df['Datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
        
         # Ignore rows with negative "Units Sold" values
        df = df[df['Units Sold'] > 0]

        sales_24h = df.loc[df['Datetime'] >= datetime.now() - timedelta(hours=24), 'Units Sold'].sum()
        sales_7d = df.loc[df['Datetime'] >= datetime.now() - timedelta(days=7), 'Units Sold'].sum()
        sales_30d = df.loc[df['Datetime'] >= datetime.now() - timedelta(days=30), 'Units Sold'].sum()

        total_sales_24h += sales_24h
        total_sales_7d += sales_7d
        total_sales_30d += sales_30d

        all_sales_df = all_sales_df.append(df[['Datetime', 'Units Sold']].rename(columns={'Units Sold': product_name}), ignore_index=True)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['Datetime'], y=df['Units Sold'], mode='lines'))
        fig.update_layout(
            plot_bgcolor='rgb(0, 0, 0, 0)',
            paper_bgcolor='rgb(0, 0, 0, 0)',
            font=dict(color='rgb(200, 200, 200)'),
            
            xaxis=dict(
                gridcolor='rgb(80, 80, 80)',
                zerolinecolor='rgb(80, 80, 80)'
            ),
            yaxis=dict(
                gridcolor='rgb(80, 80, 80)',
                zerolinecolor='rgb(80, 80, 80)'
            )
        )

        card = dbc.Card([
            dbc.CardHeader(product_name),
            dbc.CardBody([
                html.P(f'Number of reviews: {review_count}', className='card-text'),
                html.P(f'Average rating: {avg_rating}', className='card-text'),
                html.P(f'Latest price: {price}', className='card-text'),
                html.P(f'Sales in the last 24 hours: {sales_24h}', className='card-text'),
                html.P(f'Sales in the last 7 days: {sales_7d}', className='card-text'),
                html.P(f'Sales in the last 30 days: {sales_30d}', className='card-text'),
                dcc.Graph(figure=fig)
            ])
        ], id=f'card-{excel_file}', className='card')

        cards.append((card, sales_24h, sales_7d, sales_30d))

    if sort_value == '24h':
        cards.sort(key=lambda x: x[1], reverse=True)
    elif sort_value == '7d':
        cards.sort(key=lambda x: x[2], reverse=True)
    elif sort_value == '30d':
        cards.sort(key=lambda x: x[3], reverse=True)

    cards_row = dbc.Row([dbc.Col(card[0], md=4) for card in cards], justify='around')

    total_sales_div = html.Div([
    dbc.Card([
        dbc.CardBody([
            html.H2(f"Total sales for all products in the last 24 hours: {total_sales_24h}", className="total-sales-text"),
            html.H2(f"Total sales for all products in the last 7 days: {total_sales_7d}", className="total-sales-text"),
            html.H2(f"Total sales for all products in the last 30 days: {total_sales_30d}", className="total-sales-text")
        ])
    ], className='card total-sales-card')
], className='total-sales-container')  # Add a class to the parent container





    total_sales_df = all_sales_df.groupby('Datetime').sum().reset_index()

    total_sales_fig = go.Figure()
    total_sales_fig.add_trace(go.Scatter(x=total_sales_df['Datetime'], y=total_sales_df.sum(axis=1), mode='lines', name='Total Sales'))

    top_3_products = sorted([(col, all_sales_df.loc[all_sales_df['Datetime'] >= datetime.now() - timedelta(hours=24), col].sum()) for col in all_sales_df.columns if col != 'Datetime'], key=lambda x: x[1], reverse=True)[:3]
    for product, _ in top_3_products:
        total_sales_fig.add_trace(go.Scatter(x=all_sales_df['Datetime'], y=all_sales_df[product], mode='lines', name=product))

    total_sales_fig.update_layout(
        plot_bgcolor='rgb(24, 24, 24)',
        paper_bgcolor='rgb(24, 24, 24)',
        font=dict(color='rgb(200, 200, 200)'),
        title='Total Sales Over Time',
        xaxis=dict(
            gridcolor='rgb(80, 80, 80)',
            zerolinecolor='rgb(80, 80, 80)'
        ),
        yaxis=dict(
            gridcolor='rgb(80, 80, 80)',
            zerolinecolor='rgb(80, 80, 80)'
        )
    )

    return total_sales_div, cards_row, total_sales_fig

if __name__ == '__main__':
    app.run_server(debug=True)
