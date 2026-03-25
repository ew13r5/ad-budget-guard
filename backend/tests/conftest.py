import os
import pytest
import pytest_asyncio

# Mark all async tests with asyncio
pytestmark = pytest.mark.asyncio

# Check if Docker is available for integration tests
def _docker_available():
    try:
        import docker
        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False

requires_docker = pytest.mark.skipif(
    not _docker_available(),
    reason="Docker not available"
)


@pytest.fixture(scope="session")
def postgres_container():
    """Start PostgreSQL testcontainer for entire session."""
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg


@pytest.fixture(scope="session")
def postgres_url(postgres_container):
    """Sync connection URL for test PostgreSQL."""
    return postgres_container.get_connection_url()


@pytest.fixture(scope="session")
def sync_engine(postgres_url):
    """Sync engine with migrations applied once."""
    from sqlalchemy import create_engine
    from alembic.config import Config
    from alembic import command

    engine = create_engine(postgres_url)

    alembic_cfg = Config(
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "alembic.ini")
    )
    alembic_cfg.set_main_option("sqlalchemy.url", postgres_url)
    alembic_cfg.set_main_option("script_location",
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "alembic"))
    command.upgrade(alembic_cfg, "head")

    yield engine
    engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def async_engine(postgres_url):
    """Async engine for test database."""
    import re
    from sqlalchemy.ext.asyncio import create_async_engine

    async_url = re.sub(r"^postgresql(\+\w+)?://", "postgresql+asyncpg://", postgres_url)
    engine = create_async_engine(async_url)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(async_engine):
    """Async session with rollback for test isolation."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    factory = async_sessionmaker(async_engine, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
def sync_db_session(sync_engine):
    """Sync session with rollback for test isolation."""
    from sqlalchemy.orm import sessionmaker

    factory = sessionmaker(sync_engine, expire_on_commit=False)
    session = factory()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def alembic_config(postgres_url):
    """Alembic Config for test database."""
    from alembic.config import Config

    cfg = Config(
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "alembic.ini")
    )
    cfg.set_main_option("sqlalchemy.url", postgres_url)
    cfg.set_main_option("script_location",
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "alembic"))
    return cfg
