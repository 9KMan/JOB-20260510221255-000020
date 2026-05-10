"""Tests for CCL Script Library."""

import pytest
from datetime import datetime
from ccl_scripts import CCLScript, CCLScriptLibrary, ScriptCategory


def test_ccl_script_library_register():
    library = CCLScriptLibrary()
    script = CCLScript(
        name="test_script",
        category=ScriptCategory.HL7,
        description="Test script",
        schema="PSD",
        created_ts=datetime.now(),
    )
    library.register(script)
    assert library.get("test_script") is not None


def test_ccl_script_library_get():
    library = CCLScriptLibrary()
    script = CCLScript(
        name="test_script",
        category=ScriptCategory.HL7,
        description="Test script",
        schema="PSD",
        created_ts=datetime.now(),
    )
    library.register(script)
    retrieved = library.get("test_script")
    assert retrieved is not None
    assert retrieved.name == "test_script"


def test_ccl_script_library_list_by_category():
    library = CCLScriptLibrary()
    library.register(CCLScript(name="s1", category=ScriptCategory.HL7, description="", schema="PSD", created_ts=datetime.now()))
    library.register(CCLScript(name="s2", category=ScriptCategory.FIN, description="", schema="FIN", created_ts=datetime.now()))
    library.register(CCLScript(name="s3", category=ScriptCategory.HL7, description="", schema="PSD", created_ts=datetime.now()))

    hl7_scripts = library.list_by_category(ScriptCategory.HL7)
    assert len(hl7_scripts) == 2


def test_ccl_script_library_all():
    library = CCLScriptLibrary()
    library.register(CCLScript(name="s1", category=ScriptCategory.HL7, description="", schema="PSD", created_ts=datetime.now()))
    library.register(CCLScript(name="s2", category=ScriptCategory.FIN, description="", schema="FIN", created_ts=datetime.now()))

    all_scripts = library.all()
    assert len(all_scripts) == 2
