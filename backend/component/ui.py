# backend/components/ui.py


from reactpy import component, html, hooks
import httpx
import json


@component
def MySQLConnector():
    host, set_host = hooks.use_state("localhost")
    user, set_user = hooks.use_state("root")
    password, set_password = hooks.use_state("")
    database, set_database = hooks.use_state("sakila")
    status, set_status = hooks.use_state("Not connected")

    async def connect(_event):
        set_status("Connecting...")
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    "/db/connect-mysql",
                    json={"host": host, "user": user, "password": password, "database": database}
                )
            set_status("Connected to MySQL")
        except Exception as exc:
            set_status(f"Connection failed: {str(exc)[:100]}")

    return html.div(
        {"style": {"padding": "24px", "background": "#e3f2fd", "border_radius": "16px", "margin_bottom": "24px"}},
        html.h3("MySQL Connection", {"style": {"margin_top": 0}}),
        html.div(
            {"style": {"display": "grid", "grid_template_columns": "1fr 1fr", "gap": "12px"}},
            html.input({"placeholder": "Host", "value": host, "on_change": lambda e: set_host(e["target"]["value"])}),
            html.input({"placeholder": "User", "value": user, "on_change": lambda e: set_user(e["target"]["value"])}),
            html.input({"placeholder": "Password", "type": "password", "value": password, "on_change": lambda e: set_password(e["target"]["value"])}),
            html.input({"placeholder": "Database", "value": database, "on_change": lambda e: set_database(e["target"]["value"])}),
        ),
        html.button(
            {"on_click": connect, "style": {"margin_top": "16px", "padding": "10px 20px", "font_size": "16px"}},
            "Connect to MySQL"
        ),
        html.p(status, {"style": {"margin_top": "12px", "font_weight": "bold", "color": "#1565c0"}})
    )


@component
def CSVUploader():
    path, set_path = hooks.use_state("sample_data/customers.csv")
    table_name, set_table_name = hooks.use_state("customers")
    message, set_message = hooks.use_state("")

    async def upload(_event):
        set_message("Loading...")
        try:
            async with httpx.AsyncClient() as client:
                await client.post("/db/load-csv", json={"path": path, "table_name": table_name})
            set_message(f"Loaded table '{table_name}' from CSV")
        except Exception as exc:
            set_message(f"Error: {str(exc)}")

    return html.div(
        {"style": {"padding": "24px", "background": "#e8f5e9", "border_radius": "16px", "margin_bottom": "24px"}},
        html.h3("Load CSV into SQLite", {"style": {"margin_top": 0}}),
        html.div(
            {"style": {"display": "flex", "gap": "12px", "align_items": "center"}},
            html.input(
                {"value": path, "on_change": lambda e: set_path(e["target"]["value"]), "style": {"flex": 1}}
            ),
            html.span("→"),
            html.input(
                {"value": table_name, "on_change": lambda e: set_table_name(e["target"]["value"]), "style": {"width": "200px"}}
            ),
        ),
        html.button({"on_click": upload, "style": {"margin_top": "12px"}}, "Load CSV"),
        message and html.p(message, {"style": {"margin_top": "12px", "font_weight": "500"}})
    )


@component
def SchemaDisplay():
    schema, set_schema = hooks.use_state(None)

    async def refresh(_event):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get("/db/schema")
                set_schema(resp.json())
        except Exception as exc:
            set_schema({"error": str(exc)})

    return html.div(
        {"style": {"padding": "24px", "background": "#fff3e0", "border_radius": "16px", "margin_bottom": "24px"}},
        html.div(
            {"style": {"display": "flex", "justify_content": "space-between", "align_items": "center"}},
            html.h3("Database Schema", {"style": {"margin": 0}}),
            html.button({"on_click": refresh}, "Refresh"),
        ),
        schema and html.pre(
            json.dumps(schema, indent=2),
            {"style": {"background": "#f5f5f5", "padding": "16px", "border_radius": "8px", "max_height": "500px", "overflow": "auto", "margin_top": "16px"}}
        )
    )


