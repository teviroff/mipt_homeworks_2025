from dataclasses import dataclass


@dataclass
class Repository:
    """Model for GitHub repository data."""

    name: str
    description: str
    url: str
    created_at: str
    updated_at: str
    homepage: str
    size: int
    stars: int
    forks: int
    issues: int
    watchers: int
    language: str
    license: str | None
    topics: list[str]
    has_issues: bool
    has_projects: bool
    has_downloads: bool
    has_wiki: bool
    has_pages: bool
    has_discussions: bool
    is_fork: bool
    is_archived: bool
    is_template: bool
    default_branch: str

    def to_csv_entry(self) -> str:
        """Returns a CSV dump of repository."""

        return ",".join([str(value) for _, value in self.__dict__.items()])
