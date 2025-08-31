import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Statistici Elevi", layout="wide")

st.title("📊 Statistici vizuale pentru elevi")

# Încărcare fișier Excel
uploaded_file = st.file_uploader("Încarcă fișierul Excel cu elevi", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Dacă nu există coloană Status, o adăugăm
    if "Status" not in df.columns and "Media" in df.columns:
        df["Status"] = df["Media"].apply(lambda x: "Reușit" if x >= 5 else "Nereușit")

    st.subheader("📋 Date brute")
    st.dataframe(df)

    # Statistici de bază
    st.subheader("📈 Statistici")
    total = len(df)
    media_generala = df["Media"].mean()
    reusiti = len(df[df["Status"] == "Reușit"])
    nereusiti = len(df[df["Status"] == "Nereușit"])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total elevi", total)
    col2.metric("Media generală", f"{media_generala:.2f}")
    col3.metric("Reușiți", reusiti)
    col4.metric("Nereușiți", nereusiti)

    # Histogramă distribuție medii
    st.subheader("📊 Distribuția mediilor")
    fig_hist = px.histogram(df, x="Media", nbins=10, title="Distribuția mediilor elevilor")
    st.plotly_chart(fig_hist, use_container_width=True)

    # Pie chart reușiți vs nereușiți
    st.subheader("🥧 Procentaj promovare")
    fig_pie = px.pie(df, names="Status", title="Reușiți vs Nereușiți", hole=0.4)
    st.plotly_chart(fig_pie, use_container_width=True)

    # Bar chart intervale de note
    st.subheader("📊 Intervalele mediilor")
    categorii = pd.cut(df["Media"], bins=[0,5,6,7,8,9,10])
    distributie = categorii.value_counts().sort_index()
    fig_bar = px.bar(distributie, x=distributie.index.astype(str), y=distributie.values,
                     labels={"x": "Interval medii", "y": "Număr elevi"},
                     title="Număr elevi pe intervale de medie")
    st.plotly_chart(fig_bar, use_container_width=True)
else:
    st.info("📥 Încarcă un fișier Excel pentru a începe analiza.")
