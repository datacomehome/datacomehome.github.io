# spencer stanley

import requests
from collections import defaultdict

"""
functions to query data from smash.gg,
including set results and player identifiers,
and then construct a graph of losses from
this info
"""


def get_melee_rankings():
    """get all regional, state, national, and multinational
    rankings for super smash bros melee
    
    output
    ---------
    rankings: dict of {ranking id: ranking name}
    """
    rankings = requests.get(
        'https://api.smash.gg/rankings?per_page=100&\
        filter={%22videogameIds%22:%221%22,%22global%22:true,\
        %22regional%22:%22state%22}'
    ).json()['items']['entities']['rankingSeries']

    rankings += requests.get(
        'https://api.smash.gg/rankings?expand[]=players&per_page=100&\
        filter={%22videogameIds%22:%221%22,%22regional%22:%22country%22}'
    ).json()['items']['entities']['rankingSeries']

    rankings += requests.get(
        'https://api.smash.gg/rankings?expand[]=players&per_page=100&\
        filter={%22videogameIds%22:%221%22,%22regional%22:%22subState%22}'
    ).json()['items']['entities']['rankingSeries']
    
    rankings = {
        r['id']:r['name'] for r in rankings
    }
    
    return rankings


def get_sgg_phases(tournaments):
    """return list of json objects containing
    phase data for each given smash.gg tournament URL
    by querying the sgg API for each phase
    
    input
    ---------
    tournaments: list of json blobs (requests.get().json)
    for smashgg tournament & event:
    e.g., for tournament t and event e at that tournament,
    http://api.smash.gg/tournament/t/event/e?expand[]=groups
    """
    # get IDs of phase groups to query
    ids = []
    for tournament in tournaments:
        for phase_group in tournament['entities']['groups']:
            ids.append(phase_group['id'])

    # query smashgg API for each phase group
    phases = []
    base_url = 'http://api.smash.gg/phase_group/%s\
                ?expand[]=sets&expand[]=seeds'
    for pg_id in ids:
        phases.append(
            requests.get(base_url % pg_id).json()  # append json objects
        )

    return phases


def get_sgg_players(phases, rankings):
    """return {player id: {various player information}}
    for given smash.gg tournament's phases and
    a dictionary of {ranking id: ranking name}
    
    input
    ---------
    phases: as output by get_sgg_phases()
    rankings: as output by get_melee_rankings()
    
    output
    ---------
    players: {player id:{
        tag: player's gamertag
        name: player's real name,
        country: player's home country,
        state: if country is US or Canada, then state/province,
        region: subregion if applicable (e.g. NorCal),
        rankings: {ranking name: number} (e.g. SSBMRank: 1),
        image: height, width, and url of profile image, if applicable
        }
    }
    """
    players = {}

    for p in phases:
        for s in p['entities']['seeds']:
            pid = s['mutations']['entrants'].keys()[0]
            p_info = s['mutations']['players'].values()[0]
            players.update(
                {pid: 
                 {
                     'tag': p_info['gamerTag'],
                     'name': p_info['name'],
                     'country': p_info['country'],
                     'state': p_info['state'],
                     'region': p_info['region'],
                     'rankings': {
                         rankings[r['seriesId']]:r['rank']
                         for r in p_info['rankings'] 
                         if r['seriesId'] in rankings
                     },
                     'image': {
                         'height':p_info['images'][0]['height'],
                         'width':p_info['images'][0]['width'],
                         'url':p_info['images'][0]['url']
                     } if len(p_info['images']) > 0
                      else None
                 }
                }
            )

    return players


def convert_players(pid_to_dict):
    """convert output of get_sgg_players to 
    dictionary keyed by player tags
    
    input
    ---------
    pid_to_dict: dict of playerID:{player info},
    as output by get_sgg_players()
    
    output
    ---------
    players: {tag: all other information}
    """
    players = {
        players2[p]['tag'] : {
            subitem:(players2[p][subitem] if subitem != 'ssbmrank' 
                     else players2[p][subitem][0] 
                     if len(players2[p][subitem]) > 0
                     else None)
            for subitem in players2[p] if subitem != 'tag'
        }
        for p in players2
    }
    return players


def add_to_graph(phases, players, graph=None):
    """add player losses for a tournament's phases
    to graph for analysis

    input
    ---------
    phases: list of tournament phase group json objects,
    as per get_sgg_phases()
    players: dictionary of {ID:tag}, as per get_sgg_players()
    graph (optional): include if appending tournaments to
    preexisting data; should be of the form
    defaultdict(lambda: defaultdict(int))

    output
    ---------
    graph: dictionary of {losing player : {winning player : n wins}}
    """
    if graph is None:
        graph = defaultdict(lambda: defaultdict(int))

    for p in phases:
        for s in p['entities']['sets']:
            winner = players.get(str(s['winnerId']))
            loser = players.get(str(s['loserId']))
            if winner is not None and loser is not None and \
                s['entrant1Score'] >= 0 and s['entrant2Score'] >= 0:
                graph[loser['tag']][winner['tag']] += 1

    return graph