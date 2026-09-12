from app.env import build_env


def test_build_env_resolves_private_path_before_loading_secrets(tmp_path):
    root = tmp_path / "root"
    private = tmp_path / "private"
    machine_dir = root / "machines" / "test"
    env_dir = private / "env"
    machine_dir.mkdir(parents=True)
    env_dir.mkdir(parents=True)

    (machine_dir / "machine.env").write_text(
        f'PRIVATE_ROOT="{private}"\nMC_PRIVATE="$PRIVATE_ROOT"\n'
    )
    (env_dir / "test.env").write_text('TAILNET_NAME="example"\n')

    result = build_env("test", root)

    assert result["MC_PRIVATE"] == str(private)
    assert result["TAILNET_NAME"] == "example"
