def route_topics(text: str, default_tags: list[str]) -> list[str]:
    lowered = text.lower()
    routed = set(default_tags)

    if any(keyword in lowered for keyword in ("agent", "workflow", "langgraph", "openmanus")):
        routed.add("Agents")
    if any(keyword in lowered for keyword in ("robot", "warehouse", "figure", "humanoid")):
        routed.add("Robotics")
    if any(keyword in lowered for keyword in ("open source", "github", "repo", "release")):
        routed.add("Open Source")
    if not routed:
        routed.add("AI")

    return sorted(routed)
