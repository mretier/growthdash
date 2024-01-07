'''
author: Michael A. Reiter
(c) ETH Zurich, Michael A. Reiter, 2022

This file is part of Dashing Growth Curves.

Dashing Growth Curves is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Dashing Growth Curves is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Dashing Growth Curves. If not, see <https://www.gnu.org/licenses/>.
'''
import plotly.graph_objects as go


def overview_plot(df):
    def error_band(mean, std):
        # compute error band around mean of group of replicate samples
        x_error_pos = mean.index.to_list() + mean.index.to_list()[::-1]
        y_error_pos = (mean + std).to_list() + (mean - std).to_list()[::-1]

        return x_error_pos, y_error_pos



    names = df.index.str.extract(r'^(.*?)(?=_\d+$|\s\d+$|$)')
    names = names[0].str.strip().unique()
    t = df.columns.tolist()

    fig_overview = make_subplots(rows=1, cols=2, subplot_titles=('Individual', 'Grouped'))

    # trace colors
    trace_colors = sample_colorscale('icefire', np.linspace(0.1, 0.9, len(names)))

    for j, n in enumerate(names):
        df_n = df.loc[df.index.str.contains(n)]
        df_n_mean = df_n.mean(axis=0)
        df_n_std = df_n.std(axis=0)


        # trace color
        if n in ds.accepted_blank_names:
            # blanks
            trace_color = 'darkgrey'
        else:
            # samples
            trace_color = trace_colors[j]


        # add individual traces
        for i in range(df_n.shape[0]):
            fig_overview.add_trace(go.Scatter(x=t, y=df_n.iloc[i, :], name=df_n.index[i], line_color=trace_color, showlegend=False, legendgroup=n), row=1, col=1)

        # add error band
        errors_x, errors_y = error_band(df_n_mean, df_n_std)
        fig_overview.add_trace(
            go.Scatter(
                x=errors_x, y=errors_y, 
                fill='toself', 
                line_color=trace_color,
                line_width=0,
                showlegend=False,
                legendgroup=n,
                name=n,
                ), 
            row=1, col=2)
        
        # add mean trace
        fig_overview.add_trace(go.Scatter(x=t, y=df_n_mean, name=n, line_color=trace_color, legendgroup=n), row=1, col=2)


    fig_overview.update_layout(
        font_size = 16,
        font_color = 'black',
        font_family = 'Open Sans',
        legend_x = 0.5,
        legend_xanchor = 'center',

        xaxis_domain = [0, 0.40],
        xaxis2_domain = [0.60, 1],
        )

    fig_overview.update_annotations(
        yshift = 20,
        font_size = 20,
    )

    return fig_overview

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
