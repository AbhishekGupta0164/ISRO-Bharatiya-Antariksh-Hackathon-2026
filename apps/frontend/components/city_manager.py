"""
🏙️ City Manager — Streamlit component for managing cities.
Just type a city name and everything is handled automatically!
"""

import streamlit as st
from services.api_client import (
    add_road,
    fetch_graph,
    remove_city,
    remove_road,
    reset_graph,
    smart_add_city,
)


def render_city_manager():
    st.markdown(
        '<div class="section-header">🏙️ City & Road Manager</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="color: #94a3b8; margin-bottom: 24px;">'
        'Just type a city name — coordinates, Node ID, and road connections '
        'are all handled automatically. Changes take effect immediately.'
        '</p>',
        unsafe_allow_html=True,
    )

    # ── Fetch current graph ──
    graph = fetch_graph()
    if graph is None:
        st.error("⚠️ Cannot load graph data. Make sure the backend is running.")
        return

    cities = graph.get("cities", {})
    roads = graph.get("roads", [])

    # ══════════════════════════════════════════
    # SMART ADD — JUST TYPE A CITY NAME
    # ══════════════════════════════════════════
    st.markdown(
        """
        <div class="best-route-card" style="margin-bottom: 24px;">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                <span style="font-size: 1.4rem;">🌍</span>
                <span style="font-weight: 700; color: #34d399; font-size: 1.1rem;">Quick Add City</span>
            </div>
            <div style="color: #94a3b8; font-size: 0.88rem;">
                Type any city name — we'll auto-detect its location and connect it to nearby cities in the network.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("smart_add_form", clear_on_submit=True):
        new_city = st.text_input(
            "🏙️ City Name",
            placeholder="e.g. Mumbai, Chennai, Hyderabad, Pune...",
            help="Just type the city name. Coordinates, Node ID, and road connections are auto-generated.",
        )
        submitted = st.form_submit_button(
            "⚡  Add City Automatically", use_container_width=True
        )

        if submitted:
            if not new_city.strip():
                st.warning("Please enter a city name.")
            else:
                with st.spinner(f"🔍 Looking up '{new_city.strip()}'... geocoding & connecting..."):
                    result = smart_add_city(new_city.strip())

                if result.get("status") == "success":
                    st.success(f"✅ **{result['city_name']}** added as node **{result['node_id']}**")

                    # Show what was auto-created
                    roads_added = result.get("roads_added", [])
                    if roads_added:
                        road_summary = ""
                        for r in roads_added:
                            road_summary += (
                                f'<div style="display: flex; justify-content: space-between; '
                                f'padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.04);">'
                                f'<span style="color: #f1f5f9;">{result["city_name"]} → {r["to_name"]}</span>'
                                f'<span style="color: #94a3b8;">{r["distance_km"]} km · AQI {r["pollution"]}</span>'
                                f'</div>'
                            )
                        st.markdown(
                            f"""
                            <div class="glass-card" style="margin-top: 12px;">
                                <div style="color: #64748b; font-size: 0.72rem; text-transform: uppercase;
                                            letter-spacing: 0.05em; margin-bottom: 10px;">
                                    🔗 Auto-connected Roads
                                </div>
                                {road_summary}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    # Show coordinates
                    st.markdown(
                        f"""
                        <div class="glass-card" style="margin-top: 8px; padding: 14px;">
                            <span style="color: #64748b; font-size: 0.78rem;">📍 Coordinates: </span>
                            <span style="color: #94a3b8;">{result['lat']:.4f}, {result['lng']:.4f}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    st.rerun()
                else:
                    detail = result.get("detail", result.get("message", "Unknown error"))
                    st.error(f"❌ {detail}")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Stats row ──
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        st.markdown(
            f"""
            <div class="glass-card" style="text-align: center;">
                <div style="font-size: 2rem; margin-bottom: 8px;">🏙️</div>
                <div style="color: #94a3b8; font-size: 0.78rem; text-transform: uppercase;
                            letter-spacing: 0.05em;">Cities</div>
                <div style="font-weight: 700; font-size: 1.4rem; color: #34d399;
                            margin-top: 4px;">{len(cities)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_s2:
        st.markdown(
            f"""
            <div class="glass-card" style="text-align: center;">
                <div style="font-size: 2rem; margin-bottom: 8px;">🛤️</div>
                <div style="color: #94a3b8; font-size: 0.78rem; text-transform: uppercase;
                            letter-spacing: 0.05em;">Roads</div>
                <div style="font-weight: 700; font-size: 1.4rem; color: #3b82f6;
                            margin-top: 4px;">{len(roads)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_s3:
        used_ids = sorted(cities.keys())
        next_id = _suggest_next_id(used_ids)
        st.markdown(
            f"""
            <div class="glass-card" style="text-align: center;">
                <div style="font-size: 2rem; margin-bottom: 8px;">🆔</div>
                <div style="color: #94a3b8; font-size: 0.78rem; text-transform: uppercase;
                            letter-spacing: 0.05em;">Next Available ID</div>
                <div style="font-weight: 700; font-size: 1.4rem; color: #f59e0b;
                            margin-top: 4px;">{next_id}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Existing Cities Table ──
    st.markdown(
        '<div class="section-header">📍 Current Cities</div>',
        unsafe_allow_html=True,
    )

    if cities:
        table_rows = ""
        for nid, info in sorted(cities.items()):
            table_rows += (f'<tr style="border-bottom: 1px solid rgba(255,255,255,0.04);">'
                f'<td style="padding: 10px; color: #34d399; font-weight: 600;">{nid}</td>'
                f'<td style="padding: 10px; color: #f1f5f9;">{info["name"]}</td>'
                f'<td style="padding: 10px; color: #94a3b8;">{info["lat"]:.4f}</td>'
                f'<td style="padding: 10px; color: #94a3b8;">{info["lng"]:.4f}</td>'
                f'</tr>')
        th_style = 'text-align:left;padding:12px;color:#94a3b8;font-weight:600;font-size:0.8rem;text-transform:uppercase'
        html = (f'<div class="glass-card" style="padding:0;overflow:hidden;">'
            f'<table style="width:100%;border-collapse:collapse;">'
            f'<thead><tr style="border-bottom:1px solid rgba(255,255,255,0.08);">'
            f'<th style="{th_style}">ID</th>'
            f'<th style="{th_style}">City Name</th>'
            f'<th style="{th_style}">Latitude</th>'
            f'<th style="{th_style}">Longitude</th>'
            f'</tr></thead><tbody>{table_rows}</tbody></table></div>')
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.info("No cities in the graph yet.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Existing Roads Table ──
    st.markdown(
        '<div class="section-header">🛤️ Current Roads</div>',
        unsafe_allow_html=True,
    )

    if roads:
        road_rows = ""
        for r in roads:
            from_name = cities.get(r["from"], {}).get("name", r["from"]) if isinstance(cities.get(r["from"]), dict) else r["from"]
            to_name = cities.get(r["to"], {}).get("name", r["to"]) if isinstance(cities.get(r["to"]), dict) else r["to"]
            road_rows += (f'<tr style="border-bottom: 1px solid rgba(255,255,255,0.04);">'
                f'<td style="padding: 10px; color: #34d399; font-weight: 500;">{r["from"]}</td>'
                f'<td style="padding: 10px; color: #3b82f6; font-weight: 500;">{r["to"]}</td>'
                f'<td style="padding: 10px; color: #f1f5f9;">{from_name} → {to_name}</td>'
                f'<td style="padding: 10px; color: #94a3b8;">{r["distance"]} km</td>'
                f'<td style="padding: 10px; color: #f59e0b;">{r["pollution"]}</td>'
                f'</tr>')
        th_style = 'text-align:left;padding:12px;color:#94a3b8;font-weight:600;font-size:0.8rem;text-transform:uppercase'
        html = (f'<div class="glass-card" style="padding:0;overflow:hidden;">'
            f'<table style="width:100%;border-collapse:collapse;">'
            f'<thead><tr style="border-bottom:1px solid rgba(255,255,255,0.08);">'
            f'<th style="{th_style}">From</th>'
            f'<th style="{th_style}">To</th>'
            f'<th style="{th_style}">Route</th>'
            f'<th style="{th_style}">Distance</th>'
            f'<th style="{th_style}">Pollution</th>'
            f'</tr></thead><tbody>{road_rows}</tbody></table></div>')
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.info("No roads in the graph yet.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # MANAGEMENT SECTION (collapsible)
    # ══════════════════════════════════════════
    with st.expander("🔧 Advanced Management", expanded=False):

        # ── Remove City ──
        st.markdown(
            '<div class="section-header">🗑️ Remove City</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p style="color: #64748b; font-size: 0.85rem; margin-bottom: 12px;">'
            '⚠️ Removing a city also deletes all roads connected to it.</p>',
            unsafe_allow_html=True,
        )

        node_list = sorted(cities.keys())
        if node_list:
            city_labels_del = {nid: f"{cities[nid]['name']} ({nid})" for nid in node_list}
            with st.form("remove_city_form"):
                del_city = st.selectbox(
                    "Select city to remove",
                    node_list,
                    format_func=lambda x: city_labels_del[x],
                    key="del_city_sel",
                )
                del_submitted = st.form_submit_button("🗑️  Remove City", use_container_width=True)
                if del_submitted:
                    result = remove_city(del_city)
                    if result.get("status") == "success":
                        st.success(f"✅ {result['message']}")
                        st.rerun()
                    else:
                        detail = result.get("detail", result.get("message", "Unknown error"))
                        st.error(f"❌ {detail}")

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Remove Road ──
        st.markdown(
            '<div class="section-header">✂️ Remove Road</div>',
            unsafe_allow_html=True,
        )

        if roads:
            road_labels = {
                i: f"{r['from']} → {r['to']}  ({cities.get(r['from'], {}).get('name', r['from'])} → {cities.get(r['to'], {}).get('name', r['to'])})"
                for i, r in enumerate(roads)
            }
            with st.form("remove_road_form"):
                road_idx = st.selectbox(
                    "Select road to remove",
                    list(road_labels.keys()),
                    format_func=lambda x: road_labels[x],
                    key="del_road_sel",
                )
                road_del_submitted = st.form_submit_button("✂️  Remove Road", use_container_width=True)
                if road_del_submitted:
                    r = roads[road_idx]
                    result = remove_road(r["from"], r["to"])
                    if result.get("status") == "success":
                        st.success(f"✅ {result['message']}")
                        st.rerun()
                    else:
                        detail = result.get("detail", result.get("message", "Unknown error"))
                        st.error(f"❌ {detail}")
        else:
            st.info("No roads to remove.")

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Add Manual Road ──
        st.markdown(
            '<div class="section-header">🔗 Add Road Manually</div>',
            unsafe_allow_html=True,
        )

        if len(node_list) >= 2:
            city_labels = {nid: f"{cities[nid]['name']} ({nid})" for nid in node_list}
            with st.form("add_road_form", clear_on_submit=True):
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    road_from = st.selectbox(
                        "From City", node_list,
                        format_func=lambda x: city_labels[x], key="road_from",
                    )
                with col_r2:
                    road_to = st.selectbox(
                        "To City", node_list,
                        format_func=lambda x: city_labels[x],
                        index=min(1, len(node_list) - 1), key="road_to",
                    )
                col_r3, col_r4 = st.columns(2)
                with col_r3:
                    road_dist = st.number_input(
                        "Distance (km)", value=100.0, min_value=0.1, step=10.0, format="%.1f"
                    )
                with col_r4:
                    road_poll = st.number_input(
                        "Pollution (AQI)", value=5.0, min_value=0.0, step=0.5, format="%.1f"
                    )
                road_submitted = st.form_submit_button("🛤️  Add Road", use_container_width=True)
                if road_submitted:
                    if road_from == road_to:
                        st.warning("Cannot create a road from a city to itself.")
                    else:
                        result = add_road(road_from, road_to, road_dist, road_poll)
                        if result.get("status") == "success":
                            st.success(f"✅ {result['message']}")
                            st.rerun()
                        else:
                            detail = result.get("detail", result.get("message", "Unknown error"))
                            st.error(f"❌ {detail}")
        else:
            st.info("Add at least 2 cities before creating roads.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # RESET
    # ══════════════════════════════════════════
    st.markdown(
        '<div class="section-header">🔄 Reset to Defaults</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="color: #64748b; font-size: 0.85rem; margin-bottom: 12px;">'
        'This will restore the original 6-city network and remove all custom cities/roads.</p>',
        unsafe_allow_html=True,
    )

    if st.button("🔄  Reset Graph", key="btn_reset_graph", use_container_width=True):
        result = reset_graph()
        if result.get("status") == "success":
            st.success(f"✅ {result['message']}")
            st.rerun()
        else:
            detail = result.get("detail", result.get("message", "Unknown error"))
            st.error(f"❌ {detail}")


def _suggest_next_id(used: list[str]) -> str:
    """Suggest the next available single-letter ID."""
    for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        if c not in used:
            return c
    return "??"
