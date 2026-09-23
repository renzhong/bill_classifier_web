"""Persistent local test database, SQL snapshots, and reproducible upload files."""

import argparse
import base64
import json
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
STATE = Path(os.environ.get("BCW_TESTDATA_DIR", Path.home() / ".local/share/bill-classifier-web/testdata"))
CONTAINER = "bcw-testdata-mysql"
VOLUME = "bcw-testdata-mysql-data"
DATABASE = "bcw_fixture_test"
LABEL = "bill-classifier.testdata"


def run(args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def configuration():
    STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = STATE / "environment.env"
    if not path.exists():
        volume = subprocess.run(["docker", "volume", "inspect", VOLUME], capture_output=True)
        if volume.returncode == 0:
            raise RuntimeError(f"数据卷已存在，但连接配置丢失；请恢复 {path}")
        password = secrets.token_urlsafe(24)
        values = {
            "MYSQL_ROOT_PASSWORD": secrets.token_urlsafe(24),
            "MYSQL_DATABASE": DATABASE,
            "MYSQL_USER": "bcw",
            "MYSQL_PASSWORD": password,
            "BCW_ENV": "dev",
            "BCW_DB_HOST": "127.0.0.1",
            "BCW_DB_PORT": "33316",
            "BCW_DB_NAME": DATABASE,
            "BCW_DB_USER": "bcw",
            "BCW_DB_PASSWORD": password,
            "BCW_JWT_SECRET": secrets.token_urlsafe(48),
            "BCW_FERNET_KEY": base64.urlsafe_b64encode(secrets.token_bytes(32)).decode(),
            "BCW_CORS_ORIGINS": "http://127.0.0.1:15173,http://localhost:15173",
        }
        with open(path, "x", opener=lambda p, flags: os.open(p, flags, 0o600)) as output:
            output.write("".join(f"{key}={value}\n" for key, value in values.items()))
    values = dict(line.split("=", 1) for line in path.read_text().splitlines() if line)
    if values["MYSQL_DATABASE"] != DATABASE or values["BCW_DB_NAME"] != DATABASE:
        raise RuntimeError("此工具只能操作专用的 bcw_fixture_test 数据库")
    return values


def inspect_container():
    result = subprocess.run(["docker", "inspect", CONTAINER], capture_output=True)
    if result.returncode:
        return None
    container = json.loads(result.stdout)[0]
    if (container["Config"].get("Labels") or {}).get(LABEL) != "true":
        raise RuntimeError("同名容器不属于本工具，停止操作")
    return container


def start(values):
    container = inspect_container()
    if container is None:
        run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                CONTAINER,
                "--label",
                f"{LABEL}=true",
                "--restart",
                "unless-stopped",
                "--env-file",
                str(STATE / "environment.env"),
                "-p",
                f"127.0.0.1:{values['BCW_DB_PORT']}:3306",
                "-v",
                f"{VOLUME}:/var/lib/mysql",
                "mysql:8.0",
                "--character-set-server=utf8mb4",
                "--collation-server=utf8mb4_unicode_ci",
            ],
            stdout=subprocess.DEVNULL,
        )
    else:
        if not container["State"]["Running"]:
            run(["docker", "start", CONTAINER], stdout=subprocess.DEVNULL)
    for _ in range(60):
        ready = subprocess.run(
            [
                "docker",
                "exec",
                CONTAINER,
                "sh",
                "-c",
                'export MYSQL_PWD="$MYSQL_PASSWORD"; exec mysql -u"$MYSQL_USER" "$MYSQL_DATABASE" -e "SELECT 1"',
            ],
            capture_output=True,
        )
        if ready.returncode == 0:
            return
        time.sleep(1)
    raise RuntimeError("MySQL 在 60 秒内未就绪")


def sql(statement, *, root=False):
    auth = (
        'export MYSQL_PWD="$MYSQL_ROOT_PASSWORD"; exec mysql -uroot '
        if root
        else 'export MYSQL_PWD="$MYSQL_PASSWORD"; exec mysql -u"$MYSQL_USER" '
    )
    return run(
        [
            "docker",
            "exec",
            "-i",
            CONTAINER,
            "sh",
            "-c",
            auth + '--default-character-set=utf8mb4 --batch --skip-column-names "$MYSQL_DATABASE"',
        ],
        input=statement,
        capture_output=True,
    ).stdout


