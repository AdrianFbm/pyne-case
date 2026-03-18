import dash
from dash import html, dcc, Input, Output, State, callback, dash_table, ctx, ALL, MATCH
import pandas as pd
from db import run_query
import plotly.express as px
from agent import ask

app = dash.Dash(__name__)
app.title = "AI-oli - Jaffle Shop Assistant"

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
#user-input { font-family: 'Inter', sans-serif; height: 52px; line-height: 52px; box-sizing: border-box; }
#user-input::placeholder { color: #55556a !important; opacity: 1; }
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #141418; }
::-webkit-scrollbar-thumb { background: #2a2a30; border-radius: 3px; }
details summary::-webkit-details-marker { display: none; }
details > summary { list-style: none; }
#send-btn, .sql-action-btn { transition: background-color 0.2s ease; }
#send-btn:hover { background-color: #6a4de0 !important; }
#sql-editor {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  background-color: #0e0e14;
  color: #a8b4ff;
  border: 1px solid #2a2a30;
  border-radius: 6px;
  padding: 8px;
  width: 100%;
  box-sizing: border-box;
  resize: vertical;
}
#sql-editor:focus { outline: 1px solid #7c5cfc; }
.sql-action-btn {
  padding: 6px 12px;
  border-radius: 6px;
  border: none;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  font-family: 'Inter', sans-serif;
}
.sql-action-btn:hover { opacity: 0.85; }
.copy-sql-btn { background: none; border: none; color: #7c5cfc; cursor: pointer; font-size: 11px; padding: 4px 8px; font-family: 'Inter', sans-serif; }
.copy-sql-btn:hover { text-decoration: underline; }
@keyframes dotPulse {
  0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
  40% { opacity: 1; transform: scale(1); }
}
.loading-dots span {
  display: inline-block;
  width: 8px; height: 8px;
  margin: 0 3px;
  background: #8e8ea0;
  border-radius: 50%;
  animation: dotPulse 1.4s infinite ease-in-out;
}
.loading-dots span:nth-child(2) { animation-delay: 0.2s; }
.loading-dots span:nth-child(3) { animation-delay: 0.4s; }
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

    sql_editor_section = [
        html.Div("SQL Editor", style={"fontSize": "11px", "textTransform": "uppercase", "letterSpacing": "1px", "color": "#55556a", "marginBottom": "12px", "marginTop": "20px", "borderTop": "1px solid #2a2a30", "paddingTop": "16px"}),
        dcc.Textarea(
            id="sql-editor",
            placeholder="SELECT * FROM customers LIMIT 10",
            rows=6,
            style={"width": "100%", "marginBottom": "8px"},
        ),
        html.Div(
            style={"display": "flex", "gap": "6px", "marginBottom": "10px"},
            children=[
                html.Button("Run", id="run-sql-btn", n_clicks=0, className="sql-action-btn",
                            style={"backgroundColor": "#7c5cfc", "color": "white"}),
                html.Button("Run latest", id="run-latest-btn", n_clicks=0, className="sql-action-btn",
                            style={"backgroundColor": "#2a2a30", "color": "#ececf1"}),
            ],
        ),
        html.Div(id="sql-results"),
    ]

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
            *sql_editor_section,
        ],
    )


app.layout = html.Div(
    style={"display": "flex", "height": "100vh", "fontFamily": "'Inter', sans-serif", "backgroundColor": "#0a0a0f", "color": "#ececf1"},
    children=[
        _build_sidebar(),
        html.Div(
            style={"flex": "1", "display": "flex", "flexDirection": "column", "padding": "0 24px"},
            children=[
                html.Div(
                    style={"display": "flex", "alignItems": "center", "justifyContent": "center", "gap": "12px", "padding": "20px 0 10px"},
                    children=[
                        html.Img(src="/assets/logo.svg", style={"width": "48px", "height": "48px"}),
                        html.H2("AI-oli - Jaffle Shop Assistant", style={"margin": "0", "color": "#ececf1", "fontWeight": "600"}),
                    ],
                ),
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
                            style={"flex": "1", "padding": "0 16px", "borderRadius": "22px", "border": "1px solid #2a2a30", "fontSize": "14px", "backgroundColor": "#1c1c22", "color": "#ececf1", "height": "52px", "lineHeight": "52px"},
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
                dcc.Store(id="pending-question", data=None),
                dcc.Store(id="latest-chat-sql", data=None),
                dcc.Store(id="all-chat-sqls", data=[]),
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
    Output("chat-container", "children", allow_duplicate=True),
    Output("display-messages", "data", allow_duplicate=True),
    Output("pending-question", "data"),
    Output("user-input", "value"),
    Input("send-btn", "n_clicks"),
    Input("user-input", "n_submit"),
    State("user-input", "value"),
    State("display-messages", "data"),
    prevent_initial_call=True,
)
def show_user_message(n_clicks, n_submit, user_input, display_messages):
    """Instantly show the user's message and a loading indicator."""
    if not user_input or not user_input.strip():
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    question = user_input.strip()
    display_messages = display_messages or []
    display_messages.append({"role": "user", "content": question})

    # Render messages + loading dots
    elements = _render_messages(display_messages)
    loading_bubble = html.Div(
        html.Div(
            [html.Span(), html.Span(), html.Span()],
            className="loading-dots",
            style={"padding": "4px 0"},
        ),
        style={"backgroundColor": "#1c1c22", "color": "#ececf1", "padding": "12px 16px", "borderRadius": "16px 16px 16px 4px",
               "border": "1px solid #2a2a30", "width": "fit-content", "marginBottom": "10px"},
    )
    elements.append(loading_bubble)

    return elements, display_messages, question, ""


@callback(
    Output("chat-container", "children"),
    Output("chat-history", "data"),
    Output("display-messages", "data"),
    Output("latest-chat-sql", "data"),
    Output("all-chat-sqls", "data"),
    Input("pending-question", "data"),
    State("chat-history", "data"),
    State("display-messages", "data"),
    State("all-chat-sqls", "data"),
    prevent_initial_call=True,
)
def handle_llm_response(question, chat_history, display_messages, all_sqls):
    """Call the LLM and replace the loading indicator with the response."""
    if not question:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    chat_history = chat_history or []
    display_messages = display_messages or []
    all_sqls = all_sqls or []

    try:
        result = ask(question, chat_history)
    except Exception as e:
        display_messages.append({"role": "assistant", "content": f"Sorry, something went wrong: {e}", "sql": None, "chart": None, "has_data": False})
        all_sqls.append(None)
        return _render_messages(display_messages), chat_history, display_messages, dash.no_update, all_sqls

    chat_history.append({"role": "user", "content": question})
    chat_history.append({"role": "assistant", "content": result.answer})

    sql = result.sql
    msg = {
        "role": "assistant",
        "content": result.answer,
        "sql": sql,
        "chart": result.chart,
        "has_data": result.sql_data is not None,
        "data_records": result.sql_data.head(20).to_dict("records") if result.sql_data is not None else None,
        "data_columns": list(result.sql_data.columns) if result.sql_data is not None else None,
    }
    display_messages.append(msg)
    all_sqls.append(sql)
    latest_sql = sql if sql else dash.no_update

    return _render_messages(display_messages), chat_history, display_messages, latest_sql, all_sqls


def _render_messages(messages):
    """Convert stored messages into Dash components."""
    elements = []
    sql_index = 0
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
                        html.Button("Copy to editor", className="copy-sql-btn",
                                    id={"type": "copy-sql-btn", "index": sql_index},
                                    n_clicks=0),
                    ], style={"marginTop": "8px"})
                )
                sql_index += 1

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


