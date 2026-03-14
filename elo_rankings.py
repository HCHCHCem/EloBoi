import pandas as pd

# --- ELO Configuration ---
STARTING_ELO = 1000
K_FACTOR = 40  # Higher K = more volatile ratings per game

def expected_score(rating_a, rating_b):
    """Probability that A beats B."""
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

def update_elo(winners, losers, ratings):
    """Update ELO for a team game. Uses average team ELO for expected score."""
    avg_winner_elo = sum(ratings[p] for p in winners) / len(winners)
    avg_loser_elo = sum(ratings[p] for p in losers) / len(losers)

    exp_win = expected_score(avg_winner_elo, avg_loser_elo)
    exp_lose = expected_score(avg_loser_elo, avg_winner_elo)

    for p in winners:
        ratings[p] += K_FACTOR * (1 - exp_win)
    for p in losers:
        ratings[p] += K_FACTOR * (0 - exp_lose)

    return ratings

def parse_players(cell):
    """Parse comma-separated player names from a cell."""
    if pd.isna(cell):
        return []
    return [name.strip() for name in str(cell).split(",") if name.strip()]

def main():
    df = pd.read_excel("Footy Wins MASTER.xlsx", sheet_name="Games")

    ratings = {}
    game_log = []

    for _, row in df.iterrows():
        winners = parse_players(row["Winners (comma-separated)"])
        losers = parse_players(row["Losers (comma-separated)"])

        # Skip games with no result (empty, draw, or missing data)
        if not winners or not losers or str(row["Winners (comma-separated)"]).strip() == "Draw":
            continue

        # Initialise new players at starting ELO
        for p in winners + losers:
            if p not in ratings:
                ratings[p] = STARTING_ELO

        ratings = update_elo(winners, losers, ratings)

        game_log.append({
            "game": row["Game"],
            "date": row["Date"],
            "winners": ", ".join(winners),
            "losers": ", ".join(losers),
            "snapshot": dict(ratings),
        })

    # --- Print Rankings ---
    print("=" * 55)
    print(f"{'PLAYER ELO RANKINGS':^55}")
    print(f"{'(after ' + str(len(game_log)) + ' games)':^55}")
    print("=" * 55)
    print(f"{'Rank':<6}{'Player':<14}{'ELO':>8}{'W':>5}{'L':>5}{'GP':>5}")
    print("-" * 55)

    # Count wins/losses per player
    wins = {}
    losses = {}
    for entry in game_log:
        for p in entry["winners"].split(", "):
            wins[p] = wins.get(p, 0) + 1
        for p in entry["losers"].split(", "):
            losses[p] = losses.get(p, 0) + 1

    sorted_players = sorted(ratings.items(), key=lambda x: x[1], reverse=True)
    for rank, (player, elo) in enumerate(sorted_players, 1):
        w = wins.get(player, 0)
        l = losses.get(player, 0)
        gp = w + l
        print(f"{rank:<6}{player:<14}{elo:>8.1f}{w:>5}{l:>5}{gp:>5}")

    print("=" * 55)

    # --- Export to Excel ---
    rows = []
    for rank, (player, elo) in enumerate(sorted_players, 1):
        w = wins.get(player, 0)
        l = losses.get(player, 0)
        rows.append({
            "Rank": rank,
            "Player": player,
            "ELO": round(elo, 1),
            "Wins": w,
            "Losses": l,
            "Games Played": w + l,
            "Win %": f"{w / (w + l) * 100:.0f}%" if (w + l) > 0 else "0%",
        })

    out = pd.DataFrame(rows)
    out.to_excel("ELO Rankings.xlsx", index=False, sheet_name="ELO Rankings")
    print(f"\nRankings saved to: ELO Rankings.xlsx")

    # --- Print Game-by-Game History ---
    print(f"\n{'GAME-BY-GAME ELO PROGRESSION':^55}")
    print("=" * 55)
    for entry in game_log:
        print(f"\nGame {entry['game']} ({entry['date']})")
        print(f"  W: {entry['winners']}")
        print(f"  L: {entry['losers']}")
        # Show ELO for players in this game only
        all_in_game = entry["winners"].split(", ") + entry["losers"].split(", ")
        for p in all_in_game:
            print(f"    {p:<14} -> {entry['snapshot'][p]:.1f}")

if __name__ == "__main__":
    main()
