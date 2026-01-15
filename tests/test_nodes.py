import pytest
from unittest.mock import MagicMock, patch
from stock_scanner.nodes.screener import screener_node
from stock_scanner.nodes.volume import volume_node
from stock_scanner.nodes.analyst import analyst_node
from stock_scanner.state import GraphState
from stock_scanner.config import config

@pytest.fixture
def mock_fmp_client():
    with patch('stock_scanner.nodes.screener.FMPClient') as MockClient:
        yield MockClient.return_value

@pytest.fixture
def mock_volume_client():
    with patch('stock_scanner.nodes.volume.FMPClient') as MockClient:
        yield MockClient.return_value

@pytest.fixture
def mock_analyst_client():
    with patch('stock_scanner.nodes.analyst.FMPClient') as MockClient:
        yield MockClient.return_value

def test_screener_node(mock_fmp_client):
    mock_fmp_client.get_stock_screener.return_value = [{"symbol": "AAPL", "volume": 1000000}]
    
    result = screener_node({})
    
    assert "candidates" in result
    assert len(result["candidates"]) == 1
    assert result["candidates"][0]["symbol"] == "AAPL"

def test_volume_node_spike(mock_volume_client):
    # Mock candidate
    state = {"candidates": [{"symbol": "TEST", "volume": 1500}]}
    
    # Mock history (Avg vol = 1000)
    mock_history = [{'volume': 1500}] # Today/Current
    mock_history.extend([{'volume': 1000} for _ in range(35)])
    
    mock_volume_client.get_historical_price.return_value = {'historical': mock_history}
    
    # Run
    result = volume_node(state)
    
    assert "spiked_stocks" in result
    assert len(result["spiked_stocks"]) == 1
    assert result["spiked_stocks"][0]['candidate']['symbol'] == "TEST"
    assert result["spiked_stocks"][0]['volume_analysis']['is_spike'] == True

def test_volume_node_no_spike(mock_volume_client):
    state = {"candidates": [{"symbol": "DUD", "volume": 1000}]}
    
    # Avg vol = 1000
    mock_history = [{'volume': 1000}] 
    mock_history.extend([{'volume': 1000} for _ in range(35)])
    
    mock_volume_client.get_historical_price.return_value = {'historical': mock_history}
    
    result = volume_node(state)
    
    assert "spiked_stocks" in result
    assert len(result["spiked_stocks"]) == 0

def test_analyst_node_upside(mock_analyst_client):
    state = {"spiked_stocks": [{
        "candidate": {"symbol": "UP", "price": 100},
        "volume_analysis": {} 
    }]}
    
    # Target 150 (+50% upside)
    mock_analyst_client.get_price_target.return_value = [{'targetConsensus': 150}]
    
    result = analyst_node(state)
    
    assert "analyst_picks" in result
    assert len(result["analyst_picks"]) == 1
    assert result["analyst_picks"][0]['analyst_rating']['upside_percent'] == 50.0

def test_analyst_node_no_upside(mock_analyst_client):
    state = {"spiked_stocks": [{
        "candidate": {"symbol": "DOWN", "price": 100},
        "volume_analysis": {}
    }]}
    
    # Target 105 (+5% upside, below default 20%)
    mock_analyst_client.get_price_target.return_value = [{'targetConsensus': 105}]
    
    result = analyst_node(state)
    
    assert "analyst_picks" in result
    assert len(result["analyst_picks"]) == 0
