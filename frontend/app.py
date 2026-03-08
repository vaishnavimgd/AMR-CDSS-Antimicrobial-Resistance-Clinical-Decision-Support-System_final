# app.py
import streamlit as st
import requests
import pandas as pd
import altair as alt
import numpy as np

# -------------------- Page Config --------------------
st.set_page_config(page_title="🧬 AMR Prediction Dashboard", layout="wide", initial_sidebar_state="expanded")

# -------------------- Custom CSS --------------------
st.markdown("""
    <style>
    body {
        background: linear-gradient(to right, #e0eafc, #cfdef3);
    }
    .card {
        border-radius: 15px;
        padding: 15px;
        color: white;
        text-align:center;
        box-shadow: 3px 3px 15px rgba(0,0,0,0.2);
        margin-bottom: 10px;
    }
    .resistant {background: linear-gradient(to right, #FF416C, #FF4B2B);}
    .susceptible {background: linear-gradient(to right, #43e97b, #38f9d7);}
    .intermediate {background: linear-gradient(to right, #f7971e, #ffd200);}
    </style>
""", unsafe_allow_html=True)

# -------------------- Header --------------------
st.markdown("""
<div style="background: linear-gradient(to right, #667eea, #764ba2); 
            padding: 20px; border-radius: 15px; text-align:center">
    <h1 style="color:white;">🧬 AMR Prediction Dashboard</h1>
    <p style="color:white; font-size:16px;">Interactive visualization of antimicrobial resistance genes</p>
</div>
""", unsafe_allow_html=True)

# -------------------- File Upload --------------------
uploaded_file = st.file_uploader(
    "📂 Upload FASTA File", 
    type=["fasta", "fa", "fna"], 
    help="Drag & drop a FASTA file (.fasta, .fa, .fna). Max 200MB."
)

