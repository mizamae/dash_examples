from dash import Dash, dash_table, dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
import pandas as pd
import json
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
from io import StringIO
import numpy as np
import math
app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

initial_speeds={"Bins":"Speed values [rpm]"}
initial_torques={"Bins":"Max Torque values [Nm]"}
for i in range(64):
    initial_speeds[i] = None
    initial_torques[i] = None

__APP_ID__ = "speed_degradation"
        
app.layout = html.Div([
    dbc.Row(
        [
            html.Div([html.H3("Set the maximum torque-speed envelope"),],className="col-md-6"),
            dash_table.DataTable(
                                id='speed-editing-simple',
                                columns=(
                                    [{'id': 'Bins', 'name': 'Bins','type': 'text'}] +
                                    [{'id': str(i), 'name': str(i),'type': 'numeric'} for i in range(64)]
                                ),
                                data=[initial_speeds,initial_torques],
                                editable=True,
                                fill_width=True,
                                style_table={'overflowX': 'scroll','overflowY': 'scroll'},
                                merge_duplicate_headers=True
                            ),
        ],
    ),
    html.Hr(),
    dbc.Row(
            [   
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.Div([],className="col-md-2"),
                                html.Div([dbc.Label("Machine pole pairs")],className="col-md-4"),
                                html.Div([dbc.Input(type="number", min=1, step=1, value=2, id="polepairs"+__APP_ID__,)],className="col-md-4"),
                                html.Div([],className="col-md-2"),
                            ],
                            className="row",
                        ),
                        html.Div(
                            [
                                html.Div([],className="col-md-2"),
                                html.Div([dbc.Label("SpeedLim_erpm")],className="col-md-4"),
                                html.Div([dbc.Input(type="number", min=1, step=1, value=2500, id="SpeedLim_erpm"+__APP_ID__,)],className="col-md-4"),
                                html.Div([],className="col-md-2"),
                            ],
                            className="row",
                        ),
                        html.Div(
                            [
                                html.Div([],className="col-md-2"),
                                html.Div([dbc.Label("Overspeed _factor")],className="col-md-4"),
                                html.Div([dbc.Input(type="number", min=1, step=1, value=5, id="Overspeed _factor"+__APP_ID__,)],className="col-md-4"),
                                html.Div([],className="col-md-2"),
                            ],
                            className="row",
                        ),
                    ],
                    width=4,
                ),
                dbc.Col(dcc.Graph(id='torque_plot',figure={}),width=8),
            ],
            
        ),
])

@callback(
    [
        Output('torque_plot', 'figure'),
    ],
    [   
        Input('speed-editing-simple', 'data'),
        State('speed-editing-simple', 'columns'),
        Input("polepairs"+__APP_ID__,"value"),
        Input("SpeedLim_erpm"+__APP_ID__,"value"),
        Input("Overspeed _factor"+__APP_ID__,"value")
    ],
    prevent_initial_call=True,
    )
def update_speedValues(rows, columns, pp, speedLim, ovspeed_fac):
    #del rows['Bins']
    for row in rows:
        del row['Bins']
    df = pd.DataFrame(rows, columns=[c['name'] for c in columns[1:]]) # this is to avoid the "Bins" column
    if not df.isnull().values.any():

        # plot for constant torque
        figTmax = go.Figure()
        df_transposed = df.T
        
        df_transposed[2]=df_transposed[1]*(-np.exp(df_transposed[0]*ovspeed_fac/(speedLim/pp))+np.exp(ovspeed_fac))/np.exp(ovspeed_fac)
        df_transposed[2] = np.where((df_transposed[2]>df_transposed[1]), df_transposed[1], df_transposed[2])
        df_transposed[2] = np.where((df_transposed[2]<0), 0, df_transposed[2])
        figTmax.add_trace(go.Scatter(
                x=[int(value) for value in df_transposed[0]],
                y = [int(value) for value in df_transposed[1]],
                mode="lines+markers",
                name = "Max torque envelope"
                )
        )
        figTmax.add_trace(go.Scatter(
                x=[int(value) for value in df_transposed[0]],
                y = [int(value) for value in df_transposed[2]],
                mode="lines+markers",
                name = "Limited torque envelope"
                )
        )
        figTmax.update_layout(title='Torque vs speed',
                        showlegend=True,
                        height= 800,  # px
                        yaxis_title="Torque [Nm]",
                        xaxis_title="Speed [rpm]",)
        
        return [figTmax,]
    else:
        raise PreventUpdate

if __name__ == '__main__':
    app.run_server(port=8888,debug=True)