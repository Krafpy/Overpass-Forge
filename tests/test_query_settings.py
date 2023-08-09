from overpassforge.builder import Settings
from overpassforge.errors import InvalidQuerySettings
import pytest
from datetime import datetime

def test_basics():
    assert Settings("json", 10, 10000, (10.0,20.0,30.0,40.0))._compile() == \
        """[out:json][timeout:10][maxsize:10000][bbox:10.0,20.0,30.0,40.0];"""

def test_negative_timeout():
    with pytest.raises(InvalidQuerySettings):
        assert Settings(timeout=0)._compile()
    
    with pytest.raises(InvalidQuerySettings):
        assert Settings(timeout=-5)._compile()

def test_valid_csv():
    assert Settings("csv", csv_fields=("::id", "name"))._compile() == \
    """[out:csv("::id","name"; true)][timeout:25];"""

def test_valid_csv_no_header():
    assert Settings("csv", csv_fields=("::id", "name"), csv_header_line=False)._compile() == \
    """[out:csv("::id","name"; false)][timeout:25];"""

def test_invalid_csv():
    with pytest.raises(InvalidQuerySettings):
        assert Settings("csv")._compile()

def test_valid_csv_separator():
    assert Settings("csv", csv_fields=("::id", "name"), csv_separator='|')._compile() == \
    """[out:csv("::id","name"; true; "|")][timeout:25];"""

def test_date():
    assert Settings(date=datetime(2023, 1, 1))._compile() == \
        """[out:json][timeout:25][date:"2023-01-01T00:00:00Z"];"""

def test_diff():
    assert Settings(diff=(datetime(2023, 1, 1),))._compile() == \
        """[out:json][timeout:25][diff:"2023-01-01T00:00:00Z"];"""
    
    assert Settings(diff=(datetime(2023, 1, 1), datetime(2023, 4, 1)))._compile() == \
        """[out:json][timeout:25][diff:"2023-01-01T00:00:00Z","2023-04-01T00:00:00Z"];"""