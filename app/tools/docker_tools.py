import re
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE = (PROJECT_ROOT/"workspace").resolve()

IMAGE_TAG_PATTERN = re.compile(
    r"^[a-z0-9][a-z0-9._/-]*:[a-z0-9][a-z0-9_.-]*$"
)


def build_docker_image(repository_path:str, image_tag:str) -> dict:
    """Build a Docker image from a trusted repository in Forge's workspace."""

    repo_path = Path(repository_path).resolve()

    # Never allow an arbitrary host directory as the build context.
    if not repo_path.is_relative_to(WORKSPACE):
        raise ValueError("Repository must be inside Forge's workspace.")

    if not repo_path.is_dir():
        raise ValueError("Repository directory does not exist.")

    if not (repo_path / "Dockerfile").is_file():
        return {
            "success": False,
            "image_tag": image_tag,
            "error": "Dockerfile not found.",
            "logs": "",
        }


    if not IMAGE_TAG_PATTERN.fullmatch(image_tag):
        raise ValueError(
            "Invalid image tag. Use a lowercase name such as "
            "'forge-test:latest'."
        )

    command = [
        "docker",
        "build",
        "--tag",
        image_tag,
        str(repo_path)
    ]


    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        logs = []

        for line in process.stdout:
            print(line, end="", flush=True)
            logs.append(line)

        exit_code = process.wait(timeout=600)
        full_logs = "".join(logs)

        return {
            "success": exit_code == 0,
            "image_tag": image_tag,
            "exit_code": exit_code,
            "logs": full_logs[-6000:],
        }
    

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "image_tag": image_tag,
            "error": "Docker build exceeded 600 seconds.",
            "logs": "",
        }

    except FileNotFoundError:
        return {
            "success": exit_code == 0,
            "image_tag": image_tag,
            "exit_code": exit_code,
            "error_summary": None if exit_code == 0 else "Docker build failed.",
            "logs": full_logs[-6000:] if exit_code != 0 else "",
        }


if __name__=="__main__":

    repo = str(
        Path("workspace/DivyanshModi25__devops-frontend-ci-cd").resolve()
    )

    result = build_docker_image(repo,"forge-cicd-test:latest")
    print(result)