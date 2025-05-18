"""Token utilities for managing response sizes within MCP token limits."""

import json
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass


@dataclass
class TokenEstimate:
    """Estimates for token usage."""
    text_length: int
    estimated_tokens: int
    
    @property
    def is_within_limit(self) -> bool:
        """Check if estimate is within the 25k token limit."""
        return self.estimated_tokens < 25000


class TokenCounter:
    """Utility for estimating token counts and managing responses within limits."""
    
    # Conservative estimate: 1 token ≈ 4 characters (English text)
    # For code and structured data, we use more conservative ratios
    CHARS_PER_TOKEN_TEXT = 4
    CHARS_PER_TOKEN_CODE = 3
    CHARS_PER_TOKEN_JSON = 2.5
    
    # Token limit for MCP responses
    MAX_TOKENS = 25000
    SAFE_LIMIT = 23000  # Leave buffer for response wrapper
    
    @staticmethod
    def estimate_tokens(text: str, content_type: str = "text") -> TokenEstimate:
        """Estimate token count for given text.
        
        Args:
            text: Text to estimate
            content_type: Type of content ("text", "code", "json")
            
        Returns:
            TokenEstimate with character count and estimated tokens
        """
        length = len(text)
        
        if content_type == "code":
            ratio = TokenCounter.CHARS_PER_TOKEN_CODE
        elif content_type == "json":
            ratio = TokenCounter.CHARS_PER_TOKEN_JSON
        else:
            ratio = TokenCounter.CHARS_PER_TOKEN_TEXT
            
        estimated_tokens = int(length / ratio)
        
        return TokenEstimate(
            text_length=length,
            estimated_tokens=estimated_tokens
        )
    
    @staticmethod
    def estimate_json_tokens(data: Any) -> TokenEstimate:
        """Estimate tokens for JSON-serializable data."""
        json_str = json.dumps(data, indent=2)
        return TokenCounter.estimate_tokens(json_str, "json")
    
    @staticmethod
    def can_fit_in_response(text: str, current_size: int = 0) -> bool:
        """Check if text can fit in response given current size."""
        estimate = TokenCounter.estimate_tokens(text)
        return (current_size + estimate.estimated_tokens) < TokenCounter.SAFE_LIMIT
    
    @staticmethod
    def truncate_to_fit(text: str, max_tokens: int = None) -> Tuple[str, bool]:
        """Truncate text to fit within token limit.
        
        Returns:
            Tuple of (truncated_text, was_truncated)
        """
        if max_tokens is None:
            max_tokens = TokenCounter.SAFE_LIMIT
            
        estimate = TokenCounter.estimate_tokens(text)
        
        if estimate.estimated_tokens <= max_tokens:
            return text, False
            
        # Calculate approximate character limit
        char_limit = int(max_tokens * TokenCounter.CHARS_PER_TOKEN_TEXT)
        
        # Truncate with ellipsis
        truncated = text[:char_limit - 50] + "\n\n... [Content truncated due to token limit]"
        
        return truncated, True


class PaginatedResponse:
    """Manages paginated responses for large data sets."""
    
    def __init__(self, items: List[Any], page_size: Optional[int] = None):
        """Initialize paginated response.
        
        Args:
            items: List of items to paginate
            page_size: Items per page (None for automatic sizing)
        """
        self.items = items
        self.total_items = len(items)
        self.page_size = page_size
        self.total_pages = 1
        
        if page_size:
            self.total_pages = (self.total_items + page_size - 1) // page_size
        else:
            # Auto-calculate pages based on token estimates
            self._calculate_pages()
    
    def _calculate_pages(self):
        """Calculate optimal pagination based on token limits."""
        pages = []
        current_page = []
        current_tokens = 0
        
        for item in self.items:
            # Estimate tokens for this item
            item_estimate = TokenCounter.estimate_json_tokens(item)
            
            # Check if adding this item would exceed limit
            if current_tokens + item_estimate.estimated_tokens > TokenCounter.SAFE_LIMIT:
                if current_page:
                    pages.append(current_page)
                    current_page = [item]
                    current_tokens = item_estimate.estimated_tokens
                else:
                    # Single item exceeds limit - must be handled specially
                    pages.append([item])
                    current_page = []
                    current_tokens = 0
            else:
                current_page.append(item)
                current_tokens += item_estimate.estimated_tokens
        
        if current_page:
            pages.append(current_page)
        
        self.pages = pages
        self.total_pages = len(pages)
    
    def get_page(self, page_number: int) -> Dict[str, Any]:
        """Get a specific page of results.
        
        Args:
            page_number: 1-based page number
            
        Returns:
            Dictionary with page data and metadata
        """
        if not 1 <= page_number <= self.total_pages:
            raise ValueError(f"Page {page_number} out of range (1-{self.total_pages})")
        
        if hasattr(self, 'pages'):
            # Auto-calculated pages
            page_items = self.pages[page_number - 1]
        else:
            # Fixed page size
            start_idx = (page_number - 1) * self.page_size
            end_idx = min(start_idx + self.page_size, self.total_items)
            page_items = self.items[start_idx:end_idx]
        
        return {
            "items": page_items,
            "page": page_number,
            "total_pages": self.total_pages,
            "total_items": self.total_items,
            "has_next": page_number < self.total_pages,
            "has_previous": page_number > 1
        }


class ResponseBuilder:
    """Builds token-aware responses for MCP tools."""
    
    def __init__(self):
        self.token_counter = TokenCounter()
        self.current_size = 0
    
    def add_metadata_only(self, items: List[Any], 
                         metadata_extractor: callable) -> List[Dict[str, Any]]:
        """Convert items to metadata-only representation.
        
        Args:
            items: Full items to convert
            metadata_extractor: Function to extract metadata from each item
            
        Returns:
            List of metadata dictionaries
        """
        metadata_list = []
        
        for item in items:
            metadata = metadata_extractor(item)
            estimate = TokenCounter.estimate_json_tokens(metadata)
            
            # Check if we can fit this metadata
            if self.current_size + estimate.estimated_tokens < TokenCounter.SAFE_LIMIT:
                metadata_list.append(metadata)
                self.current_size += estimate.estimated_tokens
            else:
                # Add truncation indicator
                metadata_list.append({
                    "id": "truncated",
                    "message": f"Response truncated. {len(items) - len(metadata_list)} items omitted."
                })
                break
        
        return metadata_list
    
    def build_search_results(self, results: List[Dict[str, Any]], 
                           snippet_length: int = 1000) -> List[Dict[str, Any]]:
        """Build search results with snippets instead of full content.
        
        Args:
            results: Full search results
            snippet_length: Max characters per snippet
            
        Returns:
            Results with content replaced by snippets
        """
        snippet_results = []
        
        for result in results:
            # Create snippet version
            snippet_result = result.copy()
            
            if 'content' in snippet_result and len(snippet_result['content']) > snippet_length:
                # Create snippet with context
                content = snippet_result['content']
                snippet = content[:snippet_length]
                
                # Try to end at a sentence
                last_period = snippet.rfind('.')
                if last_period > snippet_length * 0.8:
                    snippet = snippet[:last_period + 1]
                
                snippet_result['content'] = snippet
                snippet_result['content_truncated'] = True
                snippet_result['full_length'] = len(content)
            
            estimate = TokenCounter.estimate_json_tokens(snippet_result)
            
            if self.current_size + estimate.estimated_tokens < TokenCounter.SAFE_LIMIT:
                snippet_results.append(snippet_result)
                self.current_size += estimate.estimated_tokens
            else:
                break
        
        return snippet_results