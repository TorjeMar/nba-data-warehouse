# MySQL test pack

Put these files into your project root with this layout:

```text
<project-root>/
  pytest.ini
  tests/
    conftest.py
    unit/
      test_transform.py
    integration/
      test_mysql_load.py
  scripts/
    run_mysql_integration_tests.sh
```

## Install dependencies

```bash
pip install pytest mysql-connector-python
```

## Run unit tests

```bash
pytest tests/unit/test_transform.py
```

## Run integration tests manually

```bash
docker compose up -d
set -a
source .env
set +a
TEST_MYSQL_E2E=1 pytest tests/integration/test_mysql_load.py
```

## Run integration tests with helper script

```bash
chmod +x scripts/run_mysql_integration_tests.sh
bash scripts/run_mysql_integration_tests.sh
```
