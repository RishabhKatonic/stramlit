"""
Katonic App Deployment — Dash Test App
Framework: Dash | Port: 8050
Run: python app.py
"""
import dash
from dash import html, dcc, Input, Output
import plotly.express as px
import datetime
import os

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("🚀 Katonic Dash Test App", style={"textAlign": "center", "color": "#2c3e50"}),
    html.Div("✅ Dash is running successfully on Katonic!",
             style={"textAlign": "center", "color": "green", "fontSize": "18px", "marginBottom": "20px"}),

    html.Div([
        html.Div([
            html.H3("📋 Environment Info"),
            html.Ul([
                html.Li(f"Framework: Dash"),
                html.Li(f"Port: 8050"),
                html.Li(f"Hostname: {os.getenv('HOSTNAME', 'unknown')}"),
                html.Li(f"Timestamp: {datetime.datetime.now().isoformat()}"),
            ])
        ], style={"width": "45%", "display": "inline-block", "verticalAlign": "top"}),

        html.Div([
            html.H3("🧪 Interactive Test"),
            html.Label("Select chart type:"),
            dcc.Dropdown(
                id="chart-type",
                options=[
                    {"label": "Bar Chart", "value": "bar"},
                    {"label": "Line Chart", "value": "line"},
                    {"label": "Scatter Plot", "value": "scatter"},
                ],
                value="bar",
                style={"marginBottom": "10px"}
            ),
            dcc.Graph(id="test-chart"),
        ], style={"width": "50%", "display": "inline-block", "verticalAlign": "top"}),
    ]),

    html.Hr(),
    html.P(f"Katonic App Deployment Test | {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
           style={"textAlign": "center", "color": "gray"}),
], style={"padding": "20px", "fontFamily": "Arial"})


@app.callback(Output("test-chart", "figure"), Input("chart-type", "value"))
def update_chart(chart_type):
    data = {"Day": [f"Day {i}" for i in range(1, 8)],
            "Value": [23, 45, 56, 78, 32, 67, 89]}
    if chart_type == "bar":
        return px.bar(data, x="Day", y="Value", title="Sample Bar Chart")
    elif chart_type == "line":
        return px.line(data, x="Day", y="Value", title="Sample Line Chart")
    else:
        return px.scatter(data, x="Day", y="Value", title="Sample Scatter Plot")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=False)
