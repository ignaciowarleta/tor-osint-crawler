import json
import os
from urllib.parse import urlparse

import matplotlib.pyplot as plt
import networkx as nx


INPUT_FILE = "results/crawl_results.json"
OUTPUT_IMAGE = "results/link_graph.png"


def shorten_label(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.hostname or "unknown"
    path = parsed.path.strip("/")

    if path:
        short_path = path[:20] + "..." if len(path) > 20 else path
        return f"{host}\n/{short_path}"
    return host


def risk_to_color(risk_label: str | None) -> str:
    if risk_label == "High":
        return "red"
    if risk_label == "Medium":
        return "orange"
    if risk_label == "Low":
        return "green"
    return "gray"


def main() -> None:
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(f"No existe {INPUT_FILE}")

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    graph = nx.DiGraph()
    node_risks: dict[str, str | None] = {}

    for page in data:
        source = page["url"]
        source_risk = page.get("risk_label")
        node_risks[source] = source_risk

        graph.add_node(source)

        for link in page.get("links", []):
            graph.add_node(link)
            graph.add_edge(source, link)

            if link not in node_risks:
                node_risks[link] = None

    if graph.number_of_nodes() == 0:
        print("No hay nodos para representar.")
        return

    labels = {node: shorten_label(node) for node in graph.nodes()}

    node_colors = [risk_to_color(node_risks.get(node)) for node in graph.nodes()]
    node_sizes = [300 + (graph.degree(node) * 80) for node in graph.nodes()]

    plt.figure(figsize=(14, 10))
    pos = nx.spring_layout(graph, seed=42, k=1.2)

    nx.draw_networkx_nodes(
        graph,
        pos,
        node_color=node_colors,
        node_size=node_sizes,
        alpha=0.85,
    )

    nx.draw_networkx_edges(
        graph,
        pos,
        arrows=True,
        arrowstyle="->",
        arrowsize=12,
        alpha=0.5,
        width=1.0,
    )

    nx.draw_networkx_labels(
        graph,
        pos,
        labels=labels,
        font_size=7,
    )

    plt.title("Tor OSINT Crawler - Link Relationship Graph")
    plt.axis("off")
    plt.tight_layout()

    os.makedirs(os.path.dirname(OUTPUT_IMAGE), exist_ok=True)
    plt.savefig(OUTPUT_IMAGE, dpi=200, bbox_inches="tight")
    plt.close()

    print(f"Grafo guardado en {OUTPUT_IMAGE}")


if __name__ == "__main__":
    main()