from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Literal

import httpx
from agent.llm_client import VercelAIGatewayClient

ROUTER_PROMPT = """
Tu es un agent de routage pour un assistant RAG multi-source.
Analyse la question, l'inventaire SQL et l'inventaire documentaire.
Réponds UNIQUEMENT en JSON avec ce schema:
{"route":"sql|vector|both","confidence":0.0,"reason":"...","fallback_order":["sql|vector","sql|vector"]}

Règles de décision :
  "sql"    → question sur des données chiffrées, filtres, agrégations,
             dates précises, comptages, colonnes spécifiques, tableaux.
  "vector" → question sémantique, recherche de concepts, profils, postes,
             résumés, reformulations, questions ouvertes sur des documents.
  "both"   → la question combine un besoin tabulaire et documentaire, ou
             l'intention est mixte / incertaine.

Ne renvoie jamais de markdown. `fallback_order` doit contenir exactement 2 routes
parmi `sql` et `vector`.
""".strip()

RoutingSource = Literal["sql", "vector", "both"]


@dataclass
class RouteDecision:
    route: RoutingSource
    confidence: float
    reason: str
    fallback_order: list[Literal["sql", "vector"]]


def heuristic_route(question: str) -> RouteDecision:
    lowered = question.lower()
    sql_keywords = [
        "combien",
        "total",
        "moyenne",
        "somme",
        "liste",
        "filtre",
        "mars",
        "avril",
        "2024",
        "statut",
        "nombre",
        "top",
        "tableau",
        "ligne",
        "colonne",
        "somme",
        "minimum",
        "maximum",
        "filtrer",
    ]
    vector_keywords = [
        "qui",
        "profil",
        "poste",
        "postes",
        "experience",
        "expérience",
        "competence",
        "compétence",
        "parcours",
        "cv",
        "resume",
        "résume",
        "document",
    ]
    both_keywords = [
        "ainsi que",
        "en te basant",
        "a partir des documents et des donnees",
        "à partir des documents et des données",
        "croise",
        "croiser",
        "combine",
        "comparer",
    ]

    sql_score = sum(keyword in lowered for keyword in sql_keywords)
    vector_score = sum(keyword in lowered for keyword in vector_keywords)
    if any(character.isdigit() for character in question):
        sql_score += 1
    if any(keyword in lowered for keyword in both_keywords):
        sql_score += 1
        vector_score += 1

    if sql_score > 0 and vector_score > 0:
        route: RoutingSource = "both"
    elif sql_score > 0:
        route = "sql"
    else:
        route = "vector"

    if route == "both":
        fallback_order = ["vector", "sql"] if vector_score >= sql_score else ["sql", "vector"]
        confidence = 0.55
    elif route == "sql":
        fallback_order = ["sql", "vector"]
        confidence = 0.72 if sql_score >= 2 else 0.58
    else:
        fallback_order = ["vector", "sql"]
        confidence = 0.74 if vector_score >= 1 else 0.56

    return RouteDecision(
        route=route,
        confidence=confidence,
        reason="Heuristique locale basee sur la question utilisateur.",
        fallback_order=fallback_order,
    )


async def route_question(
    gateway_client: VercelAIGatewayClient,
    router_model: str,
    question: str,
    *,
    sql_inventory: str,
    document_inventory: str,
) -> RouteDecision:
    if not gateway_client.is_configured:
        return heuristic_route(question)

    try:
        response = await gateway_client.complete(
            model=router_model,
            system=ROUTER_PROMPT,
            user=(
                f"Question:\n{question}\n\n"
                f"Inventaire SQL:\n{sql_inventory}\n\n"
                f"Inventaire documentaire:\n{document_inventory}\n\n"
                "JSON:"
            ),
            max_tokens=180,
            temperature=0,
        )
    except httpx.HTTPError:
        return heuristic_route(question)

    parsed = _parse_route_response(response)
    return parsed if parsed is not None else heuristic_route(question)


def _parse_route_response(raw_response: str) -> RouteDecision | None:
    try:
        payload = json.loads(raw_response.strip())
    except json.JSONDecodeError:
        return None

    route = payload.get("route")
    confidence = payload.get("confidence", 0.5)
    reason = str(payload.get("reason", "")).strip() or "Routage fourni par le modele."
    fallback_order = payload.get("fallback_order", [])

    if route not in {"sql", "vector", "both"}:
        return None
    if not isinstance(confidence, (int, float)):
        confidence = 0.5
    confidence = min(max(float(confidence), 0.0), 1.0)

    normalized_fallbacks = [item for item in fallback_order if item in {"sql", "vector"}]
    if len(normalized_fallbacks) != 2:
        normalized_fallbacks = ["sql", "vector"] if route == "sql" else ["vector", "sql"]

    return RouteDecision(
        route=route,
        confidence=confidence,
        reason=reason,
        fallback_order=normalized_fallbacks,
    )
