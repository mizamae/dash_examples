from asammdf import MDF
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash_bootstrap_components as dbc
from plotly_resampler import register_plotly_resampler, FigureResampler, FigureWidgetResampler
import json
import pickle
import os
import io
import uuid
from dash import Dash, ctx, dcc, html, Input, Output, State, callback, ALL, MATCH
from dash.exceptions import PreventUpdate
import base64
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
__APP_ID__ = "mdf4"

_MAX_SAMPLES_ = 50000

__sidebar_width__ = 20 # width in %
__SIDEBAR_STYLE__ = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": str(__sidebar_width__)+"%",
    "padding": "2rem 1rem",
    "backgroundColor": "#f8f9fa",
    "overflow": "scroll",
}

__CONTENT_STYLE__ = {
    "marginLeft": str(__sidebar_width__+2) + "%",
    "marginRight": "2rem",
    "padding": "2rem 1rem",
}

fig1 = go.Figure()

fig1.update_layout(
    margin=dict(l=20, r=20, t=20, b=20),
)

__CONTENT_CHILDREN__=[
                        html.Div([
                            dcc.Upload(
                                id='upload-data'+__APP_ID__,
                                children=html.Div([
                                    'Drag and Drop or ',
                                    html.A('Select Files')
                                ]),
                                style={
                                    'width': '100%',
                                    'height': '180px',
                                    'lineHeight': '60px',
                                    'borderWidth': '1px',
                                    'borderStyle': 'dashed',
                                    'borderRadius': '5px',
                                    'textAlign': 'center',
                                    'margin': '10px'
                                },
                                # Allow multiple files to be uploaded
                                multiple=False
                            ),
                        ],id="upload"+__APP_ID__+"_div"
                        ),
                        dcc.Graph(id="plots1",figure=fig1,style={'height': '60rem'},),
]

__SIDEBAR_MENU_CHILDREN__=[html.Div([
            dcc.Store(id="intermediate-value"+__APP_ID__),            
        ],className="row",
    )]

@app.callback([
                Output("sidebar-content","children"),
                #Output("page-content", "children", allow_duplicate=True),
                Output("upload"+__APP_ID__+"_div", 'style'),
                Output("intermediate-value"+__APP_ID__, 'data', allow_duplicate=True),
                ],
              Input('upload-data'+__APP_ID__, 'contents'),
              State('upload-data'+__APP_ID__, 'filename'),
              prevent_initial_call=True
              )
def load_file(content,name):
    content_type, content_string = content.split(',')
    decoded = base64.b64decode(content_string)
    mdf = MDF(io.BytesIO(decoded))

    filename= "file"+str(uuid.uuid4())+".dat"
    with open(filename,"wb") as file:
        file.write(decoded)

    __SIDEBAR_MENU_CHILDREN__[0].children.append(html.Div([html.H5("Signal"),],className="col-6"))
    __SIDEBAR_MENU_CHILDREN__[0].children.append(html.Div([html.H5("Plot"), ],className="col-2 text-center"))
            
    #register_plotly_resampler(mode='auto',default_n_shown_samples=1500)
    signals=[]
    for group_index,group in enumerate(mdf.groups):
        print("Group " + str(group_index))
        #fig = make_subplots(rows=1, cols=1,shared_xaxes=False,)
        group_type = group.channel_group.comment.lower()
        if group_type == "time based":
            #dynamic_fig = FigureResampler(go.Figure(),default_n_shown_samples=_MAX_SAMPLES_)
            filtered = mdf.filter([[channel.name,group_index] for channel in group.channels])
            for key in filtered.channels_db:
                for gp_nr, ch_nr in filtered.channels_db[key]:
                    data=filtered.get(group=gp_nr, index=ch_nr,record_offset=0,record_count=None)
                    resolution = (max(data.timestamps)-min(data.timestamps))/(len(data.samples)-1)
                    signals.append({'group_index':group_index,'group_number':gp_nr,'channel_index':ch_nr,
                                    'name':data.name,'units':data.unit,
                                    'resolution':resolution,'samples':len(data.samples)-1})
    with open("signals.json","w") as file:
        json.dump(signals,file,indent=4)
    
    for i,channel in enumerate(signals):
        channelName=channel["name"]
        __CHANNEL_DISPLAY__ = html.Div([
                html.Div([html.P(channelName),],className="col-6"),
                html.Div([
                    dbc.ButtonGroup([
                        dbc.Button('1', id={"type": "btnplot1", "index": i}, n_clicks=0,size="sm",color="light"),
                        dbc.Button('2', id={"type": "btnplot2", "index": i}, n_clicks=0,size="sm",color="light"),
                        dbc.Button('3', id={"type": "btnplot3", "index": i}, n_clicks=0,size="sm",color="light"),
                        ])
                    ],className="col-2"),
                
            ],className="row",
        )

        __SIDEBAR_MENU_CHILDREN__.append(__CHANNEL_DISPLAY__)
            
    return (__SIDEBAR_MENU_CHILDREN__, {'display': 'none'},json.dumps({"signals":signals,"filename":filename}))
    
