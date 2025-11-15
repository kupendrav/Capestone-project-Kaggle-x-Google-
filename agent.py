"""Small wrapper module exposing the workflow for the Flask app.
This imports the existing `research_agent_workflow` from `agent_app.py`.
"""
try:
    from agent_app import research_agent_workflow
except Exception:
    # Fallback: try loading from notebook-style module
    def research_agent_workflow(title: str, session_id: str = None, max_results: int = 5):
        raise RuntimeError('research_agent_workflow not found. Ensure agent_app.py exists and defines research_agent_workflow')

__all__ = ['research_agent_workflow']
