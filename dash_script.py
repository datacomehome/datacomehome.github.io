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

##### UDF's #####

def get_ranking(player_name, player_info):
    #Find any ranked player's ranking, return zero for unranked
    ranking = player_info[player_name]['rankings'].get('SSBMRank', 0)

    return ranking

def find_2way_interactions(player_name, wins, losses):
    # Only returns interactions for which both players have won
    # and lost to one another
    interaction_set = set([k for k,v in wins.items()]) & \
                        set([k for k,v in losses.items()])

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
plot_data = list()
interaction_data = list()
interaction_names = list()

for p in top100:
    # add neutral lines
    for loss in [
        match for match in lossgraph[p] if match in top100
        and players[match].get('latlon') is not None
        and players[p].get('latlon') is not None
    ]:
        plot_data.append(
            dict(
                type='scattergeo',
                mode='lines+markers',
                text=[p, loss],
                hoverinfo='text',
                lat=[
                    players[p]['latlon'][0] + players[p]['offset'][0],
                    players[loss]['latlon'][0] + players[loss]['offset'][0]
                ],
                lon=[
                    players[p]['latlon'][1] + players[p]['offset'][1],
                    players[loss]['latlon'][1] + players[loss]['offset'][1]
                ],
                line=dict(
                    width = 1,
                    color='rgba(68, 68, 200, 0.05)'
                ),
                marker=dict(
                    size=3,
                    color='rgb(107,107,200)',
                    opacity=1
                )
            )
        )
    # add green lines
    for loss in [
        match for match in lossgraph[p] if match in top100
        and players[match].get('latlon') is not None
        and players[p].get('latlon') is not None
    ]:
        plot_data.append(
            dict(
                type='scattergeo',
                mode='lines+markers',
                text=[p, loss],
                hoverinfo='text',
                lat=[
                    players[p]['latlon'][0] + players[p]['offset'][0],
                    players[loss]['latlon'][0] + players[loss]['offset'][0]
                ],
                lon=[
                    players[p]['latlon'][1] + players[p]['offset'][1],
                    players[loss]['latlon'][1] + players[loss]['offset'][1]
                ],
                line=dict(
                    width = 1,
                    color='rgba(68, 200, 68, 0.3)'
                ),
                marker=dict(
                    size=3,
                    color='rgb(107,107,200)',
                    opacity=1
                ),
                visible=False
            )
        )
    # add red lines
    for win in [
        match for match in wingraph[p] if match in top100
        and players[match].get('latlon') is not None
        and players[p].get('latlon') is not None
    ]:
        plot_data.append(
            dict(
                type='scattergeo',
                mode='lines+markers',
                text=[p, loss],
                hoverinfo='text',
                lat=[
                    players[p]['latlon'][0] + players[p]['offset'][0],
                    players[win]['latlon'][0] + players[win]['offset'][0]
                ],
                lon=[
                    players[p]['latlon'][1] + players[p]['offset'][1],
                    players[win]['latlon'][1] + players[win]['offset'][1]
                ],
                line=dict(
                    width = 1,
                    color='rgba(200, 68, 68, 0.3)'
                ),
                marker=dict(
                    size=3,
                    color='rgb(107,107,200)',
                    opacity=1
                ),
                visible=False
            )
        )
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
        'orientation': 'h',
        'marker':{
            'color': 'rgba(68, 200, 68, 0.8)'
        }
    };
    losses = {
        'y': names,
        'x': loss_heights,
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

# Create boolean vectors for filtering map
filters = {
    'All': [
        True if p['line']['color'] == 'rgba(68, 68, 200, 0.05)'
        else False for p in plot_data
    ]
}
for i in range(len(playerDF2)):
    player_info = playerDF2.loc[i, :]
    name, latitude, longitude = (x for x in list(player_info))
    filtered_lines = [True if latitude == x['lat'][1] and longitude == x['lon'][1]
                      and x['line']['color'] != 'rgba(68, 68, 200, 0.05)'
                      else False for x in plot_data]
    filters[name] = filtered_lines

# Create default layouts for all plots
layout = dict(
    title = '<b>Super Smash Bros. Melee Tournament Matches (2017)</b><br><i>SSBMRank Top 100</i>',
    showlegend=False,
    geo = dict(
        scope='world',
        showlakes=True,
        lakecolor = 'rgb(200, 200, 200)',
        showsubunits=True,
        showcountries=True,
        projection=dict(type='robinson'),
        showland = True,
        landcolor = 'rgb(243, 243, 243)',
        countrycolor = 'rgb(204, 204, 204)',
        subunitcolor='rgb(0, 0, 0)',
    ),
    # paper_bgcolor='rgb(255, 255, 255)',
    plot_bgcolor='rgb(240, 240, 240)'
)

interaction_layout = {
  'yaxis': {
    'dtick': 1,
    'showgrid': False,
    'zeroline': False,
    'showticklabels': False,
    },
  'xaxis': {
    'showgrid': False,
    'zeroline': False,
    'showticklabels': False,
    },
  'barmode': 'relative',
  'title': '<b>Please select a player from the dropdown menu to see interactions</b>',
  # 'paper_bgcolor':'rgb(240, 240, 240)',
  # 'plot_bgcolor':'rgb(240, 240, 240)',
  'margin':dict(l=100)
}

# Initialize the figures for the plots
fig = dict(data=plot_data, layout=layout)
fig2 = dict(data=interaction_data, layout=interaction_layout)

##### DASHBOARD #####

app = dash.Dash()
server = app.server
app.layout = html.Div(
    [
        html.Div([
            html.Img(
                 id='player-img',
                 width='100%',
                 # height='100vh',
                 style={
                     # 'padding-right': '10px',
                     'visibility': 'hidden',
                     # 'right': 30,
                     'position': 'fixed',
                     'align': 'center'
                 }
             ),
                html.Div([
                dcc.Dropdown(
                    id='player-dropdown',
                    options=
                        [
                            {'value':f, 'label':f}
                            for f in sorted(
                                filters.keys(),
                                key=lambda x:players[x]['rankings']['SSBMRank']
                                if x != 'All' else 0
                            )
                        ],
                    value='All',
                    placeholder='Select a player',
                    clearable=False,
                )],
                style={
                    'padding-top':'50px'
                }
            )
            ],
            style={
                'width': '13%',
                'vertical-align': 'top',
                'padding-top': '70px',
                'font-family': 'sans-serif',
                'position': 'fixed',
                'top': 0,
                'right': 40
            }
        ),
        html.Div(
            html.Div(
                [
                    dcc.Graph(id='playermap', style={'width': '80vw', 'height': '80vh'}, figure=fig),
                    dcc.Graph(id='interaction', style={'width': '80vw', 'height': '80vh'}, figure=fig2)
                ]
            ),
            style={'width': '80%'},
            id='output'
        )
    ],
    style={'background-color': 'rgba(29,128,159,.9)'}
)


# callback for image visibility
@app.callback(
    dash.dependencies.Output('player-img', 'style'),
    [dash.dependencies.Input('player-dropdown', 'value')]
)
def inset_image(player):
    if player == 'All':
        return {'visibility':'hidden'}
    elif players[player]['image'] is None:
        return {'visibility':'hidden'}
    else:
        return {'visibility':'visible'}


# callback for image url
@app.callback(
    dash.dependencies.Output('player-img', 'src'),
    [dash.dependencies.Input('player-dropdown', 'value')]
)
def inset_image(player):
    if player != 'All':
        return players[player]['image'].get('url')
    else:
        return


# Callback for the scattergeo
@app.callback(
    dash.dependencies.Output('playermap', 'figure'),
    [dash.dependencies.Input('player-dropdown', 'value')]
    )
def update_figure(player):
    # Set up lines
    showlines = filters[player]
    filtered_data = [p for i, p in enumerate(plot_data) if showlines[i]]
    for datum in filtered_data:
        datum['visible'] = True

    # Set up layout
    new_layout = dict(layout)
    if player != 'All':
        new_layout['title'] = '<b>2017 Tournament Matches for %s</b>' % player

    # Update graph
    return {
        'data': filtered_data,
        'layout': new_layout
    }

# Callback for the player interaction graph
@app.callback(
    dash.dependencies.Output('interaction', 'figure'),
    [dash.dependencies.Input('player-dropdown', 'value')]
    )
def update_figure_2(player):
    # Collect only data for matching player name
    if player != 'All':
        filtered_data = [interaction_data[i] for i,p in enumerate(interaction_names) if p == player][0]
        # Set up layout
        new_layout = {
            'yaxis':{
                'dtick': 1,
            },
            'barmode': 'relative',
            # 'paper_bgcolor':'rgb(240, 240, 240)',
            # 'plot_bgcolor':'rgb(256, 256, 256)',
            'title': '<b>Ranked Player Interactions for %s</b>' % player,
            'showlegend': False,
            'margin':dict(l=120),
        }

        # Update graph
        return {
            'data': filtered_data,
            'layout': new_layout,
        }
    else:
        # Return the default, no graph
        return {
            'data': interaction_data,
            'layout': interaction_layout
        }


if __name__ == '__main__':
    app.run_server(debug=False, host="0.0.0.0")
