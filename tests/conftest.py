import shutil
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.session import get_engine, get_session_factory, init_db
from app.main import create_app


@pytest.fixture
def workspace_tmp_dir():
    tmp_dir = Path("tests/.tmp") / uuid4().hex
    tmp_dir.mkdir(parents=True, exist_ok=True)
    yield tmp_dir
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)


@pytest.fixture
def configured_env(monkeypatch, workspace_tmp_dir):
    papers_dir = workspace_tmp_dir / "papers"
    vector_dir = workspace_tmp_dir / "vector_store"
    db_path = workspace_tmp_dir / "test.db"

    monkeypatch.setattr(settings, "PAPERS_DIR", str(papers_dir))
    monkeypatch.setattr(settings, "VECTOR_DB_PATH", str(vector_dir))
    monkeypatch.setattr(settings, "DATABASE_URL", f"sqlite:///{db_path.as_posix()}")

    get_engine.cache_clear()
    get_session_factory.cache_clear()
    init_db()

    yield {
        "papers_dir": papers_dir,
        "vector_dir": vector_dir,
        "db_path": db_path,
    }

    get_engine().dispose()
    get_engine.cache_clear()
    get_session_factory.cache_clear()


@pytest.fixture
def client(configured_env):
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    pdf_path = Path(
        "A_Data-Driven_Reinforcement_Learning_Enabled_Battery_Fast_Charging_Optimization_Using_Real-World_Experimental_Data.pdf"
    )
    return pdf_path.read_bytes()
