import asyncio

import httpx

from infrastructure.models import Repository


class GitHubClient:
    """Async client for making requests to GitHub API."""

    BASE_URL = "https://api.github.com"
    SEARCH_REPOS_PAGE_SIZE = 100

    def __init__(self, token: str | None = None, timeout: float = 30.0) -> None:
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHub-API-Client/1.0",
        }
        if token is not None:
            self.headers["Authorization"] = f"Bearer {token}"
        self.timeout = timeout

    async def search_repositories(
        self,
        lang: str,
        stars_min: int = 0,
        stars_max: int | None = None,
        forks_min: int = 0,
        forks_max: int | None = None,
        offset: int = 0,
        limit: int = 10,
    ) -> list[Repository]:
        """Wrapper around `/search/repositories` API endpoint."""

        query_parts = [f"language:{lang}"]
        if stars_min >= 0:
            query_parts.append(f"stars:>={stars_min}")
        if stars_max is not None:
            query_parts.append(f"stars:<={stars_max}")
        if forks_min > 0:
            query_parts.append(f"forks:>={forks_min}")
        if forks_max is not None:
            query_parts.append(f"forks:<={forks_max}")
        query = " ".join(query_parts)
        async with httpx.AsyncClient(
            headers=self.headers, timeout=self.timeout, follow_redirects=True
        ) as client:
            return await self._fetch_repos(client, query, offset, limit)

    @classmethod
    async def _fetch_page(
        cls, client: httpx.AsyncClient, query: str, page: int
    ) -> list[Repository]:
        response = await client.get(
            f"{cls.BASE_URL}/search/repositories",
            params={"q": query, "page": page, "per_page": cls.SEARCH_REPOS_PAGE_SIZE},
        )
        if response.status_code == 403:
            rate_limit = response.headers.get("X-RateLimit-Remaining", "0")
            if rate_limit == "0":
                reset_time = response.headers.get("X-RateLimit-Reset")
                raise Exception(f"Rate limit exceeded. Reset at {reset_time}")
        response.raise_for_status()
        data = response.json()
        assert isinstance(data, dict)  # noqa: S101
        items = data.get("items", [])
        assert isinstance(items, list)  # noqa: S101
        return [
            Repository(
                name=repo["name"],
                description=repo["description"] or "",
                url=repo["html_url"],
                created_at=repo["created_at"],
                updated_at=repo["updated_at"],
                homepage=repo["homepage"],
                size=repo["size"],
                stars=repo["stargazers_count"],
                forks=repo["forks_count"],
                issues=repo["open_issues"],
                watchers=repo["watchers"],
                language=repo["language"],
                license=repo["license"]["name"]
                if repo["license"] is not None
                else None,
                topics=repo["topics"],
                has_issues=repo["has_issues"],
                has_projects=repo["has_projects"],
                has_downloads=repo["has_downloads"],
                has_wiki=repo["has_wiki"],
                has_pages=repo["has_pages"],
                has_discussions=repo["has_discussions"],
                is_fork=repo["fork"],
                is_archived=repo["archived"],
                is_template=repo["is_template"],
                default_branch=repo["default_branch"],
            )
            for repo in items
        ]

    @classmethod
    async def _fetch_repos(
        cls, client: httpx.AsyncClient, query: str, offset: int, limit: int
    ) -> list[Repository]:
        repos = []
        pages = range(
            offset // cls.SEARCH_REPOS_PAGE_SIZE,
            (offset + limit + cls.SEARCH_REPOS_PAGE_SIZE - 1)
            // cls.SEARCH_REPOS_PAGE_SIZE,
        )
        for page in pages:
            fetched = await cls._fetch_page(client, query, page)
            repos.extend(fetched)
            if len(fetched) < cls.SEARCH_REPOS_PAGE_SIZE:
                break
            # NOTE: rate limiting fix
            await asyncio.sleep(0.01)
        return repos[offset % cls.SEARCH_REPOS_PAGE_SIZE :][:limit]
