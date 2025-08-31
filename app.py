import streamlit as st
import pandas as pd
import plotly.express as px
import io
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors

st.set_page_config(page_title="Statistici Elevi", layout="wide")
st.title("📊 Statistici vizuale pentru elevi")

# --- Încărcare fișier Excel ---
uploaded_file = st.file_uploader("Încarcă fișierul Excel cu elevi", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.write("👉 Coloane detectate în fișier:", df.columns.tolist())

    # --- Detectare automată coloană Media ---
    nume_coloane = [c.lower().strip() for c in df.columns]
    coloana_media = None
    for posibil in ["media", "medie", "nota finala", "nota_finala", "note"]:
        if posibil in nume_coloane:
            coloana_media = df.columns[nume_coloane.index(posibil)]
            break

    if not coloana_media:
        st.error("⚠️ Nu am găsit o coloană cu mediile. Te rog să ai o coloană 'Media' sau similar.")
        st.stop()

    df.rename(columns={coloana_media: "Media"}, inplace=True)

    # --- Status ---
    if "Status" not in df.columns:
        df["Status"] = df["Media"].apply(lambda x: "Reușit" if x >= 5 else "Nereușit")

    # 📋 Date brute
    st.subheader("📋 Date brute")
    st.dataframe(df)

    # 📈 Statistici
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

    # --- Grafice ---
    # Histogramă
    st.subheader("Distribuția mediilor")
    fig_hist = px.histogram(df, x="Media", nbins=10, title="Distribuția mediilor elevilor")
    st.plotly_chart(fig_hist, use_container_width=True)

    # Pie chart
    st.subheader("Procentaj promovare")
    fig_pie = px.pie(df, names="Status", title="Reușiți vs Nereușiți", hole=0.4)
    st.plotly_chart(fig_pie, use_container_width=True)

    # Bar chart intervale
    st.subheader("Intervalele mediilor")
    categorii = pd.cut(df["Media"], bins=[0,5,6,7,8,9,10])
    distributie = categorii.value_counts().sort_index()
    fig_bar = px.bar(distributie, x=distributie.index.astype(str), y=distributie.values,
                     labels={"x": "Interval medii", "y": "Număr elevi"},
                     title="Număr elevi pe intervale de medie")
    st.plotly_chart(fig_bar, use_container_width=True)

    # --- Export Excel ---
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Date elevi")
        pd.DataFrame({
            "Total elevi": [total],
            "Media generală": [media_generala],
            "Reușiți": [reusiti],
            "Nereușiți": [nereusiti]
        }).to_excel(writer, index=False, sheet_name="Statistici")
    data_xlsx = output.getvalue()

    st.download_button(
        label="⬇️ Descarcă raport Excel",
        data=data_xlsx,
        file_name="raport_statistic.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # --- Export PDF complet ---
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    width, height = letter

    # Titlu și statistici
    c.setFont("Helvetica-Bold", 16)
    c.drawString(180, 770, "📊 Raport Statistici Elevi")
    c.setFont("Helvetica", 12)
    c.drawString(50, 730, f"Total elevi: {total}")
    c.drawString(50, 710, f"Media generală: {media_generala:.2f}")
    c.drawString(50, 690, f"Reușiți: {reusiti}")
    c.drawString(50, 670, f"Nereușiți: {nereusiti}")

    # Grafic 1: Histogramă
    fig1, ax1 = plt.subplots()
    ax1.hist(df["Media"], bins=10, edgecolor="black")
    ax1.set_title("Distribuția mediilor")
    ax1.set_xlabel("Medie")
    ax1.set_ylabel("Număr elevi")
    img_bytes = io.BytesIO()
    plt.savefig(img_bytes, format='png', bbox_inches="tight")
    plt.close(fig1)
    img_bytes.seek(0)
    c.drawImage(ImageReader(img_bytes), 50, 400, width=500, height=200)

    # Grafic 2: Pie chart
    fig2, ax2 = plt.subplots()
    ax2.pie([reusiti, nereusiti], labels=["Reușiți", "Nereușiți"], autopct="%1.1f%%", startangle=90)
    ax2.set_title("Procentaj promovare")
    img_bytes = io.BytesIO()
    plt.savefig(img_bytes, format='png', bbox_inches="tight")
    plt.close(fig2)
    img_bytes.seek(0)
    c.drawImage(ImageReader(img_bytes), 50, 150, width=300, height=200)

    # Pagina 2: Bar chart
    c.showPage()
    c.setFont("Helvetica-Bold", 14)
    c.drawString(180, 770, "📊 Intervalele mediilor")
    fig3, ax3 = plt.subplots()
    distributie.plot(kind="bar", color="skyblue", edgecolor="black", ax=ax3)
    ax3.set_title("Număr elevi pe intervale de medie")
    ax3.set_xlabel("Intervale")
    ax3.set_ylabel("Număr elevi")
    plt.xticks(rotation=45)
    img_bytes = io.BytesIO()
    plt.savefig(img_bytes, format='png', bbox_inches="tight")
    plt.close(fig3)
    img_bytes.seek(0)
    c.drawImage(ImageReader(img_bytes), 50, 400, width=500, height=300)

    # Pagina 3: Tabel date brute (primele 30 de rânduri)
    c.showPage()
    c.setFont("Helvetica-Bold", 14)
    c.drawString(180, 770, "📋 Date brute din Excel")
    df_preview = df.head(30)
    data_table = [df_preview.columns.tolist()] + df_preview.values.tolist()
    table = Table(data_table, colWidths=[80]*len(df_preview.columns))
    style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 10),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
    ])
    table.setStyle(style)
    table.wrapOn(c, width, height)
    table.drawOn(c, 30, 400)

    # Finalizare PDF
    c.save()
    pdf_data = pdf_buffer.getvalue()

    st.download_button(
        label="⬇️ Descarcă raport PDF complet",
        data=pdf_data,
        file_name="raport_statistic.pdf",
        mime="application/pdf"
    )

else:
    st.info("📥 Încarcă un fișier Excel pentru a începe analiza.")
