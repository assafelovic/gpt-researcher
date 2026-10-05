"""Docker configuration regressions using synthetic files, never the repo .env.

Docker-dependent checks skip when the local CLI/plugin/daemon is unavailable.
Set GPTR_LEGACY_COMPOSE to a Compose v1 executable to run the same config checks
with that implementation as well. No images are pulled and no app is started.
"""

import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import uuid

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
BACKEND_SERVICES = ("gpt-researcher", "gpt-researcher-tests")


def _run(command, env):
    result = subprocess.run(
        command, env=env, cwd=env["PWD"], capture_output=True, text=True, timeout=60
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout


@pytest.fixture
def project(tmp_path):
    # Only known configuration files are copied, not an unknown local .env.
    for filename in ("docker-compose.yml", "docker-compose.env.yml"):
        shutil.copyfile(ROOT / filename, tmp_path / filename)
    for directory in ("frontend/nextjs", "docs/discord-bot"):
        (tmp_path / directory).mkdir(parents=True)
    return tmp_path


@pytest.fixture
def safe_env(project):
    # Do not let host credentials or Docker contexts leak into these probes.
    return {
        "PATH": os.environ.get("PATH", ""),
        "PWD": str(project),
        "DOCKER_CONFIG": str(project / "docker-config"),
        "DOCKER_HOST": "unix:///var/run/docker.sock",
    }


@pytest.fixture(params=("v2", "v1"))
def compose(request, project, safe_env):
    if request.param == "v1":
        executable = os.environ.get("GPTR_LEGACY_COMPOSE")
        if not executable:
            pytest.skip("Set GPTR_LEGACY_COMPOSE to check legacy Compose")
        command = [executable]
    else:
        executable = shutil.which("docker")
        if not executable:
            pytest.skip("Docker CLI is unavailable")
        command = [executable, "compose"]
    version = subprocess.run(
        command + ["version"], env=safe_env, cwd=project,
        capture_output=True, timeout=60
    )
    if version.returncode:
        pytest.skip("Compose is unavailable")
    return command + [
        "--project-directory", str(project),
        "-f", str(project / "docker-compose.yml"),
    ]


def _config(compose, project, env, *, overlay=False):
    command = compose.copy()
    if overlay:
        command += ["-f", str(project / "docker-compose.env.yml")]
    return yaml.safe_load(_run(command + ["--profile", "test", "config"], env))


def test_runtime_env_overlay_only_targets_backend_services():
    overlay = yaml.safe_load((ROOT / "docker-compose.env.yml").read_text())
    assert set(overlay["services"]) == set(BACKEND_SERVICES)
    for service in overlay["services"].values():
        # String paths keep this overlay usable with Compose 1.29.2.
        assert service["env_file"] == [".env"]


def test_shell_configuration_does_not_require_dotenv(compose, project, safe_env):
    env = safe_env | {
        "RETRIEVER": "pubmed_central",
        "SMART_LLM": "openai:synthetic-shell-model",
        "OPENAI_API_KEY": "synthetic-shell-key",
    }
    config = _config(compose, project, env)
    assert not (project / ".env").exists()
    for name in BACKEND_SERVICES:
        values = config["services"][name]["environment"]
        assert values["RETRIEVER"] == env["RETRIEVER"]
        assert values["SMART_LLM"] == env["SMART_LLM"]
        assert values["OPENAI_API_KEY"] == env["OPENAI_API_KEY"]


def test_unset_research_options_preserve_app_defaults(compose, project, safe_env):
    config = _config(compose, project, safe_env)
    for name in BACKEND_SERVICES:
        values = config["services"][name]["environment"]
        # A null value stays unset, rather than overriding Config with "".
        assert values.get("RETRIEVER") is None
        assert values.get("SMART_LLM") is None


@pytest.mark.parametrize("shell_override", (False, True))
def test_dotenv_runtime_settings_and_precedence(
    compose, project, safe_env, shell_override
):
    (project / ".env").write_text(
        "RETRIEVER=pubmed_central\n"
        "SMART_LLM=openai:synthetic-file-model\n"
        "OPENAI_API_KEY=synthetic-file-key\n"
        "GPTR_SENTINEL_OPTION=synthetic-provider-option\n"
        "LOGGING_LEVEL=DEBUG\n"
        "IMAGE_GENERATION_ENABLED=true\n"
    )
    env = safe_env.copy()
    if shell_override:
        env |= {
            "RETRIEVER": "tavily",
            "SMART_LLM": "openai:synthetic-shell-model",
            "OPENAI_API_KEY": "synthetic-shell-key",
        }
    config = _config(compose, project, env, overlay=True)
    for name in BACKEND_SERVICES:
        values = config["services"][name]["environment"]
        assert values["RETRIEVER"] == ("tavily" if shell_override else "pubmed_central")
        assert values["SMART_LLM"] == (
            "openai:synthetic-shell-model" if shell_override
            else "openai:synthetic-file-model"
        )
        assert values["OPENAI_API_KEY"] == (
            "synthetic-shell-key" if shell_override else "synthetic-file-key"
        )
        assert values["GPTR_SENTINEL_OPTION"] == "synthetic-provider-option"
        # Explicit base configuration still overrides values from env_file.
        assert values["LOGGING_LEVEL"] == "INFO"
        assert values["IMAGE_GENERATION_ENABLED"] == "true"


def test_root_dotenv_is_excluded_from_real_docker_image(project, safe_env):
    executable = shutil.which("docker")
    if not executable:
        pytest.skip("Docker CLI is unavailable")
    docker = [executable]
    available = subprocess.run(
        docker + ["info", "--format", "{{.ServerVersion}}"],
        env=safe_env, cwd=project, capture_output=True, timeout=60
    )
    if available.returncode:
        pytest.skip("Local Docker daemon is unavailable")

    context = project / "context"
    context.mkdir()
    shutil.copyfile(ROOT / ".dockerignore", context / ".dockerignore")
    (context / ".env").write_text("GPTR_SENTINEL=synthetic-root-secret\n")
    (context / ".env.example").write_text("GPTR_SENTINEL=example-value\n")
    frontend = context / "frontend/nextjs"
    frontend.mkdir(parents=True)
    (frontend / ".env").write_text("NEXT_PUBLIC_GPTR_API_URL=https://synthetic.invalid\n")
    # Exercise the same root-context COPY used by both backend Dockerfiles,
    # without pulling bases or installing the production app dependencies.
    (context / "Dockerfile").write_text(
        "FROM scratch\nWORKDIR /usr/src/app\nCOPY ./ ./\n"
    )
    tag = f"gptr-env-context-test:{uuid.uuid4().hex}"
    archive = project / "image.tar"
    try:
        _run(docker + [
            "build", "--pull=false", "--network=none", "--no-cache",
            "--tag", tag, str(context),
        ], safe_env)
        _run(docker + ["image", "save", tag, "--output", str(archive)], safe_env)
        image_files = {}
        with tarfile.open(archive) as image:
            manifest = json.load(image.extractfile("manifest.json"))[0]
            for layer_path in manifest["Layers"]:
                layer_data = image.extractfile(layer_path).read()
                with tarfile.open(fileobj=io.BytesIO(layer_data)) as layer:
                    for entry in layer:
                        if entry.isfile():
                            image_files[entry.name] = layer.extractfile(entry).read()
        assert "usr/src/app/.env" not in image_files
        assert b"synthetic-root-secret" not in b"".join(image_files.values())
        assert "usr/src/app/.env.example" in image_files
        assert "usr/src/app/frontend/nextjs/.env" in image_files
    finally:
        subprocess.run(
            docker + ["image", "rm", "--force", tag],
            env=safe_env, cwd=project, capture_output=True, timeout=60,
        )
