import os

import altair as alt
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from matplotlib.patches import Arc, Circle, Rectangle

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


@st.cache_data(show_spinner=False)
def load_csv(filename: str) -> pd.DataFrame:
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing data file: {path}")
    return pd.read_csv(path)


@st.cache_data(show_spinner=False)
def load_player_options():
    seasons = load_csv("fct_player_season_averages.csv")
    players = load_csv("raw_nba_players.csv")

    df = seasons[["player_id"]].drop_duplicates().merge(
        players[["player_id", "full_name"]],
        on="player_id",
        how="left",
    )

    df["player_name"] = df["full_name"].fillna("Player " + df["player_id"].astype(str))
    df = df[["player_id", "player_name"]].sort_values("player_name")
    df.columns = ["PLAYER_ID", "PLAYER_NAME"]
    return df


@st.cache_data(show_spinner=False)
def load_seasons_for_player(player_id):
    df = load_csv("fct_player_season_averages.csv")
    seasons = df[df["player_id"] == player_id]["season"].dropna().unique().tolist()
    return sorted(seasons)


@st.cache_data(show_spinner=False)
def get_season_stats(player_id, season):
    df = load_csv("fct_player_season_averages.csv")
    df = df[(df["player_id"] == player_id) & (df["season"] == season)].copy()

    display_cols = [
        "season", "games_played", "pts_per_game", "reb_per_game",
        "ast_per_game", "fgm_per_game", "fga_per_game",
        "fg3m_per_game", "fg3a_per_game", "ftm_per_game",
        "fta_per_game", "plus_minus_avg", "fg_pts_per_fga",
    ]

    df = df[[c for c in display_cols if c in df.columns]]
    df.columns = [c.upper() for c in df.columns]

    df = df.rename(columns={
        "SEASON": "Season",
        "GAMES_PLAYED": "Games",
        "PTS_PER_GAME": "PPG",
        "REB_PER_GAME": "RPG",
        "AST_PER_GAME": "APG",
        "FGM_PER_GAME": "FGM/G",
        "FGA_PER_GAME": "FGA/G",
        "FG3M_PER_GAME": "3PM/G",
        "FG3A_PER_GAME": "3PA/G",
        "FTM_PER_GAME": "FTM/G",
        "FTA_PER_GAME": "FTA/G",
        "PLUS_MINUS_AVG": "+/-",
        "FG_PTS_PER_FGA": "Pts/FGA",
    })

    return df


@st.cache_data(show_spinner=False)
def get_zone_stats(player_id, season):
    df = load_csv("fct_shooting_zone.csv")
    df = df[(df["player_id"] == player_id) & (df["season"] == season)].copy()
    df = df.sort_values(["shot_zone_basic", "shot_zone_area"])
    df.columns = [c.upper() for c in df.columns]
    return df


@st.cache_data(show_spinner=False)
def get_shot_locations(player_id, season):
    df = load_csv("fct_player_shot_locations.csv")
    df = df[(df["player_id"] == player_id) & (df["season"] == season)].copy()
    df = df[["loc_x", "loc_y", "shot_made_flag"]]
    df.columns = [c.upper() for c in df.columns]
    return df


def draw_half_court(ax=None):
    if ax is None:
        ax = plt.gca()

    ax.add_patch(Circle((0, 0), radius=7.5, fill=False))
    ax.add_patch(Rectangle((-30, -7.5), 60, 1, fill=False))
    ax.add_patch(Rectangle((-80, -47.5), 160, 190, fill=False))
    ax.add_patch(Rectangle((-60, -47.5), 120, 190, fill=False))
    ax.add_patch(Arc((0, 142.5), 120, 120, theta1=0, theta2=180, fill=False))
    ax.add_patch(Rectangle((-220, -47.5), 0, 140, fill=False))
    ax.add_patch(Rectangle((220, -47.5), 0, 140, fill=False))
    ax.add_patch(Arc((0, 0), 475, 475, theta1=22, theta2=158, fill=False))

    ax.set_xlim(-250, 250)
    ax.set_ylim(-47.5, 422.5)
    ax.set_aspect("equal")
    ax.axis("off")
    return ax


def render_shot_chart(df, title: str):
    if df.empty:
        st.info(f"No shot location data for {title}.")
        return

    made = df[df["SHOT_MADE_FLAG"] == 1]
    missed = df[df["SHOT_MADE_FLAG"] == 0]

    fig, ax = plt.subplots(figsize=(4, 3.5))
    draw_half_court(ax)

    ax.scatter(missed["LOC_X"], missed["LOC_Y"], s=8, alpha=0.3, color="red", label="Miss")
    ax.scatter(made["LOC_X"], made["LOC_Y"], s=12, alpha=0.75, color="green", label="Make")

    ax.legend(loc="upper right", fontsize=7)
    ax.set_title(title, fontsize=9)
    st.pyplot(fig, use_container_width=False)

