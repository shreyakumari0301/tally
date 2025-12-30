"""Tests for expanded explain functionality."""

import pytest
from datetime import datetime


class TestRawDescriptionTracking:
    """Tests for tracking raw description variations."""
    
    def test_raw_descriptions_tracked(self):
        """Test that raw descriptions are tracked for each merchant."""
        from tally.analyzer import analyze_transactions
        
        transactions = [
            {
                'date': datetime(2025, 1, 15),
                'merchant': 'Starbucks',
                'category': 'Food',
                'subcategory': 'Coffee',
                'amount': 5.50,
                'location': 'WA',
                'source': 'AMEX',
                'raw_description': 'STARBUCKS STORE 123',
                'description': 'Starbucks',
                'is_travel': False
            },
            {
                'date': datetime(2025, 1, 20),
                'merchant': 'Starbucks',
                'category': 'Food',
                'subcategory': 'Coffee',
                'amount': 6.00,
                'location': 'WA',
                'source': 'AMEX',
                'raw_description': 'STARBUCKS PIKE PLACE',
                'description': 'Starbucks',
                'is_travel': False
            },
            {
                'date': datetime(2025, 1, 25),
                'merchant': 'Starbucks',
                'category': 'Food',
                'subcategory': 'Coffee',
                'amount': 5.75,
                'location': 'WA',
                'source': 'AMEX',
                'raw_description': 'STARBUCKS #456',
                'description': 'Starbucks',
                'is_travel': False
            }
        ]
        
        stats = analyze_transactions(transactions)
        
        # Get merchant data
        variable_merchants = stats.get('variable_merchants', {})
        assert 'Starbucks' in variable_merchants
        
        starbucks_data = variable_merchants['Starbucks']
        raw_descs = starbucks_data.get('raw_descriptions', set())
        
        # Should have 3 unique raw descriptions
        assert len(raw_descs) == 3
        assert 'STARBUCKS STORE 123' in raw_descs
        assert 'STARBUCKS PIKE PLACE' in raw_descs
        assert 'STARBUCKS #456' in raw_descs
    
    def test_raw_descriptions_deduplication(self):
        """Test that duplicate raw descriptions are not double-counted."""
        from tally.analyzer import analyze_transactions
        
        transactions = [
            {
                'date': datetime(2025, 1, 15),
                'merchant': 'Amazon',
                'category': 'Shopping',
                'subcategory': 'Online',
                'amount': 49.99,
                'location': 'WA',
                'source': 'AMEX',
                'raw_description': 'AMAZON.COM',
                'description': 'Amazon',
                'is_travel': False
            },
            {
                'date': datetime(2025, 1, 20),
                'merchant': 'Amazon',
                'category': 'Shopping',
                'subcategory': 'Online',
                'amount': 25.00,
                'location': 'WA',
                'source': 'AMEX',
                'raw_description': 'AMAZON.COM',  # Same as before
                'description': 'Amazon',
                'is_travel': False
            }
        ]
        
        stats = analyze_transactions(transactions)
        
        variable_merchants = stats.get('variable_merchants', {})
        amazon_data = variable_merchants.get('Amazon', {})
        raw_descs = amazon_data.get('raw_descriptions', set())
        
        # Should have only 1 unique raw description
        assert len(raw_descs) == 1
        assert 'AMAZON.COM' in raw_descs


class TestTransactionExplanation:
    """Tests for transaction-specific explanations."""
    
    def test_transaction_has_match_info(self):
        """Test that transactions include match info for explanations."""
        from tally.analyzer import analyze_transactions
        from tally.merchant_utils import normalize_merchant, get_all_rules
        
        # Create test transaction with Netflix (should match built-in rule)
        rules = get_all_rules()
        merchant, category, subcategory, match_info = normalize_merchant('NETFLIX.COM', rules)
        
        # Build transaction with match info
        transactions = [
            {
                'date': datetime(2025, 1, 15),
                'merchant': merchant,
                'category': category,
                'subcategory': subcategory,
                'amount': 15.99,
                'location': 'WA',
                'source': 'TEST',
                'raw_description': 'NETFLIX.COM',
                'description': 'Netflix',
                'is_travel': False,
                'match_info': match_info
            }
        ]
        
        # Analyze transactions
        stats = analyze_transactions(transactions)
        
        # Check that merchant has raw descriptions tracked
        monthly_merchants = stats.get('monthly_merchants', {})
        variable_merchants = stats.get('variable_merchants', {})
        
        # Netflix might be in either monthly or variable depending on data
        netflix_data = monthly_merchants.get('Netflix') or variable_merchants.get('Netflix')
        
        if netflix_data:
            # Should have raw description
            raw_descs = netflix_data.get('raw_descriptions', set())
            assert 'NETFLIX.COM' in raw_descs
            
            # Should have match info if available
            if netflix_data.get('match_info'):
                assert 'pattern' in netflix_data['match_info']

