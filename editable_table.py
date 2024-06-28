from dash import Dash, dash_table, dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import pandas as pd
import json
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
from io import StringIO
from scipy import signal

app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

speed_values=[0,103,206,309,412,515,618,721,824,927,1030,1133,1236,1339,1442,1545,1648,1751,1854,1957,2060,2163,2266,2369,2472,2575,2678,2781,2884,2987,3090,3193,3296,3399,3502,3605,3708,3811,3914,4017,4120,4223,4326,4429,4532,4635,4738,4841,4944,5047,5150,5253,5356,5459,5562,5665,5768,5871,5974,6077,6180,6283,6386,6489]
columns = (
            [{'id': 'Torque', 'name': 'Torque','type': 'numeric'}] +
            [{'id': str(speed), 'name': str(speed),'type': 'numeric'} for speed in speed_values]
        )
torque_vect=[0,4,8,12,16,20,24,28,32,36,40,44,48,52,56,60,64,68,72,76,80,84,88,92,96,100,104,108,112,116,120,124,128,132,136,140,144,148,152,156,160,164,168,172,176,180,184,188,192,196,200,204,208,212,216,220,224,228,232,236,240,244,248,252]
initial_torques=[{"Torque":torque} for torque in torque_vect]
initial_speeds={"Bins":"Speed values"}
torque_speed={"Bins":"Max Torque values"}
for i in range(64):
    initial_speeds[i] = None
    
__FIRSTROW_HEIGHT__ = 5000

def discrete_background_color_bins(df, df_speedLimit, n_bins=9, columns='all'):
    import colorlover
    bounds = [i * (1.0 / n_bins) for i in range(n_bins + 1)]
    if columns == 'all':
        if 'id' in df:
            df_numeric_columns = df.select_dtypes('number').drop(['id'], axis=1)
        else:
            df_numeric_columns = df.select_dtypes('number')
    else:
        df_numeric_columns = df[columns]
    df_max = df_numeric_columns.max().max()
    df_min = df_numeric_columns.min().min()
    ranges = [
        ((df_max - df_min) * i) + df_min
        for i in bounds
    ]
    styles = []
    legend = []
    for i in range(1, len(bounds)):
        min_bound = ranges[i - 1]
        max_bound = ranges[i]
        backgroundColor = colorlover.scales[str(n_bins)]['seq']['Blues'][i - 1]
        color = 'white' if i > len(bounds) / 2. else 'inherit'

        for column in df_numeric_columns:
            styles.append({
                'if': {
                    'filter_query': (
                        '{{{column}}} >= {min_bound}' +
                        (' && {{{column}}} < {max_bound}' if (i < len(bounds) - 1) else '')
                    ).format(column=column, min_bound=min_bound, max_bound=max_bound),
                    'column_id': column
                },
                'backgroundColor': backgroundColor,
                'color': color
            })
            # this is tooo slow
            # for k,row in enumerate(df[column].index.values):
            #     styles.append({
            #     'if': {
            #         'filter_query': str(row)+' > ' + str(df_speedLimit.iloc[1,k+1]),
            #     },
            #     'backgroundColor': 'grey',
            #     'color': color
            # })
        legend.append(
            html.Div(style={'display': 'inline-block', 'width': '60px'}, children=[
                html.Div(
                    style={
                        'backgroundColor': backgroundColor,
                        'borderLeft': '1px rgb(50, 50, 50) solid',
                        'height': '10px'
                    }
                ),
                html.Small(round(min_bound, 2), style={'paddingLeft': '2px'})
            ])
        )

    return (styles, html.Div(legend, style={'padding': '5px 0 5px 0'}))


        