@callback(
        [
            Output({"type": "btnplot1", "index": ALL}, "color"),
            Output("plots1", "figure", allow_duplicate=True),
            Output("intermediate-value"+__APP_ID__, 'data', allow_duplicate=True),
        ],
        Input({"type": "btnplot1", "index": ALL}, "n_clicks"),
        [
            State('plots1', 'figure'),
            State({"type": "btnplot1", "index": ALL}, "color"),
            State("intermediate-value"+__APP_ID__, 'data'),
        ],
        prevent_initial_call=True,
        )
def display_plot1(btn1,fig_state,btn_state,data_state):
    fig = FigureResampler(go.Figure(**fig_state),default_n_shown_samples=_MAX_SAMPLES_)
    button_clicked = ctx.triggered_id
    var_index = button_clicked['index']
    
    if not data_state or btn1[var_index]==0:
        raise PreventUpdate
    else:
        data_state = json.loads(data_state)
    

    with open(data_state['filename'],"rb") as file:
        decoded=file.read()

    mdf = MDF(io.BytesIO(decoded))

    if not "fig1" in data_state:
        data_state["fig1"]={"xini":0,"xend":None,"signals":[]}

    filtered = mdf.filter([(data_state['signals'][var_index]["name"],data_state['signals'][var_index]["group_index"])])

    offset = 0 if not data_state["fig1"]["xini"] else int(data_state["fig1"]["xini"]/data_state['signals'][var_index]["resolution"])
    record_count = None if not data_state["fig1"]["xend"] else int((data_state["fig1"]["xend"]-data_state["fig1"]["xini"])/data_state['signals'][var_index]["resolution"])

    data=filtered.get(group=0, index=1,record_offset=offset,record_count=record_count)

    if btn1[var_index]%2!=0:   # request to add signal to figure
        fig.add_trace(go.Scattergl(showlegend=True,name=data.name + "[" +data.unit+"]"), hf_x=data.timestamps, hf_y=data.samples)
        data_state["fig1"]["signals"].append({"name":data_state['signals'][var_index]["name"],
                                              "group_index":data_state['signals'][var_index]["group_index"],
                                              "resolution":data_state['signals'][var_index]["resolution"]
                                              })
        btn_state[var_index]="primary"
    else:# request to remove signal from fig
        for i, trace in enumerate(fig_state['data']):
            if 'name' in trace and data.name + "[" +data.unit+"]" in trace['name']:
                fig_state['data'][i].clear()
                data_state["fig1"]["signals"].remove({"name":data_state['signals'][var_index]["name"],
                                                      "group_index":data_state['signals'][var_index]["group_index"],
                                                      "resolution":data_state['signals'][var_index]["resolution"]
                                                      })
                break
        fig = FigureResampler(go.Figure(**fig_state),default_n_shown_samples=_MAX_SAMPLES_)
        btn_state[var_index]="light"
    
    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
    )
    
    return btn_state,fig,json.dumps(data_state)

# Callback to get the zoommed limits in a graph called basic-interactions
@callback(
    [
        Output("plots1","figure", allow_duplicate=True),
        Output("intermediate-value"+__APP_ID__, 'data', allow_duplicate=True),
    ],
    Input('plots1', 'relayoutData'),
    [
        State('plots1', 'figure'),
        State("intermediate-value"+__APP_ID__, 'data'),
    ],
    prevent_initial_call=True,
    )
def display_relayout_data(relayoutData,fig_state,data_state):
    try:
        xini = relayoutData["xaxis.range[0]"]
        xend = relayoutData["xaxis.range[1]"]
    except:
        raise PreventUpdate
    fig = FigureResampler(go.Figure(),default_n_shown_samples=_MAX_SAMPLES_)
    data_state = json.loads(data_state)
    signals = data_state["fig1"]["signals"]
    data_state["fig1"]["xini"]=xini
    data_state["fig1"]["xend"]=xend
    with open(data_state['filename'],"rb") as file:
        decoded=file.read()

    mdf = MDF(io.BytesIO(decoded))

    for signal in signals:
        filtered = mdf.filter([(signal["name"],signal["group_index"])])
        #data=filtered.get(group=0, index=1,record_offset=100,record_count=_MAX_SAMPLES_)
        offset = 0 if not data_state["fig1"]["xini"] else int(data_state["fig1"]["xini"]/signal["resolution"])
        record_count = None if not data_state["fig1"]["xend"] else int((data_state["fig1"]["xend"]-data_state["fig1"]["xini"])/signal["resolution"])
        data=filtered.get(group=0, index=1,record_offset=offset,record_count=record_count)
        fig.add_trace(go.Scattergl(showlegend=True,name=data.name + "[" +data.unit+"]"), hf_x=data.timestamps, hf_y=data.samples)
    
    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
    )
    return (fig,json.dumps(data_state))




app.layout = html.Div([
    
    html.Div(__SIDEBAR_MENU_CHILDREN__,className="col-2",id="sidebar-content"),
    html.Div(__CONTENT_CHILDREN__,className="col-10",id="page-content"),
    
], className="row")

if __name__ == '__main__':
    app.run(debug=True)