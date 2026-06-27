import streamlit as st


def render_ai_engine():
    """
    Renders the AI Engine Control Panel tab with model status,
    manual training trigger, and a live training log area.
    """
    st.markdown('<div class="section-header">🤖 AI Engine Control Panel</div>', unsafe_allow_html=True)
    st.markdown(
        '<p style="color: #94a3b8; margin-bottom: 24px;">'
        'Monitor and control the EcoNav AI model. Trigger retraining cycles on demand '
        'and view real-time model performance metrics.'
        '</p>',
        unsafe_allow_html=True,
    )

    # ---- Model Status ----
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            """
            <div class="glass-card" style="text-align: center;">
                <div style="font-size: 2rem; margin-bottom: 8px;">🧠</div>
                <div style="color: #94a3b8; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em;">Model Status</div>
                <div style="font-weight: 700; font-size: 1.1rem; color: #34d399; margin-top: 4px;">
                    <span class="status-dot online"></span> Active
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            """
            <div class="glass-card" style="text-align: center;">
                <div style="font-size: 2rem; margin-bottom: 8px;">⚡</div>
                <div style="color: #94a3b8; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em;">Architecture</div>
                <div style="font-weight: 700; font-size: 1.1rem; color: #f1f5f9; margin-top: 4px;">
                    Weighted Score Model
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            """
            <div class="glass-card" style="text-align: center;">
                <div style="font-size: 2rem; margin-bottom: 8px;">🔄</div>
                <div style="color: #94a3b8; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em;">Hot-Reload</div>
                <div style="font-weight: 700; font-size: 1.1rem; color: #34d399; margin-top: 4px;">
                    Enabled
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ---- Decision Pipeline Diagram ----
    st.markdown('<div class="section-header">🏗️ Decision Pipeline</div>', unsafe_allow_html=True)

    arch_dot = """
    digraph Pipeline {
        rankdir=LR;
        bgcolor="transparent";
        node [shape=record, style="rounded,filled", fontname="Inter", fontsize=10,
              fillcolor="#1e293b", fontcolor="#e2e8f0", color="#334155", penwidth=1.5];
        edge [color="#475569", penwidth=1.2, arrowsize=0.8];

        input [label="{Input|start, end nodes}", fillcolor="#064e3b", color="#10b981", fontcolor="#34d399"];
        graph [label="{Graph Engine|Build city network}"];
        rl [label="{RL Agent|Explore paths}"];
        scorer [label="{Eco Scorer|distance × pollution}"];
        output [label="{Output|Eco Route + Metrics}", fillcolor="#1e1b4b", color="#6366f1", fontcolor="#a5b4fc"];

        input -> graph -> rl -> scorer -> output;
    }
    """
    st.graphviz_chart(arch_dot, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ---- Manual Training Trigger ----
    st.markdown('<div class="section-header">🎯 Manual Training</div>', unsafe_allow_html=True)

    if "training_log" not in st.session_state:
        st.session_state.training_log = []

    if st.button("🚀 Trigger Model Retraining", key="btn_train", use_container_width=True):
        with st.spinner("Running ML training pipeline & hot-reloading weights…"):
            from services.api_client import trigger_training
            result = trigger_training()

            if result.get("status") == "success":
                st.session_state.training_log.append("✅ " + result.get("message", "Training completed."))
                st.success(result["message"])
            else:
                st.session_state.training_log.append("❌ " + result.get("message", "Unknown error."))
                st.error(result.get("message", "Training failed."))

    if st.session_state.training_log:
        st.markdown('<div class="section-header">📋 Training Log</div>', unsafe_allow_html=True)
        log_html = "<div class='training-log'>"
        for entry in st.session_state.training_log:
            log_html += f"<div>{entry}</div>"
        log_html += "</div>"
        st.markdown(log_html, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ---- Weight Info ----
    st.markdown('<div class="section-header">📊 Model Weights</div>', unsafe_allow_html=True)

    weights_html = """
    <div class="glass-card">
        <table style="width: 100%; border-collapse: collapse;">
            <thead>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.08);">
                    <th style="text-align: left; padding: 10px; color: #94a3b8; font-weight: 600; font-size: 0.8rem; text-transform: uppercase;">Weight</th>
                    <th style="text-align: left; padding: 10px; color: #94a3b8; font-weight: 600; font-size: 0.8rem; text-transform: uppercase;">Default</th>
                    <th style="text-align: left; padding: 10px; color: #94a3b8; font-weight: 600; font-size: 0.8rem; text-transform: uppercase;">Description</th>
                </tr>
            </thead>
            <tbody>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.04);">
                    <td style="padding: 10px; color: #34d399; font-weight: 500;">distance_weight</td>
                    <td style="padding: 10px; color: #94a3b8;">0.15</td>
                    <td style="padding: 10px; color: #94a3b8;">How much route length matters</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.04);">
                    <td style="padding: 10px; color: #3b82f6; font-weight: 500;">pollution_weight</td>
                    <td style="padding: 10px; color: #94a3b8;">0.45</td>
                    <td style="padding: 10px; color: #94a3b8;">How much AQI pollution matters</td>
                </tr>
                <tr>
                    <td style="padding: 10px; color: #f59e0b; font-weight: 500;">exposure_weight</td>
                    <td style="padding: 10px; color: #94a3b8;">0.40</td>
                    <td style="padding: 10px; color: #94a3b8;">Cumulative exposure penalty</td>
                </tr>
            </tbody>
        </table>
    </div>
    """
    st.markdown(weights_html, unsafe_allow_html=True)
