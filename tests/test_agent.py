from reflection_adk.agent import Critique, root_agent


def test_critique_schema_has_expected_fields():
    assert set(Critique.model_fields) == {"approved", "strengths", "improvements"}


def test_reflection_pipeline_has_three_stages():
    assert root_agent.name == "reflection_pipeline"
    assert [agent.name for agent in root_agent.sub_agents] == ["writer", "critic", "refiner"]

