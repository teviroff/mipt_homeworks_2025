import os
from pathlib import Path
from typing import Annotated, Self

from aiofile import async_open
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field, model_validator

from infrastructure.client import GitHubClient

router = APIRouter()


def _get_github_client() -> GitHubClient:
    token = os.getenv("GITHUB_TOKEN")
    return GitHubClient(token=token)


class SearchQueryParams(BaseModel):
    """Pydantic model with `/search` endpoint query parameters."""

    lang: str
    stars_min: Annotated[int, Field(ge=0)] = 0
    stars_max: Annotated[int | None, Field(ge=0)] = None
    forks_min: Annotated[int, Field(ge=0)] = 0
    forks_max: Annotated[int | None, Field(ge=0)] = None
    offset: Annotated[int, Field(ge=0)] = 0
    limit: Annotated[int, Field(ge=1)] = 10

    @model_validator(mode="after")
    def check_stars_range(self) -> Self:
        """Checks that stars constraints form a valid range."""

        if self.stars_max is not None and self.stars_min > self.stars_max:
            raise ValueError("Provided stars constraints are contradictory")
        return self

    @model_validator(mode="after")
    def check_forks_range(self) -> Self:
        """Checks that forks constraints form a valid range."""

        if self.forks_max is not None and self.forks_min > self.forks_max:
            raise ValueError("Provided forks constraints are contradictory")
        return self


@router.get("/search")
async def search(
    query: SearchQueryParams = Query(),
    client: GitHubClient = Depends(_get_github_client),
) -> None:
    """
    Performs GitHub API request with given parameters and writes results to
    `/static` folder.
    """  # noqa: D205

    repos = await client.search_repositories(
        query.lang,
        query.stars_min,
        query.stars_max,
        query.forks_min,
        query.forks_max,
        query.offset,
        query.limit,
    )
    filename = f"repositories_{query.lang}_{query.limit}_{query.offset}.csv"
    path = Path.cwd() / "static" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()
    async with async_open(path, "w") as f:
        for repo in repos:
            await f.write(f"{repo.to_csv_entry()}\n")
