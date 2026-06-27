import random

import streamlit as st


def render_environment_manager():
    """
    Renders the Environment Manager tab where users can manually add,
    view, and remove custom places from the routing graph.
    """
    st.markdown('<div class="section-header">🌍 Manage Your Environment</div>', unsafe_allow_html=True)
    st.markdown(
        '<p style="color: #94a3b8; margin-bottom: 24px;">'
        'Add, view, and remove places that form the routing network. '
        'These places will be used as waypoints when finding eco-friendly routes.'
        '</p>',
        unsafe_allow_html=True,
    )

    # Initialize session state for places
    if "custom_places" not in st.session_state:
        st.session_state.custom_places = [
            {"name": "Home", "traffic": "Low", "pollution": "Low"},
            {"name": "Downtown", "traffic": "High", "pollution": "High"},
            {"name": "Central Park", "traffic": "Low", "pollution": "Low"},
            {"name": "Industrial Zone", "traffic": "Medium", "pollution": "High"},
            {"name": "Office", "traffic": "Medium", "pollution": "Medium"},
        ]

    # ---- Add Place Form ----
    st.markdown('<div class="section-header">➕ Add a New Place</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        new_name = st.text_input("Place Name", placeholder="e.g. Riverside Park", key="add_place_name")
    with col2:
        new_traffic = st.selectbox("Base Traffic", ["Low", "Medium", "High"], key="add_place_traffic")
    with col3:
        new_pollution = st.selectbox("Base Pollution (AQI)", ["Low", "Medium", "High"], key="add_place_pollution")

    add_clicked = st.button("Add Place", key="btn_add_place", use_container_width=True)
    if add_clicked:
        if new_name.strip():
            existing_names = [p["name"].lower() for p in st.session_state.custom_places]
            if new_name.strip().lower() in existing_names:
                st.warning(f"⚠️ A place named **{new_name.strip()}** already exists.")
            else:
                st.session_state.custom_places.append({
                    "name": new_name.strip(),
                    "traffic": new_traffic,
                    "pollution": new_pollution,
                })
                st.success(f"✅ **{new_name.strip()}** added to the environment!")
                st.rerun()
        else:
            st.warning("Please enter a place name.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ---- Display Existing Places ----
    st.markdown('<div class="section-header">📍 Current Places</div>', unsafe_allow_html=True)

    if not st.session_state.custom_places:
        st.info("No places added yet. Add your first place above!")
    else:
        for idx, place in enumerate(st.session_state.custom_places):
            traffic_color = {"Low": "#10b981", "Medium": "#f59e0b", "High": "#ef4444"}.get(place["traffic"], "#94a3b8")
            pollution_color = {"Low": "#10b981", "Medium": "#f59e0b", "High": "#ef4444"}.get(place["pollution"], "#94a3b8")

            place_html = f"""
            <div class="place-card">
                <div>
                    <div class="place-name">📍 {place['name']}</div>
                    <div class="place-meta" style="margin-top: 4px;">
                        <span style="color: {traffic_color};">● Traffic: {place['traffic']}</span>
                        &nbsp;&nbsp;
                        <span style="color: {pollution_color};">● Pollution: {place['pollution']}</span>
                    </div>
                </div>
            </div>
            """
            st.markdown(place_html, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Remove place
        remove_name = st.selectbox(
            "Remove a place",
            options=[""] + [p["name"] for p in st.session_state.custom_places],
            key="remove_place_select",
        )
        if st.button("Remove Selected Place", key="btn_remove_place"):
            if remove_name:
                st.session_state.custom_places = [
                    p for p in st.session_state.custom_places if p["name"] != remove_name
                ]
                st.success(f"🗑️ **{remove_name}** removed.")
                st.rerun()


def get_place_names():
    """Returns the list of user-defined place names for use in routing."""
    if "custom_places" not in st.session_state:
        return ["A", "B", "C", "D", "E"]
    names = [p["name"] for p in st.session_state.custom_places]
    return names if names else ["A", "B", "C", "D", "E"]


def build_routes_from_places(source: str, destination: str):
    """
    Builds mock routes between source and destination using
    intermediate places from the session state for the waypoints.
    """
    places = get_place_names()
    intermediates = [p for p in places if p != source and p != destination]

    traffic_map = {}
    pollution_map = {}
    if "custom_places" in st.session_state:
        for p in st.session_state.custom_places:
            t = {"Low": 2, "Medium": 5, "High": 8}.get(p["traffic"], 3)
            q = {"Low": 30, "Medium": 100, "High": 250}.get(p["pollution"], 50)
            traffic_map[p["name"]] = t
            pollution_map[p["name"]] = q

    routes = []
    # Direct route
    avg_traffic = (traffic_map.get(source, 3) + traffic_map.get(destination, 3)) // 2
    routes.append({
        "path": [source, destination],
        "distance": random.randint(5, 12),
        "traffic": avg_traffic,
        "fuel": 0,
    })

    # Routes through single intermediates (up to 4)
    random.shuffle(intermediates)
    for mid in intermediates[:4]:
        avg_t = (traffic_map.get(source, 3) + traffic_map.get(mid, 4) + traffic_map.get(destination, 3)) // 3
        routes.append({
            "path": [source, mid, destination],
            "distance": random.randint(8, 20),
            "traffic": avg_t,
            "fuel": 0,
        })

    # One route through two intermediates (if enough places)
    if len(intermediates) >= 2:
        pair = random.sample(intermediates[:4], 2)
        avg_t = sum(traffic_map.get(n, 4) for n in [source] + pair + [destination]) // 4
        routes.append({
            "path": [source, pair[0], pair[1], destination],
            "distance": random.randint(14, 25),
            "traffic": avg_t,
            "fuel": 0,
        })

    return routes
