import dash
from dash import html, dcc, Input, Output, State, callback, dash_table, ctx
import plotly.express as px
from agent import ask

app = dash.Dash(__name__)
app.title = "Jaffle Shop AI Assistant"

# Inject dark-mode CSS for body background and input placeholder
app.index_string = '''<!DOCTYPE html>
<html>
<head>
{%metas%}
<title>{%title%}</title>
{%favicon%}
{%css%}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
body { background-color: #0a0a0f; margin: 0; font-family: 'Inter', sans-serif; }
#user-input { font-family: 'Inter', sans-serif; height: 44px; line-height: 44px; box-sizing: border-box; }
#user-input::placeholder { color: #55556a !important; opacity: 1; }
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #141418; }
::-webkit-scrollbar-thumb { background: #2a2a30; border-radius: 3px; }
details summary::-webkit-details-marker { display: none; }
details > summary { list-style: none; }
#send-btn { transition: background-color 0.2s ease; }
#send-btn:hover { background-color: #6a4de0 !important; }
</style>
</head>
<body>
{%app_entry%}
<footer>{%config%}{%scripts%}{%renderer%}</footer>
</body>
</html>'''

def _build_sidebar():
    """Build the database schema sidebar."""
    schema = {
        "customers": {
            "rows": 200,
            "columns": [
                ("customer_id", "INTEGER"),
                ("first_name", "VARCHAR"),
                ("last_name", "VARCHAR"),
                ("email", "VARCHAR"),
                ("loyalty_tier", "VARCHAR"),
                ("created_at", "TIMESTAMP"),
            ],
        },
        "order_items": {
            "rows": 6583,
            "columns": [
                ("order_item_id", "INTEGER"),
                ("order_id", "INTEGER"),
                ("product_id", "INTEGER"),
                ("quantity", "INTEGER"),
                ("unit_price", "DECIMAL"),
                ("line_total", "DECIMAL"),
            ],
        },
        "orders": {
            "rows": 3000,
            "columns": [
                ("order_id", "INTEGER"),
                ("customer_id", "INTEGER"),
                ("order_date", "DATE"),
                ("status", "VARCHAR"),
                ("total_amount", "DECIMAL"),
                ("order_channel", "VARCHAR"),
            ],
        },
        "products": {
            "rows": 16,
            "columns": [
                ("product_id", "INTEGER"),
                ("product_name", "VARCHAR"),
                ("category", "VARCHAR"),
                ("price", "DECIMAL"),
                ("description", "VARCHAR"),
            ],
        },
    }

    table_blocks = []
    for table_name, info in schema.items():
        col_items = [
            html.Div(
                [
                    html.Span(col, style={"color": "#8e8ea0"}),
                    html.Span(f"  {dtype}", style={"color": "#55556a", "fontSize": "11px"}),
                ],
                style={"padding": "2px 0 2px 12px"},
            )
            for col, dtype in info["columns"]
        ]
        table_blocks.append(
            html.Details(
                [
                    html.Summary(
                        [
                            html.Span(table_name, style={"fontWeight": "bold", "color": "#ececf1"}),
                            html.Span(
                                f" · {info['rows']:,} rows",
                                style={"color": "#55556a", "fontSize": "11px", "fontWeight": "normal"},
                            ),
                        ],
                        style={"cursor": "pointer", "padding": "6px 0", "listStyleType": "none"},
                    ),
                    html.Div(col_items, style={"paddingBottom": "6px"}),
                ],
                style={"marginBottom": "4px"},
            )
        )

    return html.Div(
        style={
            "width": "260px",
            "minWidth": "260px",
            "backgroundColor": "#111115",
            "borderRight": "1px solid #2a2a30",
            "overflowY": "auto",
            "padding": "20px",
            "fontSize": "13px",
            "color": "#b0b0be",
        },
        children=[
            html.Div("Database Schema", style={"fontSize": "11px", "textTransform": "uppercase", "letterSpacing": "1px", "color": "#55556a", "marginBottom": "12px"}),
            *table_blocks,
        ],
    )


app.layout = html.Div(
    style={"display": "flex", "height": "100vh", "fontFamily": "'Inter', sans-serif", "backgroundColor": "#0a0a0f", "color": "#ececf1"},
    children=[
        _build_sidebar(),
        html.Div(
            style={"flex": "1", "display": "flex", "flexDirection": "column", "padding": "0 24px"},
            children=[
                html.H2("Jaffle Shop AI Assistant", style={"textAlign": "center", "padding": "20px 0 10px", "color": "#ececf1", "fontWeight": "600"}),
                html.P("Ask questions about customers, orders, and products in plain English.",
                       style={"textAlign": "center", "color": "#8e8ea0", "margin": "0 0 15px"}),

                # Chat history display
                html.Div(
                    id="chat-container",
                    style={"flex": "1", "overflowY": "auto", "padding": "10px", "border": "1px solid #2a2a30", "borderRadius": "12px", "backgroundColor": "#141418"},
                ),

                # Input area
                html.Div(
                    style={"display": "flex", "gap": "8px", "padding": "15px 0", "maxWidth": "680px", "width": "100%", "margin": "0 auto"},
                    children=[
                        dcc.Input(
                            id="user-input",
                            type="text",
                            placeholder="Ask about products, orders, revenue...",
                            style={"flex": "1", "padding": "0 16px", "borderRadius": "22px", "border": "1px solid #2a2a30", "fontSize": "14px", "backgroundColor": "#1c1c22", "color": "#ececf1", "height": "44px", "lineHeight": "44px"},
                            debounce=False,
                            n_submit=0,
                        ),
                        html.Button(
                            "Send",
                            id="send-btn",
                            n_clicks=0,
                            style={"padding": "12px 24px", "borderRadius": "22px", "border": "none", "backgroundColor": "#7c5cfc", "color": "white", "cursor": "pointer", "fontSize": "14px", "fontWeight": "500"},
                        ),
                    ],
                ),

                # Hidden stores
                dcc.Store(id="chat-history", data=[]),
                dcc.Store(id="display-messages", data=[]),
            ],
        ),
    ],
)


