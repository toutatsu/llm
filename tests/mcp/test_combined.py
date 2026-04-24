from llm.mcp.server.combined import app


def test_expected_paths_mounted():
    mounted_paths = {route.path for route in app.routes}
    for path in ["/math", "/text", "/search", "/shell", "/filesystem", "/postgres",
                 "/datetime", "/http"]:
        assert path in mounted_paths, f"{path} が app.routes に存在しない"
