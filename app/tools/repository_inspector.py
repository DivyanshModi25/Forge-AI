from urllib.parse import urlparse
from pathlib import Path
import subprocess


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE = PROJECT_ROOT / "workspace"

MANIFESTS = {
    "requirements.txt": "Python dependencies",
    "pyproject.toml": "Python project configuration",
    "Pipfile": "Pipenv dependencies",
    "package.json": "Node.js dependencies",
    "pnpm-lock.yaml": "pnpm lockfile",
    "yarn.lock": "Yarn lockfile",
    "Cargo.toml": "Rust dependencies",
    "pom.xml": "Maven configuration",
    "build.gradle": "Gradle configuration",
    "go.mod": "Go dependencies",
}


IMPORTANT_FILES = [
    "Dockerfile",
    "docker-compose.yml",
    "compose.yaml",
    "compose.yml",
    ".dockerignore",
    "Makefile",
]


def validate_github_url(url:str)-> tuple[str,str]:
    """Validate a public GitHub repository URL."""

    parsed = urlparse(url.strip())

    if(parsed.scheme!="https" or parsed.hostname!="github.com"):
        raise ValueError("Invalid Url, Expected a github url only ⚠️")


    parts = parsed.path.split("/")


    owner,repo = parts[1:3]
    repo=repo.removesuffix(".git")

    if not owner or not repo or owner in {".", ".."} or repo in {".", ".."}:
        raise ValueError("Invalid GitHub owner or repository.")

    if any(c in owner + repo for c in ("/", "\\", "\0")):
        raise ValueError("Invalid characters in repository URL.")

    clone_url = f"https://github.com/{owner}/{repo}.git"

    return owner, repo, clone_url


def inspect_repository(github_url:str) -> dict:

    owner,repo,clone_url = validate_github_url(github_url)

    WORKSPACE.mkdir(parents=True, exist_ok=True)
    repo_path = (WORKSPACE / f"{owner}__{repo}").resolve()

    print(repo_path)

    if not repo_path.is_relative_to(WORKSPACE.resolve()):
        raise ValueError("Repository path is outside the workspace.")

    if repo_path.exists():
        raise FileExistsError(
            f"Workspace already exists: {repo_path}. "
            "Remove it before inspecting this repository again."
        )

    try:
        subprocess.run(
            ["git","clone","--depth","1","--",clone_url,str(repo_path)],
            check=True,
            capture_output=True,
            text=True,
            timeout=120
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"Git clone failed: {exc.stderr[-1500:]}"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Git clone exceeded the time limit.") from exc

    root_entries = sorted(
        path.name
        for path in repo_path.iterdir()
        if path.name != ".git"
    )

    manifests = [
        {"file": name, "description": description}
        for name, description in MANIFESTS.items()
        if (repo_path / name).is_file()
    ]

    important_files = [
        name
        for name in IMPORTANT_FILES
        if (repo_path / name).is_file()
    ]

    workflows_dir = repo_path / ".github" / "workflows"

    workflows = (
        sorted(
            str(path.relative_to(repo_path))
            for path in workflows_dir.iterdir()
            if path.is_file() and path.suffix in {".yml", ".yaml"}
        )
        if workflows_dir.is_dir()
        else []
    )

    has_tests = any(
        (repo_path / name).is_dir()
        for name in ("tests", "test", "__tests__")
    )


    return {
        "repository": f"{owner}/{repo}",
        "local_path": str(repo_path),
        "root_entries": root_entries[:100],
        "manifests": manifests,
        "important_files": important_files,
        "github_workflows": workflows,
        "has_tests_directory": has_tests,
        "has_dockerfile": (repo_path / "Dockerfile").is_file(),
    }



if __name__=="__main__":
    print(inspect_repository("https://github.com/DivyanshModi25/Accounting-Software"))
