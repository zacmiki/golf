import pandas as pd
from streamlit.testing.v1 import AppTest


def app_session(name: str, membership: int, handicap: float) -> AppTest:
    app = AppTest.from_file("streamlit_app.py").run()
    app.session_state["logged_in"] = True
    app.session_state["selected_option"] = "Handicap Manager"
    app.session_state["tesserato_name"] = name
    app.session_state["df"] = pd.DataFrame(
        {
            "Numero tessera": [membership],
            "Index Nuovo": [handicap],
            "Data": ["01/01/2026"],
            "Gara": ["Test round"],
            "Stbl": [36],
            "Formula": ["STB"],
            "SD": [handicap],
        }
    )
    return app.run()


def test_member_data_is_isolated_between_sessions() -> None:
    alice = app_session("Alice", 111, 12.3)
    bob = app_session("Bob", 222, 24.6)

    assert alice.metric[0].value == "Alice (111)"
    assert bob.metric[0].value == "Bob (222)"
    assert alice.metric[1].value == "12.3"
    assert bob.metric[1].value == "24.6"