def user_bubble(text):
    return html.Div(
        text,
        style={"backgroundColor": "#7c5cfc", "color": "white", "padding": "12px 16px", "borderRadius": "16px 16px 4px 16px",
               "marginLeft": "auto", "maxWidth": "70%", "width": "fit-content", "marginBottom": "10px"},
    )


def assistant_bubble(children):
    return html.Div(
        children,
        style={"backgroundColor": "#1c1c22", "color": "#ececf1", "padding": "12px 16px", "borderRadius": "16px 16px 16px 4px",
               "border": "1px solid #2a2a30", "maxWidth": "85%", "marginBottom": "10px"},
    )


@callback(
    Output("chat-container", "children"),
    Output("chat-history", "data"),
    Output("display-messages", "data"),
    Output("user-input", "value"),
    Input("send-btn", "n_clicks"),
    Input("user-input", "n_submit"),
    State("user-input", "value"),
    State("chat-history", "data"),
    State("display-messages", "data"),
    prevent_initial_call=True,
)
def handle_send(n_clicks, n_submit, user_input, chat_history, display_messages):
    if not user_input or not user_input.strip():
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    question = user_input.strip()
    display_messages = display_messages or []
    chat_history = chat_history or []

    # Add user message to display
    display_messages.append({"role": "user", "content": question})

    # Call the agent
    try:
        result = ask(question, chat_history)
    except Exception as e:
        display_messages.append({"role": "assistant", "content": f"Sorry, something went wrong: {e}", "sql": None, "chart": None, "has_data": False})
        return _render_messages(display_messages), chat_history, display_messages, ""

    # Update Claude chat history for context
    chat_history.append({"role": "user", "content": question})
    chat_history.append({"role": "assistant", "content": result.get("answer", "")})

    # Store display message (data can't be serialized in dcc.Store, handle separately)
    msg = {
        "role": "assistant",
        "content": result.get("answer", ""),
        "sql": result.get("sql"),
        "chart": result.get("chart"),
        "has_data": result.get("data") is not None,
        "data_records": result["data"].head(20).to_dict("records") if result.get("data") is not None else None,
        "data_columns": list(result["data"].columns) if result.get("data") is not None else None,
    }
    display_messages.append(msg)

    return _render_messages(display_messages), chat_history, display_messages, ""


def _render_messages(messages):
    """Convert stored messages into Dash components."""
    elements = []
    for msg in messages:
        if msg["role"] == "user":
            elements.append(user_bubble(msg["content"]))
        else:
            children = [dcc.Markdown(msg["content"])]

            # Show SQL in collapsible detail
            if msg.get("sql"):
                children.append(
                    html.Details([
                        html.Summary("View SQL", style={"cursor": "pointer", "color": "#8e8ea0", "fontSize": "12px"}),
                        html.Code(msg["sql"], style={"display": "block", "padding": "8px", "backgroundColor": "#0e0e14", "color": "#a8b4ff", "borderRadius": "4px", "fontSize": "12px", "whiteSpace": "pre-wrap"}),
                    ], style={"marginTop": "8px"})
                )

            # Data table
            if msg.get("data_records"):
                children.append(
                    dash_table.DataTable(
                        data=msg["data_records"],
                        columns=[{"name": c, "id": c} for c in msg["data_columns"]],
                        style_table={"overflowX": "auto", "marginTop": "10px"},
                        style_cell={"textAlign": "left", "padding": "6px 10px", "fontSize": "13px", "backgroundColor": "#141418", "color": "#ececf1", "border": "1px solid #2a2a30"},
                        style_header={"backgroundColor": "#1c1c22", "fontWeight": "bold", "color": "#ececf1", "border": "1px solid #2a2a30"},
                        style_data_conditional=[{"if": {"row_index": "odd"}, "backgroundColor": "#18181e"}],
                        page_size=10,
                    )
                )

            # Chart
            if msg.get("chart") and msg.get("data_records"):
                chart = msg["chart"]
                import pandas as pd
                df = pd.DataFrame(msg["data_records"])
                fig = None
                if chart.get("type") == "bar":
                    fig = px.bar(df, x=chart["x"], y=chart["y"], title=chart.get("title", ""))
                elif chart.get("type") == "line":
                    fig = px.line(df, x=chart["x"], y=chart["y"], title=chart.get("title", ""))
                elif chart.get("type") == "pie":
                    fig = px.pie(df, names=chart["x"], values=chart["y"], title=chart.get("title", ""))
                if fig:
                    fig.update_layout(template="plotly_dark", paper_bgcolor="#1c1c22", plot_bgcolor="#141418", margin=dict(l=20, r=20, t=40, b=20), height=350)
                    children.append(dcc.Graph(figure=fig, style={"marginTop": "10px"}))

            elements.append(assistant_bubble(children))
    return elements


if __name__ == "__main__":
    app.run(debug=True, port=8050)
