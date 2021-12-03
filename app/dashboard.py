from flask import render_template, request, flash, redirect, url_for
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from app.models import User, Dashboard
from app import db
from app.backend.company import Company
from app.backend.summary.compliance import getCompliance, natlaw_urls, jdsupra_urls
from app import app

from bokeh.application import Application
from bokeh.application.handlers import FunctionHandler
from bokeh.plotting import figure
from bokeh.embed import server_document
from bokeh.models import ColumnDataSource, Select, CheckboxGroup, CustomJS, Range1d, LinearAxis, Span, Label
from bokeh.models.axes import LogAxis
from bokeh.layouts import layout
from bokeh.server.server import BaseServer
from bokeh.server.tornado import BokehTornado
from bokeh.server.util import bind_sockets
from threading import Thread
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
import asyncio

import pandas as pd
import numpy as np
import pickle
import os

# global df being used for the graph (changes with the dropdowns)
df = None
sentiment_df = None
current_feature = None
current_period = None
companyObject = None

def dashboard(companyName):

    # setup
    print('getting bulk data...')
    print('Getting ticker symbol...')
    global companyObject
    companyObject = Company(companyName)

    if not companyObject.found:
        print('Company not found!')
        return render_template('companyNotFound.html', title='Company Not Found', companyName=companyName)

    ################################ stocks ###########################################################

    keys = ['bid', 'ask', 'weeklyHigh', 'weeklyLow']
    stockInfo = dict.fromkeys(keys, 0)
    print('Getting stock price...')
    stockInfo['bid'], stockInfo['ask']  = companyObject.getStockPrice()
    print('Getting historical data...')
    infoDF = companyObject.getHistoricalPricesDf(period='5d')
    stockInfo['weeklyHigh'] = round(max(infoDF['High']),2)
    stockInfo['weeklyLow'] = round(min(infoDF['Low']),2)
    print('Getting Stock Price Change...')
    # stockInfo['dailyMvmt'] = companyObject.getStockPriceChange()

    ################################## Bokeh graph ######################################################

    def create_stocks_graph(doc):
        global df, sentiment_df, current_feature, current_period, companyObject
        feature_names = ['Open', 'High', 'Low', 'Close']
        periods = ['1d','5d','1mo','3mo','6mo','1y','2y','5y','10y','ytd','max']
        default_period = '3mo'
        default_feature = 'Close'
        current_feature = default_feature
        current_period = default_period
        base = os.getcwd()
        sentiment_path = base + "/app/static/sentiment_csv/" + companyObject.ticker + ".csv"
        sentiment_df = pd.read_csv(sentiment_path)
        df = companyObject.getHistoricalPricesDf(period=default_period)
        source = ColumnDataSource(data={

        'x' : df.index,

        'y' : df['Close']
        })

        p = figure(title=f"Stocks at {default_feature} for past {default_period}",
        x_axis_label='Date',
        y_axis_label=default_feature,
        tools="pan,wheel_zoom,reset,box_zoom",
        plot_width=920,
        plot_height=600,
        x_axis_type="datetime",
        sizing_mode='fixed')

        # x ticks cleaning
        df.index = pd.to_datetime(df.index)
        df.index.name = 'Date'
        df.sort_index(inplace=True)

        sentiment_df['Time'] = pd.to_datetime(sentiment_df['Time'])

        # shift sentiment graph
        earliest_sentiment = sentiment_df['Time'].iloc[0]
        df_subset = df[df.index >= earliest_sentiment]
        avg_df_subset = df_subset['Close'].mean()
        sentiment_df['Sentiment'] *= 10
        sentiment_df['Sentiment'] += avg_df_subset

        # make line graphs
        stock_line = p.line(x='x', y='y', legend_label = "Stock", line_width=2, line_alpha=0.6, line_color='blue', source=source)
        sentiment_line = p.line(x=sentiment_df['Time'],
            y=sentiment_df['Sentiment'],
            legend_label = "Sentiment",
            line_width=2,
            line_alpha=0.6,
            line_color='red')

        # sentiment reference lines
        neutralline = Span(location=avg_df_subset + 5, dimension='width', line_color='black', line_dash='dashed', line_width=1, line_alpha=0.5)
        neutralLabel = Label(x=70, y=avg_df_subset + 5.2, x_units='screen', text='Neutral Sentiment', render_mode='css', border_line_alpha=0,
        background_fill_color='white', background_fill_alpha=1.0)
        p.renderers.extend([neutralline, neutralLabel])

        # figure styling
        p.outline_line_color = 'black'
        p.legend.visible = True
        p.legend.click_policy="hide"

        checkbox = CheckboxGroup(labels=["Stock", "Sentiment"], active=[0,1])
        callback = CustomJS(code="""
                            stock_line.visible = false;
                            sentiment_line.visible = false;
                            neutralline.visible = false;
                            neutralLabel.visible = false;
                            // p.xaxis.visible = false;

                            // cb_obj injected in by the callback
                            if (cb_obj.active.includes(0)){
                                stock_line.visible = true;
                                // p.xaxis.visible = true;
                                } // 0 index box is stock_line

                            if (cb_obj.active.includes(1))
                            {sentiment_line.visible = true;
                            neutralline.visible = true;
                            neutralLabel.visible = true;
                            }
                            """,
                    args={'stock_line': stock_line, 'sentiment_line': sentiment_line, 'neutralline': neutralline, 'p':p, 'neutralLabel':neutralLabel})

        checkbox.js_on_change('active', callback)

        def update_plot(attr, old, new):
            global df, current_feature, current_period
            if new in feature_names:
                # change feature
                print('updating feature')
                print('old:', old)
                print('new:', new)
                current_feature = new
                p.yaxis.axis_label = current_feature # update y-axis
                # p.title = f"Stocks at {current_feature} for past {current_period}"
                source.data = {
                    'x' : df.index,
                    'y' : df[current_feature]
                }
            else:
                # change period
                print('updating period')
                print('old:', old)
                print('new:', new)
                current_period = new
                df = companyObject.getHistoricalPricesDf(period=new)
                df.index = pd.to_datetime(df.index)
                df.index.name = 'Date'
                df.sort_index(inplace=True)
                x_ticks = [d.strftime("%m/%d/%Y)")[:-1] for d in df.index.date]
                # p.title = f"Stocks at {current_feature} for past {current_period}"
                source.data = {
                    'x' : df.index,
                    'y' : df[current_feature]
                }


        # add selects
        period_select = Select(title="Period", value=default_period, options=periods)
        feature_select = Select(title="Feature", value=default_feature, options=feature_names)
        period_select.on_change("value", update_plot) # update period
        feature_select.on_change("value", update_plot) # update feature

        doc.add_root(layout(
            [feature_select, period_select],
            [checkbox],
            [p]))

    # can't use shortcuts here, since we are passing to low level BokehTornado
    bkapp = Application(FunctionHandler(create_stocks_graph))

    # This is so that if this app is run using something like "gunicorn -w 4" then
    # each process will listen on its own port
    if app.config['IN_PRODUCTION']:
        sockets, port = bind_sockets("www.nittanydatalabs.org", 0)
    else:
        sockets, port = bind_sockets("localhost", 0)

    # initiate bokeh server
    def bk_worker():
        # https://github.com/bokeh/bokeh/blob/1.1.0/examples/howto/server_embed/flask_embed.py
        asyncio.set_event_loop(asyncio.new_event_loop())

        if app.config['IN_PRODUCTION']:
            bokeh_tornado = BokehTornado({'/bkapp': bkapp}, extra_websocket_origins=["*"])
        else:
            bokeh_tornado = BokehTornado({'/bkapp': bkapp}, extra_websocket_origins=["localhost:8000"])
        bokeh_http = HTTPServer(bokeh_tornado)
        bokeh_http.add_sockets(sockets)

        server = BaseServer(IOLoop.current(), bokeh_tornado, bokeh_http)
        server.start()
        server.io_loop.start()

    Thread(target=bk_worker).start()

    # stocks graph script
    if app.config['IN_PRODUCTION']:
        script = server_document('http://nittanydatalabs.org:%d/bkapp' % port)
    else:
        script = server_document('http://localhost:%d/bkapp' % port)

    # refresh custom_sectors before initially generating dashboard
    current_user.summaries_sectors = pickle.dumps([])

    ################################## Summaries ######################################################

    sector_options = {
        'National Law Review': natlaw_urls,
        'JD Supra': jdsupra_urls
        }
    # determine which summaries sectors to give options for

    # sources = pickle.loads(current_user.summaries_sources)
    # for source in sources:
    #     if source == 'nat_law_review':
    #         sector_options.update({'National Law Review': natlaw_urls})

    #     elif source == 'jdsupra':
    #         sector_options.update({'JD Supra': jdsupra_urls})

    ################################## Generate Dashboard ######################################################

    print('Dashboard Ready!')

    # add finished dashboard to database
    dash = Dashboard(
    company_name=companyObject.companyName,
    display_name=companyObject.displayName,
    author=current_user
    )
    db.session.add(dash)
    db.session.commit()

    return render_template('dashboard.html',
    ticker=companyObject.ticker,
    displayName=companyObject.displayName,

    # stocks
    stockInfo=stockInfo,

    # bokeh
    script=script,

    # customize summaries form
    sector_options=sector_options
    )
