"""Fetch anime data from AniList and Jikan APIs."""

import requests
import json
import time
from pathlib import Path
from typing import List, Dict, Any
from rich.console import Console
from rich.progress import track

console = Console()


class AnimeDataFetcher:
    """Fetch anime data from various APIs."""

    def __init__(self, data_dir: str = "data/anime"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # API endpoints
        self.anilist_url = "https://graphql.anilist.co"
        self.jikan_base_url = "https://api.jikan.moe/v4"

    def fetch_from_jikan(
        self,
        max_anime: int = 100,
        min_score: float = 7.0
    ) -> List[Dict[str, Any]]:
        """
        Fetch anime data from Jikan API (MyAnimeList).

        Args:
            max_anime: Maximum number of anime to fetch
            min_score: Minimum score filter

        Returns:
            List of anime data dictionaries
        """
        console.print(f"[cyan]Fetching anime data from Jikan API...[/cyan]")

        anime_list = []
        page = 1

        while len(anime_list) < max_anime:
            try:
                # Fetch top anime page
                url = f"{self.jikan_base_url}/top/anime"
                params = {
                    "page": page,
                    "limit": 25,
                    "min_score": min_score
                }

                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                if not data.get("data"):
                    break

                for anime in data["data"]:
                    if len(anime_list) >= max_anime:
                        break

                    anime_data = self._parse_jikan_anime(anime)
                    anime_list.append(anime_data)

                    console.print(f"  ✓ Fetched: {anime_data['title']}")

                page += 1
                time.sleep(1)  # Rate limiting (3 requests/second max)

            except Exception as e:
                console.print(f"[red]Error fetching page {page}: {e}[/red]")
                break

        console.print(f"[green]✓ Fetched {len(anime_list)} anime from Jikan[/green]")
        return anime_list

    def _parse_jikan_anime(self, anime: Dict) -> Dict[str, Any]:
        """Parse Jikan API anime response."""
        return {
            "id": anime["mal_id"],
            "title": anime["title"],
            "title_english": anime.get("title_english"),
            "title_japanese": anime.get("title_japanese"),
            "type": anime.get("type"),
            "episodes": anime.get("episodes"),
            "status": anime.get("status"),
            "aired_from": anime.get("aired", {}).get("from"),
            "aired_to": anime.get("aired", {}).get("to"),
            "score": anime.get("score"),
            "scored_by": anime.get("scored_by"),
            "rank": anime.get("rank"),
            "popularity": anime.get("popularity"),
            "synopsis": anime.get("synopsis", ""),
            "genres": [g["name"] for g in anime.get("genres", [])],
            "themes": [t["name"] for t in anime.get("themes", [])],
            "demographics": [d["name"] for d in anime.get("demographics", [])],
            "studios": [s["name"] for s in anime.get("studios", [])],
            "image_url": anime.get("images", {}).get("jpg", {}).get("large_image_url"),
            "url": anime.get("url"),
            "year": anime.get("year"),
            "season": anime.get("season"),
            "source": anime.get("source"),
        }

    def fetch_anime_details(self, anime_id: int, source: str = "jikan") -> Dict[str, Any]:
        """Fetch detailed information for a specific anime."""
        if source == "jikan":
            return self._fetch_jikan_details(anime_id)
        # TODO: Add AniList support

    def _fetch_jikan_details(self, anime_id: int) -> Dict[str, Any]:
        """Fetch detailed anime info including characters and staff."""
        try:
            # Get anime details
            url = f"{self.jikan_base_url}/anime/{anime_id}/full"
            response = requests.get(url)
            response.raise_for_status()
            anime = response.json()["data"]

            time.sleep(0.4)  # Rate limiting

            # Get characters
            char_url = f"{self.jikan_base_url}/anime/{anime_id}/characters"
            char_response = requests.get(char_url)
            characters = char_response.json().get("data", [])

            time.sleep(0.4)

            # Get recommendations
            rec_url = f"{self.jikan_base_url}/anime/{anime_id}/recommendations"
            rec_response = requests.get(rec_url)
            recommendations = rec_response.json().get("data", [])

            return {
                **self._parse_jikan_anime(anime),
                "characters": [
                    {
                        "id": c["character"]["mal_id"],
                        "name": c["character"]["name"],
                        "role": c["role"],
                        "image_url": c["character"]["images"]["jpg"]["image_url"],
                        "voice_actors": [
                            {
                                "id": va["person"]["mal_id"],
                                "name": va["person"]["name"],
                                "language": va["language"]
                            }
                            for va in c.get("voice_actors", [])
                        ]
                    }
                    for c in characters[:10]  # Limit to top 10 characters
                ],
                "recommendations": [
                    {
                        "id": r["entry"]["mal_id"],
                        "title": r["entry"]["title"],
                        "votes": r["votes"]
                    }
                    for r in recommendations[:10]
                ]
            }

        except Exception as e:
            console.print(f"[red]Error fetching details for anime {anime_id}: {e}[/red]")
            return {}

    def fetch_from_anilist(
        self,
        max_anime: int = 100,
        min_score: int = 70
    ) -> List[Dict[str, Any]]:
        """
        Fetch anime data from AniList GraphQL API.

        Args:
            max_anime: Maximum number of anime to fetch
            min_score: Minimum average score (0-100)

        Returns:
            List of anime data dictionaries
        """
        console.print(f"[cyan]Fetching anime data from AniList API...[/cyan]")

        query = '''
        query ($page: Int, $perPage: Int, $minScore: Int) {
          Page(page: $page, perPage: $perPage) {
            pageInfo {
              hasNextPage
            }
            media(type: ANIME, averageScore_greater: $minScore, sort: SCORE_DESC) {
              id
              title {
                romaji
                english
                native
              }
              description
              episodes
              averageScore
              popularity
              genres
              studios {
                nodes {
                  name
                }
              }
              characters(perPage: 5, sort: ROLE) {
                nodes {
                  id
                  name {
                    full
                  }
                }
              }
              relations {
                edges {
                  relationType
                  node {
                    id
                    title {
                      romaji
                    }
                  }
                }
              }
              recommendations(perPage: 5, sort: RATING_DESC) {
                nodes {
                  mediaRecommendation {
                    id
                    title {
                      romaji
                    }
                  }
                  rating
                }
              }
            }
          }
        }
        '''

        anime_list = []
        page = 1

        while len(anime_list) < max_anime:
            variables = {
                "page": page,
                "perPage": 50,
                "minScore": min_score
            }

            try:
                response = requests.post(
                    self.anilist_url,
                    json={"query": query, "variables": variables}
                )
                response.raise_for_status()
                data = response.json()

                media_list = data["data"]["Page"]["media"]

                if not media_list:
                    break

                for anime in media_list:
                    if len(anime_list) >= max_anime:
                        break

                    anime_data = self._parse_anilist_anime(anime)
                    anime_list.append(anime_data)

                    console.print(f"  ✓ Fetched: {anime_data['title']}")

                if not data["data"]["Page"]["pageInfo"]["hasNextPage"]:
                    break

                page += 1
                time.sleep(0.6)  # Rate limiting (90 requests/minute)

            except Exception as e:
                console.print(f"[red]Error fetching page {page}: {e}[/red]")
                break

        console.print(f"[green]✓ Fetched {len(anime_list)} anime from AniList[/green]")
        return anime_list

    def _parse_anilist_anime(self, anime: Dict) -> Dict[str, Any]:
        """Parse AniList API anime response."""
        return {
            "id": anime["id"],
            "title": anime["title"]["romaji"],
            "title_english": anime["title"].get("english"),
            "title_japanese": anime["title"].get("native"),
            "synopsis": anime.get("description", ""),
            "episodes": anime.get("episodes"),
            "score": anime.get("averageScore"),
            "popularity": anime.get("popularity"),
            "genres": anime.get("genres", []),
            "studios": [s["name"] for s in anime.get("studios", {}).get("nodes", [])],
            "characters": [
                {
                    "id": c["id"],
                    "name": c["name"]["full"]
                }
                for c in anime.get("characters", {}).get("nodes", [])
            ],
            "relations": [
                {
                    "type": edge["relationType"],
                    "id": edge["node"]["id"],
                    "title": edge["node"]["title"]["romaji"]
                }
                for edge in anime.get("relations", {}).get("edges", [])
            ],
            "recommendations": [
                {
                    "id": node["mediaRecommendation"]["id"],
                    "title": node["mediaRecommendation"]["title"]["romaji"],
                    "rating": node["rating"]
                }
                for node in anime.get("recommendations", {}).get("nodes", [])
                if node.get("mediaRecommendation")
            ]
        }

    def save_to_json(self, anime_list: List[Dict], filename: str = "anime_data.json"):
        """Save anime data to JSON file."""
        filepath = self.data_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(anime_list, f, indent=2, ensure_ascii=False)

        console.print(f"[green]✓ Saved {len(anime_list)} anime to {filepath}[/green]")
        return filepath

    def load_from_json(self, filename: str = "anime_data.json") -> List[Dict]:
        """Load anime data from JSON file."""
        filepath = self.data_dir / filename

        if not filepath.exists():
            console.print(f"[red]File not found: {filepath}[/red]")
            return []

        with open(filepath, "r", encoding="utf-8") as f:
            anime_list = json.load(f)

        console.print(f"[green]✓ Loaded {len(anime_list)} anime from {filepath}[/green]")
        return anime_list


if __name__ == "__main__":
    # Test fetching
    fetcher = AnimeDataFetcher()

    # Fetch from Jikan
    anime_list = fetcher.fetch_from_jikan(max_anime=50, min_score=8.0)
    fetcher.save_to_json(anime_list, "jikan_top_anime.json")

    # Or fetch from AniList
    # anime_list = fetcher.fetch_from_anilist(max_anime=50, min_score=80)
    # fetcher.save_to_json(anime_list, "anilist_top_anime.json")
