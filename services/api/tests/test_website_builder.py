from aethon.website_builder import WebsiteBuilder
from app.memory_repository import MemoryRepository

def test_website_builder_creates_and_persists_static_artifact():
    builder=WebsiteBuilder(repository=MemoryRepository())
    build=builder.build("Create a farm landing page", owner_id="owner-1", project_id="p1")
    assert build.project_id == "p1"
    assert set(("index.html","styles.css","app.js")).issubset(build.files)
    restored=builder.get("p1", owner_id="owner-1")
    assert restored is not None
    assert restored.files["index.html"] == build.files["index.html"]

def test_website_builder_is_owner_scoped():
    builder=WebsiteBuilder(repository=MemoryRepository())
    builder.build("Create a portfolio", owner_id="owner-1", project_id="p2")
    assert builder.get("p2", owner_id="owner-2") is None