@callback(
    Output("sql-editor", "value", allow_duplicate=True),
    Input({"type": "copy-sql-btn", "index": ALL}, "n_clicks"),
    State("all-chat-sqls", "data"),
    prevent_initial_call=True,
)
def copy_sql_to_editor(n_clicks_list, all_sqls):
    """Copy a specific SQL query from chat into the SQL editor."""
    if not ctx.triggered_id or not any(n_clicks_list):
        return dash.no_update
    index = ctx.triggered_id["index"]
    # all_sqls contains one entry per assistant message (None if no SQL)
    # But sql_index only counts messages that have SQL, so we need to map
    sql_only = [s for s in (all_sqls or []) if s]
    if index < len(sql_only):
        return sql_only[index]
    return dash.no_update


@callback(
    Output("sql-results", "children"),
    Input("run-sql-btn", "n_clicks"),
    State("sql-editor", "value"),
    prevent_initial_call=True,
)
def run_sql(n_clicks, sql):
    """Execute the SQL in the editor and display results."""
    if not sql or not sql.strip():
        return html.Div("Enter a SQL query to run.", style={"color": "#55556a", "fontSize": "12px"})
    result = run_query(sql.strip())
    if isinstance(result, str):
        return html.Div(result, style={"color": "#ff6b6b", "fontSize": "12px", "whiteSpace": "pre-wrap"})
    if result.empty:
        return html.Div("Query returned no rows.", style={"color": "#8e8ea0", "fontSize": "12px"})
    return dash_table.DataTable(
        data=result.head(50).to_dict("records"),
        columns=[{"name": c, "id": c} for c in result.columns],
        style_table={"overflowX": "auto"},
        style_cell={"textAlign": "left", "padding": "4px 8px", "fontSize": "11px", "backgroundColor": "#141418", "color": "#ececf1", "border": "1px solid #2a2a30", "maxWidth": "180px", "overflow": "hidden", "textOverflow": "ellipsis"},
        style_header={"backgroundColor": "#1c1c22", "fontWeight": "bold", "color": "#ececf1", "border": "1px solid #2a2a30"},
        style_data_conditional=[{"if": {"row_index": "odd"}, "backgroundColor": "#18181e"}],
        page_size=10,
    )


@callback(
    Output("sql-editor", "value"),
    Output("sql-results", "children", allow_duplicate=True),
    Input("run-latest-btn", "n_clicks"),
    State("latest-chat-sql", "data"),
    prevent_initial_call=True,
)
def run_latest_from_chat(n_clicks, latest_sql):
    """Fill the editor with the latest chat SQL and run it."""
    if not latest_sql:
        return dash.no_update, html.Div("No SQL from chat yet.", style={"color": "#55556a", "fontSize": "12px"})
    result = run_query(latest_sql.strip())
    if isinstance(result, str):
        result_component = html.Div(result, style={"color": "#ff6b6b", "fontSize": "12px", "whiteSpace": "pre-wrap"})
    elif result.empty:
        result_component = html.Div("Query returned no rows.", style={"color": "#8e8ea0", "fontSize": "12px"})
    else:
        result_component = dash_table.DataTable(
            data=result.head(50).to_dict("records"),
            columns=[{"name": c, "id": c} for c in result.columns],
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left", "padding": "4px 8px", "fontSize": "11px", "backgroundColor": "#141418", "color": "#ececf1", "border": "1px solid #2a2a30", "maxWidth": "180px", "overflow": "hidden", "textOverflow": "ellipsis"},
            style_header={"backgroundColor": "#1c1c22", "fontWeight": "bold", "color": "#ececf1", "border": "1px solid #2a2a30"},
            style_data_conditional=[{"if": {"row_index": "odd"}, "backgroundColor": "#18181e"}],
            page_size=10,
        )
    return latest_sql, result_component


if __name__ == "__main__":
    app.run(debug=True, port=8050)