@component
def SQLExecutor():
    sql, set_sql = hooks.use_state("SELECT * FROM customers LIMIT 10")
    result, set_result = hooks.use_state(None)
    loading, set_loading = hooks.use_state(False)

    async def execute(_event):
        set_loading(True)
        set_result(None)
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post("/db/execute-sql", json={"query": sql})
                resp.raise_for_status()
                data = resp.json()
                set_result(data if isinstance(data, list) else {"error": str(data)})
        except Exception as exc:
            set_result({"error": str(exc)})
        finally:
            set_loading(False)

    return html.div(
        {"style": {"padding": "24px", "background": "#f3e5f5", "border_radius": "16px"}},
        html.h3("Execute SQL", {"style": {"margin_top": 0}}),
        html.textarea(
            {
                "value": sql,
                "rows": 8,
                "style": {"width": "100%", "font_family": "monospace", "padding": "12px", "font_size": "15px"},
                "on_change": lambda e: set_sql(e["target"]["value"])
            }
        ),
        html.button(
            {"on_click": execute, "disabled": loading, "style": {"margin_top": "12px", "padding": "12px 24px", "font_size": "16px"}},
            "Run Query" if not loading else "Running..."
        ),

        # Correct Python conditional rendering (no ? :)
        loading and html.p("Executing query...", {"style": {"margin_top": "16px", "font_style": "italic"}}),

        result and "error" in result and html.div(
            {"style": {"margin_top": "16px", "color": "red", "background": "#ffebee", "padding": "16px", "border_radius": "8px"}},
            html.strong("Error: "), result["error"]
        ),

        result and isinstance(result, list) and len(result) > 0 and html.div(
            {"style": {"margin_top": "16px"}},
            html.p(f"{len(result)} row{'s' if len(result) != 1 else ''} returned"),
            html.div(
                {"style": {"overflow_x": "auto", "margin_top": "12px"}},
                html.table(
                    {"style": {"width": "100%", "border_collapse": "collapse", "font_size": "14px"}},
                    html.thead(
                        html.tr(
                            [html.th(
                                {"style": {"border": "1px solid #ccc", "padding": "10px", "background": "#eee", "text_align": "left"}},
                                col
                            ) for col in result[0].keys()]
                        )
                    ),
                    html.tbody(
                        [html.tr(
                            [html.td(
                                {"style": {"border": "1px solid #ddd", "padding": "8px"}},
                                str(value) if value is not None else "NULL"
                            ) for value in row.values()]
                        ) for row in result[:100]]
                    )
                )
            ),
            len(result) > 100 and html.p(f"... showing first 100 of {len(result)} rows", {"style": {"margin_top": "8px", "color": "#666"}})
        ),

        result and isinstance(result, list) and len(result) == 0 and html.p("Query executed successfully (0 rows returned)", {"style": {"margin_top": "16px", "color": "#4caf50"}})
    )


@component
def App():
    return html.div(
        {"style": {"font_family": "system-ui, sans-serif", "max_width": "1300px", "margin": "0 auto", "padding": "32px", "background": "#fafafa", "min_height": "100vh"}},
        html.h1(
            {"style": {"text_align": "center", "color": "#1976d2", "font_size": "2.8rem", "margin_bottom": "8px"}},
            "NL2SQL • Multi-Database Interface"
        ),
        html.p(
            {"style": {"text_align": "center", "color": "#555", "font_size": "1.2rem", "margin_bottom": "40px"}},
            "Connect to MySQL • Load CSV • Explore Schema • Run SQL"
        ),

        MySQLConnector(),
        CSVUploader(),
        SchemaDisplay(),
        SQLExecutor(),

        html.footer(
            {"style": {"margin_top": "80px", "text_align": "center", "color": "#999", "font_size": "0.9rem"}},
            "Built with ReactPy + FastAPI • 100% Python • No JavaScript required"
        )
    )