app.layout = html.Div([
    dcc.Store(id="maintable_data"),    
    dcc.Store(id="torquespeedlimittable_data"),    
    dbc.Row(
            [
                dbc.Col(
                    [
                        dash_table.DataTable(
                            id='speed-editing-simple',
                            columns=(
                                [{'id': 'Bins', 'name': 'Bins','type': 'text'}] +
                                [{'id': str(i), 'name': str(i),'type': 'numeric'} for i in range(64)]
                            ),
                            data=[initial_speeds,torque_speed],
                            editable=True,
                            fill_width=True,
                            style_table={'overflowX': 'scroll','overflowY': 'scroll'},
                            merge_duplicate_headers=True
                        ),
                        
                        dbc.Row(
                            [

                                html.Div(
                                        [
                                            dbc.Button("+", id="btn_incr_offset", color="primary", n_clicks=0,className='col-12',disabled=True),
                                        ],
                                        className="col-4", 
                                ),
                                html.Div(
                                        [
                                            dbc.Button("-", id="btn_decr_offset", color="primary", n_clicks=0,className='col-12',disabled=True),
                                        ],
                                        className="col-4", 
                                ),
                                html.Div(
                                        [
                                            dbc.Button("Reset selection", id="btn_deselect", color="primary", n_clicks=0,className='col-12',disabled=True),
                                        ],
                                        className="col-4", 
                                ),

                            ],
                            style = {'display': 'none'},
                            id="btn_selection_row", 
                        ),
                        
                        dash_table.DataTable(
                            id='table-editing-simple',
                            columns=columns,
                            data=initial_torques,

                            #filter_action='native',
                            editable=True,
                            #row_selectable="multi",
                            #column_selectable="multi",
                            selected_rows=[],
                            export_format='xlsx',
                            export_headers='display',
                            fill_width=True,
                            style_table={'overflowX': 'scroll','overflowY': 'scroll'},
                            merge_duplicate_headers=True
                        ),
                    ],
                    width=8,
                ),
                dbc.Col(dcc.Graph(id='3Dplot',figure={}),width=4),
            ],
            style={
                    'maxHeight': str(__FIRSTROW_HEIGHT__)+'px',
                    'overflow': 'auto'
                },
            
        ),
    dbc.Row(
            [dcc.Graph(id='IsoTplot',figure={}),]
        ),
    dbc.Row(
            [dcc.Graph(id='IsoWplot',figure={}),]
        ),
])

@callback(
    [
        Output('table-editing-simple', 'columns'),
        Output("torquespeedlimittable_data", 'data'),
    ],
    [Input('speed-editing-simple', 'data'),],
    [
        State('speed-editing-simple', 'columns'),
    ],
    prevent_initial_call=True,
    )
def update_speedValues(rows, columns):
    df = pd.DataFrame(rows, columns=[c['name'] for c in columns])
    if not df.isnull().values.any():
        cols = (
                [{'id': 'Torque', 'name': 'Torque','type': 'numeric'}] +
                [{'id': str(speed), 'name': str(speed),'type': 'numeric'} for speed in df.values[0][1:]]
            )
        return (cols,df.to_json())
    else:
        raise PreventUpdate


@callback(
    [
        Output('3Dplot', 'figure'),
        Output('IsoTplot', 'figure'),
        Output('IsoWplot', 'figure'),
        Output('table-editing-simple', 'style_data_conditional'),
        Output("maintable_data", 'data'),
        Output("btn_selection_row","style")
    ],
    [Input('table-editing-simple', 'data'),],
    [
        State('table-editing-simple', 'columns'),
        State("torquespeedlimittable_data", 'data'),
    ],
    prevent_initial_call=True,
    )
def display_output(rows, columns, torquespeedLimit):
    df = pd.DataFrame(rows, columns=[c['name'] for c in columns])
    df.set_index("Torque",inplace=True)
    fig3D={}
    figIsoT={}
    figIsoW={}
    styles=[{},]
    buttons_row = {'display': 'none'}
    
    # filter 1 z=df.rolling(window=5).mean().values
    try:
        df_speedLimit=pd.read_json(StringIO(torquespeedLimit))
    except:
        df_speedLimit=None
    
    if not df.isnull().values.any():
        fig3D = go.Figure(
            data=[go.Surface(z=df.values, 
                            y=[int(value) for value in df.index.values], 
                            x=[int(value) for value in df.columns[1:]],
                            hovertemplate = 'Speed: %{x:.0f} rpm - Torque: %{y:.0f} Nm - Current: %{z:.0f} A<extra></extra>',
                            colorscale ='Blues',
                            ),
                ]
        )
        # fig3D.add_trace(go.Surface(z=signal.savgol_filter(df.values,53,3), 
        #                     y=[int(value) for value in df.index.values], 
        #                     x=[int(value) for value in df.columns[1:]],
        #                     hovertemplate = 'Speed: %{x:.0f} rpm - Torque: %{y:.0f} Nm<extra></extra>',
        #                     colorscale ='Blues',
        #                     ),
        # )
            
        fig3D.update_traces(showscale=False)
        fig3D.update_layout(title='3D plot',
                        #width=1500, height=1500,
                        autosize=True,
                        margin=dict(l=10, r=10, b=20, t=40))
        fig3D.update_scenes(xaxis_title_text="Speed [rpm]",  
                    yaxis_title_text="Torque [Nm]",  
                    zaxis_title_text='Current [A]')
        
        # plot for constant torque
        figIsoT = go.Figure()
        for torque in df.index.values:
            figIsoT.add_trace(go.Scatter(
                    x=[int(value) for value in df.columns[1:]],
                    y = df.loc[torque].values,
                    mode="lines+markers",
                    name = "T="+str(torque) + "Nm"
                    )
            )
        figIsoT.update_layout(title='Current along isoTorque lines',
                        showlegend=True,
                        xaxis_title="Speed [rpm]",)
        
        # plot for constant speed
        figIsoW = go.Figure()
        temp_df = df.transpose()
        for speed in temp_df.index.values:
            figIsoW.add_trace(go.Scatter(
                    x=[int(value) for value in temp_df.columns[1:]],
                    y = temp_df.loc[speed].values,
                    mode="lines+markers",
                    name = "W="+str(speed) + "rpm"
                    )
            )
        figIsoW.update_layout(title='Current along isoSpeed lines',
                        showlegend=True,
                        xaxis_title="Torque [Nm]",)
        
        (styles, legend) = discrete_background_color_bins(df,df_speedLimit)
        buttons_row = {'display': 'flex'}

    return (fig3D,figIsoT,figIsoW,styles,df.to_json(),buttons_row)

