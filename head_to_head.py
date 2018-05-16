##### IMPORTS #####
import json
import numpy as np
import pandas as pd
import plotly
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go

##### DATA LOADING #####

with open('data/players.json') as file:
    players = json.load(file)
with open('data/citystates.json') as file:
    cs_geo = json.load(file)
with open('data/2017_lossgraph.json') as file:
    lossgraph = json.load(file)
with open('data/2017_wingraph.json') as file:
    wingraph = json.load(file)

##### UDFs #####

def get_ranking(player_name, player_info):
    #Find any ranked player's ranking, return zero for unranked
    ranking = player_info[player_name]['rankings'].get('SSBMRank', 0)

    return ranking

def find_2way_interactions(player_name, wins=wingraph, losses=lossgraph):
    # Only returns interactions for which both players have won
    # and lost to one another
    interaction_set = set([k for k,v in wins[player_name].items()]) | \
                        set([k for k,v in losses[player_name].items()])

    return interaction_set

##### PREPROCESSING #####

# Add jitter to each player's lat lon coordinates
for p in players:
    isnorcal = issocal = False
    if players[p]['citystate'] is None and players[p]['region'] == 'NorCal':
        isnorcal = True
    elif players[p]['citystate'] is None and players[p]['region'] == 'SoCal':
        issocal = True

    players[p]['offset'] = (
        np.random.normal(scale=0.2) + isnorcal - issocal,
        np.random.normal(scale=0.2) - isnorcal
    )

# Make a data frame for players and their coordinates
playerDF2 = pd.DataFrame(
    columns=['tag', 'lat', 'lon']
)

top100 = sorted(
    [p for p in players if players[p]['rankings'].get('SSBMRank') is not None],
    key=lambda x: players[x]['rankings']['SSBMRank']
)

for i, p in enumerate(top100):
    latlon = players[p].get('latlon')
    if latlon is not None:
        playerDF2.loc[i, ['tag', 'lat', 'lon']] = (
            p,
            latlon[0] + players[p]['offset'][0],
            latlon[1] + players[p]['offset'][1]
        )
playerDF2.reset_index(drop=True, inplace=True)

# Lines
interaction_data = list()
interaction_names = list()
interaction_layout = dict()

for p in top100:
    # Add interaction plot data
    wins, losses = (wingraph[p], lossgraph[p])
    names = set([name for name in wins.keys()]) | set([name for name in losses.keys()])

    interactions = dict()
    for name in names:
        ranking = get_ranking(name, players)
        if ranking > 0:
            interactions[name] = (wins.get(name, 0), losses.get(name, 0), ranking)

    sorted_interactions = sorted(list(interactions.items()), key=lambda x: x[1][2], reverse=True)

    names = [x[0] for x in sorted_interactions]
    win_heights = [x[1][0] for x in sorted_interactions]
    loss_heights = [-x[1][1] for x in sorted_interactions]

    wins = {
        'y': names,
        'x': win_heights,
        'name': 'wins',
        'type': 'bar',
        'width': 0.8,
        'orientation': 'h',
        'marker':{
            'color': 'rgba(68, 200, 68, 0.8)'
        }
    };
    losses = {
        'y': names,
        'x': loss_heights,
        'width': 0.8,
        'name': 'losses',
        'type': 'bar',
        'orientation': 'h',
        'marker':{
            'color': 'rgba(200, 68, 68, 0.8)'
        }
    };

    interaction_data.append([wins, losses]);
    interaction_names.append(p)

## End of player loop ##


# Initialize the figures for the plots
sfig = plotly.tools.make_subplots(rows=1, cols=2, print_grid=False)

##### DASHBOARD #####

app = dash.Dash()
server = app.server
app.layout = html.Div(
    [html.Div([
        html.Div(
            [html.H1('Player Comparison')],
            style={
                'width':'100%',
                'display': 'inline-block',
                'color': 'rgba(236,184,7)'
            }
        ),
        html.Div(
            [],
            style={
                'width':'15%',
                'display': 'inline-block'
            }
        ),
        html.Div([
            html.Img(
                 id='p1-img',
                 width='130px',
                 height='130px',
                 style={
                     'visibility': 'hidden',
                     'margin-left': 'auto',
                     'margin-right': 'auto',
                     'horizontal-align': 'center'
                 }
            ),
            dcc.Dropdown(
                id='p1-dropdown',
                options=[{'value':f, 'label':f} for f in top100],
                value='Mang0',
                placeholder='Select a player',
                clearable=False
            )],
            style={
                'width':'20%',
                'display':'inline-block'
            }),

            html.Div([
                html.H2([
                    html.Br(), html.Br(),
                    html.B('2017 Head to Head:'),
                    html.Br(),
                    html.P('', id='h2h')])
            ], style={
                'width':'29%',
                'display':'inline-block',
                'text-align':'center',
                'vertical-align':'center',
                'font-weight':700,
                'color':'rgba(255,255,255,0.9)'
            }),

            html.Div([
                html.Img(
                    id='p2-img',
                    width='130px',
                    height='130px',
                    style={
                        'visibility': 'hidden',
                        'display': 'block',
                        'margin-left': 'auto',
                        'margin-right': 'auto',
                    }
                ),
                dcc.Dropdown(
                    id='p2-dropdown',
                    options=
                        [
                            {'value':f, 'label':f}
                            for f in top100
                        ],
                    value='Armada',
                    placeholder='Select a player',
                    clearable=False
                )],
                style={
                    'width':'20%',
                    'display':'inline-block',
                    'vertical-align':'center'
                }
            ),
        html.Div(
            [],
            style={
                'width':'15%',
                'display': 'inline-block'
            }
        )
    ],
        style={
            'width': '100%',
            'vertical-align': 'top',
            'padding-top': '70px',
            'font-family': 'sans-serif',
            'text-align': 'center'
        }
    ),
     html.Div([], style={'width':'100%', "height":'15px'}),
     html.Div(
        html.Div(
            [dcc.Graph(id='interaction', figure=sfig)]
        ),
        style={'width': '100%'},
        id='output'
    )],
    style={'background-color': 'rgba(29, 128, 159, 0.9)'}
)

