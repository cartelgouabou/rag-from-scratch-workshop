import asyncio

from agent.llm_client import VercelAIGatewayClient
from agent.router import _parse_route_response, heuristic_route, route_question


def test_heuristic_route_prefers_sql_for_aggregation_questions() -> None:
    assert heuristic_route("Quel est le total des ventes de mars ?").route == "sql"
    assert heuristic_route("Résume le rapport d'activité").route == "vector"


def test_heuristic_route_can_pick_both_for_mixed_question() -> None:
    decision = heuristic_route("Quels postes Arthur a-t-il occupés et combien d'années d'expérience a-t-il ?")
    assert decision.route == "both"
    assert decision.fallback_order[0] in {"sql", "vector"}


def test_parse_route_response_accepts_structured_json() -> None:
    decision = _parse_route_response(
        '{"route":"both","confidence":0.82,"reason":"mixte","fallback_order":["vector","sql"]}'
    )
    assert decision is not None
    assert decision.route == "both"
    assert decision.confidence == 0.82
    assert decision.fallback_order == ["vector", "sql"]


def test_route_question_falls_back_to_heuristic_without_api_key() -> None:
    client = VercelAIGatewayClient(
        base_url="https://ai-gateway.vercel.sh/v1",
        api_key="",
    )

    decision = asyncio.run(
        route_question(
            client,
            "google/gemini-3.1-flash-lite",
            "Combien de commandes en mars ?",
            sql_inventory="Document: example.csv\nTable: doc_example",
            document_inventory="- arthur_CV.pdf | type=pdf | active_chunks=27",
        )
    )

    assert decision.route == "sql"
    asyncio.run(client.close())