@callback(
    Output('table-editing-simple', 'derived_virtual_selected_row_ids'),
    Input('3Dplot', 'clickData'),
    prevent_initial_call=True,
)
def selectedPointOn3D(points):
    if points:
        point = points['points'][0]
        print(point)
        return [json.dumps({"speed":point['x'],"torque":point['y']}),]
    else:
        return []

# @callback(
#     Output('3Dplot', 'figure',allow_duplicate=True),
#     Input('table-editing-simple', 'selected_cells'),
#     prevent_initial_call=True,
# )
# def enableOffsetButtons(points,):
#     if points:
#         pass
#     else:
#         pass
    
@callback(
    Output('3Dplot', 'figure',allow_duplicate=True),
    Output('btn_incr_offset','disabled'),
    Output('btn_decr_offset','disabled'),
    Output('btn_deselect','disabled'),
    Input('table-editing-simple', 'selected_cells'),
    State("maintable_data", 'data'),
    State("3Dplot", 'figure'),
    prevent_initial_call=True,
)
def selectedPointOnTable(points,data,figuredata):
    if figuredata:
        if len(figuredata['data'])>1: # if there are some points highlighted, remove them
            figuredata['data']=[figuredata['data'][0],]
        fig3D = go.Figure(**figuredata)
    else:
        fig3D = {}
    btn_incr_offset_disabled = True
    btn_decr_offset_disabled = True
    btn_deselect_disabled = True
    
    if points:
        Xcoordinates=[]
        Ycoordinates=[]
        Zcoordinates=[]
        if data:
            df=pd.read_json(StringIO(data))
            
            for point in points:
                try:
                    Xcoordinates.append(int(point["column_id"]))
                    Ycoordinates.append(df.index.values[point["row"]])
                    z=df.loc[df.index.values[point["row"]],int(point["column_id"])]
                    Zcoordinates.append(z+10 if z<0 else z)
                except:
                    pass
            figuredata['data'].append(go.Scatter3d(x=Xcoordinates,
                                                    y=Ycoordinates,
                                                    z=Zcoordinates,
                                                    marker_size = 10,
                                                    mode='markers'),)
            fig3D = go.Figure(**figuredata)
            btn_incr_offset_disabled = False
            btn_decr_offset_disabled = False
            btn_deselect_disabled = False
            return fig3D,btn_incr_offset_disabled,btn_decr_offset_disabled,btn_deselect_disabled
            
        raise PreventUpdate
    else:
        return fig3D,btn_incr_offset_disabled,btn_decr_offset_disabled,btn_deselect_disabled

# This callback highlights in red the point in the table corresponding to the clicked one on the 3D figure
# @callback(
#     Output('table-editing-simple', 'style_data_conditional',allow_duplicate=True),
#     Input('table-editing-simple', 'derived_virtual_selected_row_ids'),
#     State('table-editing-simple', 'style_data_conditional'),
#     prevent_initial_call=True,
# )
# def highlightInTable(selected_rows,style):
    
#     if selected_rows :
#         return style[:-1]+ [{
#             'if': { 'filter_query': '{Torque} = ' +str(json.loads(row)["torque"]),"column_id":str(json.loads(row)["speed"])},
#             'backgroundColor': '#FF0000'
#         } for row in selected_rows]



if __name__ == '__main__':
    app.run(debug=True)