def test_training_pipeline_module_imports():
    from app.training_pipeline import assess
    assert callable(assess)