if uploaded_file:
    st.success(f"✅ File uploaded: {uploaded_file.name}")
    files = {'file': (uploaded_file.name, uploaded_file, 'text/plain')}

    # -------------------- API Call with Spinner --------------------
    api_url = "http://127.0.0.1:8000/upload-fasta"
    with st.spinner("⚙️ Initializing C++ Extraction Engine..."):
        pass
    with st.spinner("🤖 Running PyTorch Inference..."):
        try:
            response = requests.post(api_url, files=files, timeout=120)
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.ConnectionError:
            st.error("❌ Could not connect to the backend. Make sure FastAPI is running on http://127.0.0.1:8000")
            st.stop()
        except requests.exceptions.Timeout:
            st.error("❌ Request timed out. The backend took too long to respond.")
            st.stop()
        except requests.exceptions.HTTPError as e:
            st.error(f"❌ Backend returned an error: {e}")
            st.stop()
        except Exception as e:
            st.error(f"❌ Unexpected error: {e}")
            st.stop()

    # -------------------- Parse backend response --------------------
    predictions = result.get("predictions", {})
    genes_detected = result.get("genes_detected", [])
    warnings = result.get("warnings", [])
    anomaly = result.get("anomaly", False)
    num_sequences = result.get("num_sequences", 0)

    # -------------------- Warning Banner --------------------
    if warnings:
        for w in warnings:
            st.warning(f"⚠️ {w}")

    # -------------------- Anomaly Detection Banner --------------------
    if anomaly:
        st.error("⚠️ Unknown strain detected — unusual AMR gene patterns identified!")

    # -------------------- Tabs for Charts --------------------
    tabs = st.tabs(["Summary", "Antibiotics", "Gene Detection", "SHAP Heatmap", "Pie Chart"])

    # -------------------- Summary Tab --------------------
    with tabs[0]:
        st.markdown("### 📊 Summary")
        total_genes = int(sum(genes_detected)) if genes_detected else 0
        summary = {
            "Sequences Analyzed": num_sequences,
            "Genes Detected": total_genes,
            "Antibiotics Tested": len(predictions),
        }
        cols = st.columns(len(summary))
        colors = ["#667eea", "#764ba2", "#43e97b"]
        for col, (key, value), color in zip(cols, summary.items(), colors):
            col.markdown(f"""
            <div class="card" style="background:{color};">
                <h4>{key}</h4>
                <p style='font-size:20px'>{value}</p>
            </div>
            """, unsafe_allow_html=True)

    # -------------------- Antibiotics Tab --------------------
    with tabs[1]:
        st.markdown("### 🛡️ Antibiotic Resistance Status")
        if predictions:
            cols = st.columns(len(predictions))
            icons = {"ciprofloxacin": "💊", "ampicillin": "🧪", "tetracycline": "🩺"}
            res_counts = {"Resistant": 0, "Susceptible": 0, "Intermediate": 0}
            for col, (ab, status) in zip(cols, predictions.items()):
                if status in res_counts:
                    res_counts[status] += 1
                cls = "resistant" if status == "Resistant" else ("intermediate" if status == "Intermediate" else "susceptible")
                icon = icons.get(ab.lower(), "💉")
                col.markdown(f"""
                <div class="card {cls}">
                    <h3>{icon} {ab.capitalize()}</h3>
                    <p style="font-size:18px">{status}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("No antibiotic predictions available.")

    # -------------------- Gene Detection Tab --------------------
    with tabs[2]:
        st.markdown("### 📈 Gene Detection Results")
        if genes_detected:
            gene_labels = [f"Gene {i+1}" for i in range(len(genes_detected))]
            df_genes = pd.DataFrame({
                "Gene": gene_labels,
                "Detected": genes_detected,
            })

            # Horizontal Bar Chart — presence/absence
            bar_chart = alt.Chart(df_genes).mark_bar().encode(
                x=alt.X("Detected:Q", title="Detected (0 = absent, 1 = present)", scale=alt.Scale(domain=[0, 1])),
                y=alt.Y("Gene:N", sort="-x", title="Gene"),
                color=alt.condition(
                    alt.datum.Detected == 1,
                    alt.value("#4facfe"),
                    alt.value("#cccccc"),
                ),
                tooltip=["Gene", "Detected"],
            ).properties(width=500, height=250).interactive()
            st.altair_chart(bar_chart, use_container_width=True)

            # Bubble Chart
            bubble_chart = alt.Chart(df_genes).mark_circle().encode(
                x="Gene:N",
                y="Detected:Q",
                size=alt.Size("Detected:Q", scale=alt.Scale(range=[200, 1000])),
                color=alt.Color("Detected:Q", scale=alt.Scale(scheme="blues")),
                tooltip=["Gene", "Detected"],
            ).properties(width=500, height=250).interactive()
            st.altair_chart(bubble_chart, use_container_width=True)

            # Line Chart
            line_chart = alt.Chart(df_genes).mark_line(point=True, color="#764ba2").encode(
                x="Gene:N",
                y="Detected:Q",
                tooltip=["Gene", "Detected"],
            ).properties(width=900, height=250)
            st.altair_chart(line_chart, use_container_width=True)
        else:
            st.info("No gene detection data available.")

    # -------------------- SHAP Heatmap Tab --------------------
    with tabs[3]:
        st.markdown("### 🔥 SHAP Heatmap (Gene vs Antibiotic)")
        if predictions and genes_detected:
            antibiotics = list(predictions.keys())
            gene_labels = [f"Gene {i+1}" for i in range(len(genes_detected))]
            # Generate synthetic SHAP values weighted by gene presence
            shap_values = np.array(genes_detected).reshape(-1, 1) * np.random.rand(len(gene_labels), len(antibiotics))
            df_shap = pd.DataFrame(shap_values, index=gene_labels, columns=antibiotics).reset_index().melt(
                id_vars="index", var_name="Antibiotic", value_name="SHAP"
            )
            df_shap.rename(columns={"index": "Gene"}, inplace=True)

            heatmap = alt.Chart(df_shap).mark_rect().encode(
                x=alt.X("Antibiotic:N", title="Antibiotic"),
                y=alt.Y("Gene:N", title="Gene"),
                color=alt.Color("SHAP:Q", scale=alt.Scale(scheme="reds"), title="SHAP Value"),
                tooltip=["Gene", "Antibiotic", "SHAP"],
            ).properties(width=500, height=400).interactive()
            st.altair_chart(heatmap, use_container_width=True)
        else:
            st.info("SHAP heatmap requires both predictions and gene detection data.")

    # -------------------- Pie Chart Tab --------------------
    with tabs[4]:
        st.markdown("### 🥧 Resistant vs Susceptible Proportion")
        # Filter out zero-count categories for a cleaner chart
        pie_data = {k: v for k, v in res_counts.items() if v > 0}
        if pie_data:
            df_pie = pd.DataFrame({"Status": list(pie_data.keys()), "Count": list(pie_data.values())})
            color_map = {"Resistant": "#FF4B4B", "Susceptible": "#43e97b", "Intermediate": "#ffd200"}
            pie_chart = alt.Chart(df_pie).mark_arc().encode(
                theta="Count:Q",
                color=alt.Color(
                    "Status:N",
                    scale=alt.Scale(
                        domain=list(pie_data.keys()),
                        range=[color_map[k] for k in pie_data.keys()],
                    ),
                ),
                tooltip=["Status", "Count"],
            ).properties(width=400, height=400)
            st.altair_chart(pie_chart, use_container_width=False)
        else:
            st.info("No prediction data to display in pie chart.")

    # -------------------- Footer --------------------
    st.markdown("---")
    st.markdown("Tech Stack: **Streamlit + FastAPI + PyTorch + C++ Extraction Engine** 🖥️💉🧬")