def render_zone_heatmap(df, title: str):
    if df.empty:
        st.info(f"No zone stats available for {title}.")
        return

    df = df.copy()
    df.columns = [c.lower() for c in df.columns]

    area_labels = {
        "Back Court(BC)": "Back",
        "Center(C)": "Center",
        "Left Side Center(LC)": "L Center",
        "Left Side(L)": "L Wing",
        "Right Side Center(RC)": "R Center",
        "Right Side(R)": "R Wing",
    }

    df["shot_zone_area_clean"] = df["shot_zone_area"].replace(area_labels)

    df = df[df["shot_zone_area_clean"] != "Back"]
    df = df[df["fga"] >= 10]

    if df.empty:
        st.info(f"No zones with at least 10 attempts for {title}.")
        return

    chart = (
        alt.Chart(df)
        .mark_rect()
        .encode(
            x=alt.X(
                "shot_zone_area_clean:N",
                sort=[
                    "L Wing",
                    "L Center",
                    "Center",
                    "R Center",
                    "R Wing",
                ],
                title="Area",
                axis=alt.Axis(
                    labelAngle=-15,
                    labelPadding=10,
                    labelOverlap=False,
                ),
            ),
            y=alt.Y(
                "shot_zone_basic:N",
                title="Zone",
                axis=alt.Axis(labelLimit=220),
            ),
            color=alt.Color(
                "pct_diff:Q",
                title="FG% vs Player Pool",
                scale=alt.Scale(scheme="redyellowgreen"),
                legend=alt.Legend(format="+.0%"),
            ),
            tooltip=[
                alt.Tooltip("shot_zone_basic:N", title="Zone"),
                alt.Tooltip("shot_zone_area_clean:N", title="Area"),
                alt.Tooltip("fg_pct:Q", format=".1%", title="Player FG%"),
                alt.Tooltip("league_fg_pct:Q", format=".1%", title="Player Pool FG%"),
                alt.Tooltip("pct_diff:Q", format="+.1%", title="Diff vs Player Pool"),
                alt.Tooltip("fga:Q", title="Player FGA"),
            ],
        )
        .properties(
            title=title,
            width=550,
            height=260,
        )
    )

    st.altair_chart(chart, use_container_width=True)

def show_metric_cards(stats_df):
    if stats_df.empty:
        return

    row = stats_df.iloc[0]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Games", row.get("Games", "N/A"))
    col2.metric("PPG", row.get("PPG", "N/A"))
    col3.metric("RPG", row.get("RPG", "N/A"))
    col4.metric("APG", row.get("APG", "N/A"))

def main():
    st.set_page_config(page_title="NBA Shooting Comparison", layout="wide")

    st.title("NBA Player Shooting Comparison")

    with st.sidebar:
        st.header("Project Overview")

        st.write(
            """
            Interactive NBA analytics dashboard for comparing
            player performance across seasons.

            **Features**
            - Season-level statistics
            - Shot location visualization
            - Shooting efficiency vs Player Pool average
            - Player-to-player comparison

            **Tech Stack**
            - Python
            - NBA API
            - dbt
            - Snowflake
            - Streamlit
            """
        )
    try:
        players = load_player_options()
    except FileNotFoundError as e:
        st.error(str(e))
        st.info("Make sure the required CSV files are inside the `data/` folder next to `app.py`.")
        return

    if players.empty:
        st.error("No players found in fct_player_season_averages.csv.")
        return

    player_dict = {
        f"{row['PLAYER_NAME']} ({row['PLAYER_ID']})": int(row["PLAYER_ID"])
        for _, row in players.iterrows()
    }

    col_sel_a, col_sel_b = st.columns(2)

    with col_sel_a:
        st.subheader("Player A")
        player_label_a = st.selectbox("Player A", list(player_dict.keys()), key="player_a")
        player_id_a = player_dict[player_label_a]
        seasons_a = load_seasons_for_player(player_id_a)
        season_a = st.selectbox("Season A", seasons_a, key="season_a")

    with col_sel_b:
        st.subheader("Player B")
        player_label_b = st.selectbox("Player B", list(player_dict.keys()), key="player_b")
        player_id_b = player_dict[player_label_b]
        seasons_b = load_seasons_for_player(player_id_b)
        season_b = st.selectbox("Season B", seasons_b, key="season_b")

    stats_a = get_season_stats(player_id_a, season_a)
    stats_b = get_season_stats(player_id_b, season_b)

    st.markdown("## Season Stats Comparison")

    col_stats_a, col_stats_b = st.columns(2)

    with col_stats_a:
        st.markdown(f"**{player_label_a} — {season_a}**")
        show_metric_cards(stats_a)
        if not stats_a.empty:
            st.dataframe(stats_a, use_container_width=True, hide_index=True)
        else:
            st.info("No stats for this player/season.")

    with col_stats_b:
        st.markdown(f"**{player_label_b} — {season_b}**")
        show_metric_cards(stats_b)
        if not stats_b.empty:
            st.dataframe(stats_b, use_container_width=True, hide_index=True)
        else:
            st.info("No stats for this player/season.")

    st.markdown("## Zone FG% vs Player Pool")

    zones_a = get_zone_stats(player_id_a, season_a)
    zones_b = get_zone_stats(player_id_b, season_b)

    col_zone_a, col_zone_b = st.columns(2)

    with col_zone_a:
        render_zone_heatmap(zones_a, f"{player_label_a} — {season_a}")

    with col_zone_b:
        render_zone_heatmap(zones_b, f"{player_label_b} — {season_b}")

    st.markdown("## Shot Location Charts")

    shots_a = get_shot_locations(player_id_a, season_a)
    shots_b = get_shot_locations(player_id_b, season_b)

    col_shot_a, col_shot_b = st.columns(2)

    with col_shot_a:
        render_shot_chart(shots_a, f"{player_label_a} — {season_a}")

    with col_shot_b:
        render_shot_chart(shots_b, f"{player_label_b} — {season_b}")


if __name__ == "__main__":
    main()