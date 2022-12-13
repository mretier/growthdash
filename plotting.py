'''
author: Michael A. Reiter
(c) ETH Zurich, Michael A. Reiter, 2022

This file is part of Dashing Growth Curves.

Dashing Growth Curves is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Dashing Growth Curves is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Dashing Growth Curves. If not, see <https://www.gnu.org/licenses/>.
'''
import plotly.graph_objects as go



def bar_chart(names, y, errors, n_ex, y_axis='y', dp_overlay=None, ):

    # pop out blank values from figure
    names = names.copy()
    y = y.copy()
    dp_overlay = dp_overlay.copy()
    errors = errors.copy()
    n_ex = n_ex.copy()
    idx_blank = [i for i in range(len(names)) if names[i] in ['blank', 'Blank', 'blanks', 'Blanks']]
    blank_names = [names.pop(x) for x in sorted(idx_blank, reverse=True)]
    [y.pop(x) for x in sorted(idx_blank, reverse=True)]
    [errors.pop(x) for x in sorted(idx_blank, reverse=True)]
    [n_ex.pop(x) for x in sorted(idx_blank, reverse=True)]
    [dp_overlay.pop(x) for x in blank_names]
    

    # annotate number of excluded samples in bar chart
    annotations = [{'text': '<b>{}</b>'.format(x), 'x': i, 'y': 0.02, 'yref':'y domain', 'font_size': 16, 'showarrow':False} for i, x in enumerate(n_ex)]

    # plor bar chart
    if errors is None:
        data = [go.Bar(x=names, y=y, marker_color='rgb(39, 125, 161)')]
    else:
        hovertexts = ['{:.2f} &plusmn; {:.2f}'.format(y[i], errors[i]) for i in range(len(names))]
        data = [go.Bar(x=names, y=y, 
                        error_y={'type': 'data', 'array':errors},
                        marker_color='rgb(44, 105, 154)', 
                        hoverinfo='text', 
                        hovertext=hovertexts,
                )]
    
    # overlay individual datapoints
    if dp_overlay is not None:
        # dp_overlay is a dict with the same keys as the "names" variable and contains individual datapoints to be plotted on top of the bar chars
        data_overlay = [go.Box(y=[y['value'] for y in dp_overlay[x]],
                                boxpoints='all',
                                name=x, jitter=0.5,
                                pointpos=0.25,
                                fillcolor='rgba(255,255,255,0)',
                                hoveron='points',
                                hoverinfo='text',
                                hovertext=['{}'.format(y['name']) for y in dp_overlay[x]],
                                marker={'size': 15, 'line':{'width':4, 'color': 'rgb(242, 158, 76)'}, 'opacity':0.75, 'color':'rgba(0,0,0,0)'},
                                line={'color':'rgba(255,255,255,0)'})
                         for x in names]
        data.extend(data_overlay)



    layout = go.Layout(
                      font = {'size': 16},
                      showlegend = False,
                      xaxis = {'title': ''},
                      yaxis = {'title': y_axis},
                      paper_bgcolor = 'rgba(0,0,0,0)',
                      plot_bgcolor = 'rgba(0,0,0,0)',
                      annotations=annotations,
                      margin = {'l':80, 'r': 0, 't': 40, 'b': 150},
                      modebar =  {'bgcolor':'rgba(0,0,0,0)', 'color':'darkslategrey', "activecolor":'black'},
                      )



    fig = go.Figure(data=data, layout=layout)
    return fig
