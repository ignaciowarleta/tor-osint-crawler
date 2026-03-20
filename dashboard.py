import json
import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt


st.set_page_config(page_title="Tor OSINT Dashboard", layout="wide")

st.title("Tor OSINT Dashboard")
st.write("Visualización de resultados del crawler sobre Tor.")

RESULTS_JSON = "results/crawl_results.json"
SUMMARY_JSON = "results/summary.json"
GRAPH_IMAGE = "results/link_graph.png"


def load_json(path: str):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


results = load_json(RESULTS_JSON)
summary = load_json(SUMMARY_JSON)

if not results:
    st.warning("No se encontraron resultados. Ejecuta primero el crawler.")
    st.stop()

df = pd.DataFrame(results)

st.subheader("KPIs")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Páginas analizadas", len(df))
c2.metric("Errores", int(df["error"].notna().sum()) if "error" in df else 0)
c3.metric("High Risk", int((df["risk_label"] == "High").sum()) if "risk_label" in df else 0)
c4.metric("Forms", int(df["forms_count"].sum()) if "forms_count" in df else 0)

if summary:
    st.subheader("Resumen")
    st.json(summary)

st.subheader("Distribución de categorías")
if "category" in df:
    fig, ax = plt.subplots(figsize=(6, 3))
    df["category"].value_counts().plot(kind="bar", ax=ax)
    ax.set_xlabel("Categoría")
    ax.set_ylabel("Número de páginas")
    plt.tight_layout()
    st.pyplot(fig)

st.subheader("Distribución de riesgo")
if "risk_label" in df:
    fig, ax = plt.subplots(figsize=(6, 3))
    df["risk_label"].value_counts().reindex(["High", "Medium", "Low"], fill_value=0).plot(kind="bar", ax=ax)
    ax.set_xlabel("Risk Label")
    ax.set_ylabel("Número de páginas")
    plt.tight_layout()
    st.pyplot(fig)

st.subheader("Resultados")
st.dataframe(df, use_container_width=True)

if os.path.exists(GRAPH_IMAGE):
    st.subheader("Grafo de enlaces")
    st.image(GRAPH_IMAGE, caption="Relaciones entre páginas y enlaces")