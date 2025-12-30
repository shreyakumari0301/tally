"""Tests for category-based view functionality."""

import pytest
from datetime import datetime


class TestCategoryView:
    """Tests for category view functionality."""
    
    def test_category_grouping(self):
        """Test that transactions are grouped by category."""
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
                'raw_description': 'STARBUCKS',
                'description': 'Starbucks',
                'is_travel': False
            },
            {
                'date': datetime(2025, 1, 20),
                'merchant': 'Whole Foods',
                'category': 'Food',
                'subcategory': 'Grocery',
                'amount': 150.00,
                'location': 'WA',
                'source': 'AMEX',
                'raw_description': 'WHOLEFDS',
                'description': 'Whole Foods',
                'is_travel': False
            },
            {
                'date': datetime(2025, 1, 25),
                'merchant': 'Amazon',
                'category': 'Shopping',
                'subcategory': 'Online',
                'amount': 49.99,
                'location': 'WA',
                'source': 'AMEX',
                'raw_description': 'AMAZON.COM',
                'description': 'Amazon',
                'is_travel': False
            }
        ]
        
        stats = analyze_transactions(transactions)
        
        # Check by_category exists and has correct data
        assert 'by_category' in stats
        by_category = stats['by_category']
        
        # Food category should have 2 transactions
        food_key = ('Food', 'Coffee')
        grocery_key = ('Food', 'Grocery')
        assert food_key in by_category
        assert grocery_key in by_category
        assert by_category[food_key]['count'] == 1
        assert by_category[food_key]['total'] == 5.50
        assert by_category[grocery_key]['count'] == 1
        assert by_category[grocery_key]['total'] == 150.00
        
        # Shopping category should have 1 transaction
        shopping_key = ('Shopping', 'Online')
        assert shopping_key in by_category
        assert by_category[shopping_key]['count'] == 1
        assert by_category[shopping_key]['total'] == 49.99
    
    def test_category_totals(self):
        """Test that category totals are calculated correctly."""
        from tally.analyzer import analyze_transactions
        
        transactions = []
        # Add multiple Food transactions
        for i in range(5):
            transactions.append({
                'date': datetime(2025, 1, i+1),
                'merchant': 'Restaurant',
                'category': 'Food',
                'subcategory': 'Dining',
                'amount': 25.00,
                'location': 'WA',
                'source': 'AMEX',
                'raw_description': 'RESTAURANT',
                'description': 'Restaurant',
                'is_travel': False
            })
        
        # Add multiple Shopping transactions
        for i in range(3):
            transactions.append({
                'date': datetime(2025, 1, i+10),
                'merchant': 'Store',
                'category': 'Shopping',
                'subcategory': 'Retail',
                'amount': 50.00,
                'location': 'WA',
                'source': 'AMEX',
                'raw_description': 'STORE',
                'description': 'Store',
                'is_travel': False
            })
        
        stats = analyze_transactions(transactions)
        
        # Calculate category totals
        by_category = stats['by_category']
        food_total = sum(data['total'] for (cat, sub), data in by_category.items() if cat == 'Food')
        shopping_total = sum(data['total'] for (cat, sub), data in by_category.items() if cat == 'Shopping')
        
        assert food_total == 125.00  # 5 * 25
        assert shopping_total == 150.00  # 3 * 50

