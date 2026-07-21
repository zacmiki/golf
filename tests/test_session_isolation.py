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

    assert not alice.exception and not bob.exception
    assert "Alice (111)" in alice.success[0].value
    assert "Bob (222)" in bob.success[0].value
    assert "12.3" in alice.success[0].value
    assert "24.6" in bob.success[0].value
