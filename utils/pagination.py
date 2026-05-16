"""
Pagination helper functions for consistent paginated API responses.
Provides utilities for extracting pagination parameters and formatting responses.
"""

from flask import request
from utils.schemas import PaginationQuerySchema, get_paginated_response_data, validate_request


class PaginationHelper:
    """Helper class for handling pagination in API endpoints."""

    @staticmethod
    def get_pagination_params():
        """
        Extract and validate pagination parameters from request.
        
        Returns:
            Dictionary with page, per_page, sort_by, sort_order
        """
        params = {
            'page': request.args.get('page', 1, type=int),
            'per_page': request.args.get('per_page', 20, type=int),
            'sort_by': request.args.get('sort_by', 'created_at', type=str),
            'sort_order': request.args.get('sort_order', 'desc', type=str),
        }
        
        # Validate parameters
        is_valid, result = validate_request(PaginationQuerySchema, params)
        if not is_valid:
            return None, result
        
        return result, None

    @staticmethod
    def paginate(items, total, page, per_page):
        """
        Format paginated response.
        
        Args:
            items: List of items for current page
            total: Total number of items
            page: Current page number
            per_page: Items per page
            
        Returns:
            Formatted response dict
        """
        return get_paginated_response_data(items, page, per_page, total)

    @staticmethod
    def apply_sort(query, sort_by, sort_order, allowed_fields=None):
        """
        Apply sorting to SQLAlchemy query.
        
        Args:
            query: SQLAlchemy query object
            sort_by: Field to sort by
            sort_order: 'asc' or 'desc'
            allowed_fields: List of allowed sort fields
            
        Returns:
            Sorted query object
        """
        if allowed_fields and sort_by not in allowed_fields:
            sort_by = allowed_fields[0]
        
        if sort_order.lower() == 'asc':
            query = query.order_by(sort_by.asc())
        else:
            query = query.order_by(sort_by.desc())
        
        return query

    @staticmethod
    def sql_paginate(query, page, per_page):
        """
        Apply limit and offset to SQLAlchemy query.
        
        Args:
            query: SQLAlchemy query object
            page: Page number (1-indexed)
            per_page: Items per page
            
        Returns:
            Tuple of (paginated_query, total_count)
        """
        total = query.count()
        offset = (page - 1) * per_page
        items = query.offset(offset).limit(per_page).all()
        return items, total