# h2h callback
@app.callback(
    dash.dependencies.Output('h2h', 'children'),
    [dash.dependencies.Input('p1-dropdown', 'value'),
     dash.dependencies.Input('p2-dropdown', 'value')]
)
def update_h2h(p1, p2):
    return ' - '.join(
        [str(wingraph[p1][p2]) if p2 in wingraph[p1] else '0',
         str(wingraph[p2][p1]) if p1 in wingraph[p2] else '0']
    )


# callback for image visibility
@app.callback(
    dash.dependencies.Output('p2-img', 'style'),
    [dash.dependencies.Input('p2-dropdown', 'value')]
)
def inset_image2(player):
    if players[player]['image'] is None:
        return {'visibility':'hidden'}
    else:
        return {'visibility':'visible'}


# callback for image url
@app.callback(
    dash.dependencies.Output('p2-img', 'src'),
    [dash.dependencies.Input('p2-dropdown', 'value')]
)
def inset_image2(player):
    return players[player]['image'].get('url')


# callback for image visibility
@app.callback(
    dash.dependencies.Output('p1-img', 'style'),
    [dash.dependencies.Input('p1-dropdown', 'value')]
)
def inset_image(player):
    if players[player]['image'] is None:
        return {'visibility':'hidden'}
    else:
        return {'visibility':'visible'}


# callback for image url
@app.callback(
    dash.dependencies.Output('p1-img', 'src'),
    [dash.dependencies.Input('p1-dropdown', 'value')]
)
def inset_image(player):
    return players[player]['image'].get('url')


# Callback for the player interaction graph
@app.callback(
    dash.dependencies.Output('interaction', 'figure'),
    [dash.dependencies.Input('p1-dropdown', 'value'),
     dash.dependencies.Input('p2-dropdown', 'value')]
    )
def update_figure(player1, player2):
    cross_int = [
        p for p in find_2way_interactions(player1) & \
            find_2way_interactions(player2)
        if p in top100
    ]

    # Collect only data for matching player name
    p1_data = [
        i.copy() for i in
        interaction_data[interaction_names.index(player1)]
    ]

    p1_xwin = []
    p1_xloss = []
    p1_y = []

    for xw, xl, y in zip(p1_data[0]['x'], p1_data[1]['x'], p1_data[0]['y']):
        if y in cross_int:
            p1_xwin.append(xw)
            p1_xloss.append(xl)
            p1_y.append(y)

    p1_data[0]['x'], p1_data[1]['x'],\
        p1_data[0]['y'], p1_data[1]['y'] = p1_xwin, p1_xloss, p1_y, p1_y

    p2_data = [
        i.copy() for i in
        interaction_data[interaction_names.index(player2)]
    ]

    p2_xwin = []
    p2_xloss = []
    p2_y = []

    for xw, xl, y in zip(p2_data[0]['x'], p2_data[1]['x'], p2_data[0]['y']):
        if y in cross_int:
            p2_xwin.append(xw)
            p2_xloss.append(xl)
            p2_y.append(y)

    p2_data[0]['x'], p2_data[1]['x'], \
        p2_data[0]['y'], p2_data[1]['y'] = p2_xwin, p2_xloss, p2_y, p2_y

    # Set up layout
    new_layout = {
      'barmode': 'relative',
      'autosize': True,
      'width':1000,
      'paper_bgcolor':'rgb(240, 240, 240)',
      'plot_bgcolor':'rgb(256, 256, 256)',
      'title': '<b>Ranked Player Interactions for %s and %s</b>' % (player1, player2),
      'showlegend': False,
      'margin':dict(l=120),
    }

    sfig = plotly.tools.make_subplots(rows=1, cols=2, print_grid=False)
    sfig.append_trace(
        p1_data[0], 1, 1
    )
    sfig.append_trace(
        p1_data[1], 1, 1
    )
    sfig.append_trace(
        p2_data[0], 1, 2
    )
    sfig.append_trace(
        p2_data[1], 1, 2
    )
    sfig.layout.update(
        {'barmode':'relative',
         'showlegend':False,
         'title':'Record Comparison',
         'hoverlabel':dict(
             bgcolor='black',
             font={'color': 'white'}
         ),
         'margin':{
             'l':130,
             'r':130
         },
         'yaxis':{
             'dtick':1
         },
         'yaxis2':{
             'dtick':1,
             'side':'right'
         }
        }
    )

    # Update graph
    return sfig


if __name__ == '__main__':
    app.run_server(debug=False, host="0.0.0.0")
