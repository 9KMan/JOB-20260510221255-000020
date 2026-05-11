"""
Tests for CCL Script Library.
"""

import pytest
from ccl_scripts import (
    CCLScriptLibrary,
    CCLScript,
    SchemaCategory,
    ExecutionStatus,
    ExecutionResult,
    get_library,
)
from datetime import datetime


class TestCCLScriptLibrary:
    def setup_method(self):
        self.library = CCLScriptLibrary()

    def test_library_initializes_with_scripts(self):
        scripts = self.library.list_scripts()
        assert len(scripts) > 0
        assert all("name" in s for s in scripts)

    def test_list_scripts_by_category(self):
        scripts = self.library.list_scripts(SchemaCategory.PSD)
        assert all(s["category"] == "PSD" for s in scripts)

    def test_get_script(self):
        script = self.library.get_script("extract_order_proc")
        assert script is not None
        assert script.name == "extract_order_proc"

    def test_get_nonexistent_script(self):
        script = self.library.get_script("nonexistent")
        assert script is None

    def test_execute_script_dry_run(self):
        result = self.library.execute_script("extract_order_proc", {"start_date": "2024-01-01"}, dry_run=True)
        assert result.status == ExecutionStatus.SUCCESS
        assert result.script_name == "extract_order_proc"

    def test_execute_nonexistent_script(self):
        result = self.library.execute_script("nonexistent_script", dry_run=True)
        assert result.status == ExecutionStatus.FAILED
        assert "not found" in result.error_message.lower()

    def test_execution_history(self):
        self.library.execute_script("extract_order_proc", dry_run=True)
        history = self.library.get_execution_history(limit=10)
        assert len(history) >= 1

    def test_statistics(self):
        self.library.execute_script("extract_order_proc", dry_run=True)
        stats = self.library.get_statistics()
        assert "total_scripts" in stats
        assert "total_executions" in stats
        assert stats["total_scripts"] > 0


class TestCCLScript:
    def test_create_script(self):
        script = CCLScript(
            name="test_script",
            category=SchemaCategory.PSD,
            description="Test script",
            content="SELECT * FROM TEST",
            schema_area="PSD",
        )
        assert script.name == "test_script"
        assert script.category == SchemaCategory.PSD

    def test_script_to_dict(self):
        script = CCLScript(
            name="test_script",
            category=SchemaCategory.HL7,
            description="Test",
            content="SELECT * FROM TEST",
            schema_area="HSD",
        )
        d = script.to_dict()
        assert d["name"] == "test_script"
        assert d["category"] == "HL7"


class TestExecutionResult:
    def test_execution_result_to_dict(self):
        result = ExecutionResult(
            script_name="test",
            status=ExecutionStatus.SUCCESS,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            duration_seconds=1.5,
            rows_affected=100,
        )
        d = result.to_dict()
        assert d["script_name"] == "test"
        assert d["status"] == "success"
        assert d["rows_affected"] == 100


class TestGetLibrary:
    def test_singleton_pattern(self):
        lib1 = get_library()
        lib2 = get_library()
        assert lib1 is lib2