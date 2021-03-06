import os
import subprocess
import sys
from pathlib import Path

import py
import pytest
import yaml
from cookiecutter.exceptions import FailedHookException
from pipx.constants import DEFAULT_PIPX_BIN_DIR, LOCAL_BIN_DIR
from pytest_cookies.plugin import Cookies  # type: ignore
from pytest_virtualenv import VirtualEnv

from tests.utils import inside_dir


def test_project_tree(cookies: Cookies) -> None:
    result = cookies.bake(extra_context={"project_dir": "test-project"})
    assert result.exit_code == 0
    assert result.exception is None
    assert result.project_path.name == "test-project"


def test_run_flake8(cookies: Cookies) -> None:
    result = cookies.bake(extra_context={"project_dir": "flake8-compat"})
    with inside_dir(str(result.project_path)):
        subprocess.check_call(["flake8"])


def test_project_dir_hook(cookies: Cookies) -> None:
    result = cookies.bake(extra_context={"project_dir": "myproject"})
    assert result.exit_code == 0
    result = cookies.bake(extra_context={"project_dir": "my-project"})
    assert result.exit_code == 0
    result = cookies.bake(extra_context={"project_dir": "my?project"})
    assert result.exit_code != 0
    if sys.platform == "win32":
        # Unfortunately, pre_gen hook is called before cookiecutter copies the template
        #  into the TMP dir for rendering.
        # This will not hurt the user,
        #  but the error message will also include a traceback
        assert isinstance(result.exception, OSError)
    else:
        assert isinstance(result.exception, FailedHookException)
    result = cookies.bake(extra_context={"project_dir": "t" * 256})
    assert result.exit_code != 0


def test_project_id_hook(cookies: Cookies) -> None:
    wrong_ids = [
        "qwe/qwe",
        "qwe?qwe",
        "qwe!qwe",
        "qwe.qwe",
        "qwe%qwe",
        "qwe-qwe",
        "-qwe",
        "qwe-",
        "qwe-qwe",
        "123",
        "1 23",
        "1qwe23",
    ]
    correct_ids = [
        "qwe",
        "q",
        "qwe_qwe",
        "_qwe",
        "qwe_",
        "qwe123",
        "qwe_123",
        "qwe" * 20,
    ]
    for id_ in wrong_ids:
        result = cookies.bake(extra_context={"project_id": id_})
        assert result.exit_code != 0, id_
        assert isinstance(result.exception, FailedHookException)
    for id_ in correct_ids:
        result = cookies.bake(extra_context={"project_id": id_})
        assert result.exit_code == 0, id_


def test_project_description(cookies: Cookies) -> None:
    descriptions = [
        # " ",
        "Descrition!",
        "123",
        "https://github.com/neuro-inc/cookiecutter-neuro-project/",
    ]
    for descr in descriptions:
        result = cookies.bake(extra_context={"project_description": descr})
        assert result.exit_code == 0, descr


@pytest.mark.parametrize("venv_install_packages", ["", "neuro-cli", "neuro-all"])
def test_user_role_added(
    tmpdir: py.path.local, venv_install_packages: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    cwd = Path(os.getcwd())

    # This 'hides' neuro-cli installed via pipx
    cur_path = os.environ["PATH"].split(os.pathsep)
    avoid_paths = (
        str(LOCAL_BIN_DIR),
        str(DEFAULT_PIPX_BIN_DIR),
    )
    filtered_path = list(filter(lambda x: x not in avoid_paths, cur_path))
    monkeypatch.setenv("PATH", os.pathsep.join(filtered_path))

    with VirtualEnv() as venv:
        if venv_install_packages:
            venv.install_package(venv_install_packages, installer="pip")

        venv.run(
            ("cookiecutter", cwd, "-o", tmpdir, "--no-input", "--default-config"),
            capture=True,
        )
        proj_yml = yaml.safe_load(
            Path(tmpdir / "neuro project" / ".neuro" / "project.yml").read_text()
        )

        if venv_install_packages:
            assert "owner" in proj_yml
            assert "role" in proj_yml
        else:
            assert "owner" not in proj_yml
            assert "role" not in proj_yml
