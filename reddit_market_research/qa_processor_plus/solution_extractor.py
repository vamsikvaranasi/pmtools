"""
SolutionExtractorV2 — No Fabricated Scores

Per PM Decision #2: Raw signals only (upvotes, comment count)
Removes effectiveness and success_rate fields completely.
Extracts from ALL comments, not just Answer category.
"""

from typing import List, Dict, Any, Optional


class SolutionExtractorV2:
    """Extracts solutions and workarounds from QA conversations without fake scores."""
    
    # Solution type indicators
    SOLUTION_KEYWORDS = {
        'workaround': ['workaround', 'work around', 'temporary', 'interim', 'for now'],
        'implementation': ['implement', 'implementation', 'solution', 'approach', 'method'],
        'configuration': ['configure', 'configuration', 'setting', 'parameter', 'option'],
        'external_tool': ['tool', 'library', 'plugin', 'package', 'extension', 'service'],
        'best_practice': ['best practice', 'recommendation', 'practice', 'should', 'recommend'],
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the SolutionExtractorV2.
        
        Args:
            config: Optional configuration dictionary
        """
        if config is None:
            config = {}
        self.config = config
    
    def extract_solutions(self, conversation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract solutions from a conversation.
        
        Extracts from:
        1. Question body (OP workarounds/attempts)
        2. ALL comments (not just Answer category)
        
        Each solution has:
        - text: solution text
        - source: 'question' or 'comment'
        - post_id: ID of post
        - post_url: URL of post
        - upvotes: upvote count (raw signal)
        - solution_type: identified type from keywords
        
        NO effectiveness or success_rate fields
        
        Args:
            conversation: Conversation object with question and comments
            
        Returns:
            List of extracted solutions
        """
        solutions = []
        
        # Extract from question body
        question = conversation.get('question', {})
        if question.get('text'):
            question_solutions = self._extract_from_text(
                question.get('text'),
                source='question',
                post_id=question.get('post_id'),
                post_url=question.get('post_url'),
                upvotes=question.get('upvotes', 0)
            )
            solutions.extend(question_solutions)
        
        # Extract from ALL comments (not just Answer category)
        comments = conversation.get('comments', [])
        for comment in comments:
            comment_solutions = self._extract_from_text(
                comment.get('text', ''),
                source='comment',
                post_id=comment.get('post_id', question.get('post_id')),
                post_url=comment.get('post_url', question.get('post_url')),
                upvotes=comment.get('upvotes', 0)
            )
            solutions.extend(comment_solutions)
        
        return solutions
    
    def _extract_from_text(self, text: str, source: str, post_id: str, 
                          post_url: str, upvotes: int) -> List[Dict[str, Any]]:
        """
        Extract solutions from a text passage.
        
        Args:
            text: Text to extract from
            source: 'question' or 'comment'
            post_id: ID of post
            post_url: URL of post
            upvotes: Upvote count for this item
            
        Returns:
            List of solutions
        """
        solutions = []
        
        if not text or len(text.strip()) < 20:
            return solutions
        
        # Identify solution type
        solution_type = self._identify_solution_type(text)
        
        # If it looks like a solution, extract it
        if solution_type or self._looks_like_solution(text):
            solutions.append({
                'text': text,
                'source': source,
                'post_id': post_id,
                'post_url': post_url,
                'upvotes': upvotes,
                'solution_type': solution_type or 'general_solution'
            })
        
        return solutions
    
    def _identify_solution_type(self, text: str) -> Optional[str]:
        """Identify the type of solution based on keywords."""
        text_lower = text.lower()
        
        for sol_type, keywords in self.SOLUTION_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                return sol_type
        
        return None
    
    def _looks_like_solution(self, text: str) -> bool:
        """Heuristic to determine if text is a solution/answer."""
        text_lower = text.lower()
        
        # Check for solution indicators
        indicators = [
            'try',
            'use',
            'do',
            'change',
            'set',
            'install',
            'add',
            'remove',
            'update',
            'check',
            'verify',
            'ensure',
            'configure',
            'implement',
            'call',
            'run',
            'execute'
        ]
        
        return any(indicator in text_lower for indicator in indicators)
