from pytest_cookies.plugin import Cookies  # type: ignore

from tests.e2e.conftest import exec
from tests.utils import inside_dir


def test_neuro_flow_live(cookies: Cookies) -> None:
    result = cookies.bake(
        extra_context={
            "project_dir": "test-project",
            "project_id": "awesome_project",
        }
    )
    with inside_dir(str(result.project_path)):
        proc = exec("neuro-flow --show-traceback ps")
        assert "JOB" in proc.stdout, proc

        proc = exec("neuro-flow --show-traceback status train", assert_exit_code=False)
        assert "is not running" in proc.stdout, proc

        proc = exec("neuro-flow --show-traceback run --dry-run train")
        assert "neuro run" in proc.stdout, proc
        assert "--tag=project:awesome-project" in proc.stdout, proc