def python_command(values, *command):
    env = os.environ | values
    return run(
        ["uv", "--cache-dir", str(BACKEND / ".uv-cache"), "run", "--frozen", *command], cwd=BACKEND, env=env
    )


def migrate(values):
    python_command(values, "alembic", "upgrade", "head")


def snapshot(destination):
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = destination.with_suffix(".sql.tmp")
    try:
        with open(temporary, "w", opener=lambda p, flags: os.open(p, flags, 0o600)) as output:
            run(
                [
                    "docker",
                    "exec",
                    CONTAINER,
                    "sh",
                    "-c",
                    'export MYSQL_PWD="$MYSQL_PASSWORD"; exec mysqldump -u"$MYSQL_USER" '
                    "--single-transaction --no-tablespaces --set-gtid-purged=OFF "
                    '--skip-dump-date --hex-blob "$MYSQL_DATABASE"',
                ],
                stdout=output,
            )
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"SQL 快照：{destination}", flush=True)
    return destination


def backup_path():
    return STATE / "snapshots" / f"snapshot-{time.time_ns()}.sql"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=["init", "snapshot", "restore", "status", "stop", "backend", "frontend"]
    )
    parser.add_argument("--from-sql", type=Path, help="restore 使用的快照；默认 baseline.sql")
    args = parser.parse_args()
    if args.command in ("status", "stop"):
        container = inspect_container()
        if not container or not container["State"]["Running"]:
            print("测试数据库尚未启动；运行 init 可启动并保留原有数据。")
        elif args.command == "stop":
            run(["docker", "stop", CONTAINER])
        else:
            print(
                sql(
                    b"SELECT 'users', COUNT(*) FROM users UNION ALL SELECT 'bills', COUNT(*) FROM bills;"
                ).decode()
            )
        return
    values = configuration()
    start(values)
    if args.command == "init":
        migrate(values)
        if int(sql(b"SELECT COUNT(*) FROM users;")) == 0:
            sql((BACKEND / "devdata/seed.sql").read_bytes())
        else:
            print("数据库已有数据，保留现有账号、账单和规则。", flush=True)
        python_command(values, "-m", "devdata.generate", str(STATE / "uploads"))
        if not (STATE / "baseline.sql").exists():
            snapshot(STATE / "baseline.sql")
    elif args.command == "snapshot":
        snapshot(backup_path())
    elif args.command == "restore":
        source = args.from_sql or STATE / "baseline.sql"
        content = source.read_bytes()
        saved = snapshot(backup_path())
        try:
            sql(
                f"DROP DATABASE {DATABASE}; CREATE DATABASE {DATABASE} CHARACTER SET utf8mb4;".encode(),
                root=True,
            )
            sql(content)
            migrate(values)
        except Exception:
            print(f"恢复失败，操作前的完整备份保留在 {saved}", file=sys.stderr)
            raise
        print("已恢复快照。请重启连接此数据库的后端进程。", flush=True)
    elif args.command == "backend":
        migrate(values)
        python_command(values, "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "18000")
    elif args.command == "frontend":
        run(
            ["npm", "run", "dev", "--", "--host", "127.0.0.1", "--port", "15173"],
            cwd=ROOT / "frontend",
            env=os.environ | {"VITE_API_BASE": "/api/v1", "VITE_BACKEND_URL": "http://127.0.0.1:18000"},
        )
    print(f"数据目录：{STATE}\n数据库：127.0.0.1:{values['BCW_DB_PORT']}/{DATABASE}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
    except (RuntimeError, subprocess.CalledProcessError, FileNotFoundError) as error:
        print(str(error), file=sys.stderr)
        if isinstance(error, subprocess.CalledProcessError) and error.stderr:
            print(error.stderr.decode(), file=sys.stderr)
        sys.exit(1)
