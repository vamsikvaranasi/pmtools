"""
Pain Point and Solution Extractors

Extract pain points from questions and solutions from answers.
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict, Counter
import logging

logger = logging.getLogger(__name__)


class PainPointExtractor:
    """
    Extracts pain points from question content.
    """

    # Keywords for different pain point categories
    PAIN_POINT_KEYWORDS = {
        'technical': [
            'bug', 'error', 'crash', 'broken', 'not working', 'failed', 'issue', 'problem',
            'doesn\'t work', 'won\'t load', 'stuck', 'freezes', 'slow', 'performance',
            'compatibility', 'integration', 'deployment', 'setup', 'configuration'
        ],
        'usability': [
            'confusing', 'difficult', 'hard to', 'complicated', 'not intuitive', 'unclear',
            'can\'t find', 'lost', 'frustrating', 'annoying', 'bad ux', 'bad ui'
        ],
        'feature': [
            'missing', 'no way to', 'can\'t', 'need to', 'wish', 'feature request',
            'doesn\'t have', 'lacks', 'missing feature', 'not available'
        ],
        'pricing': [
            'expensive', 'cost', 'price', 'too much', 'afford', 'cheap', 'overpriced',
            'subscription', 'billing', 'payment'
        ],
        'support': [
            'documentation', 'docs', 'help', 'support', 'tutorial', 'guide', 'examples',
            'no info', 'unclear docs', 'bad docs'
        ]
    }

    def __init__(self):
        self.logger = logger

    def extract_pain_points(self, conversations: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract pain points from Q&A conversations.

        Args:
            conversations: Dictionary of Q&A conversations

        Returns:
            Dictionary with pain points analysis
        """
        pain_points = []
        pain_point_counter = Counter()
        category_counter = Counter()

        for conversation in conversations.values():
            question = conversation.get('question', {})
            question_text = self._get_full_question_text(question)

            # Extract pain points from question
            question_pain_points = self._extract_from_text(question_text)

            if question_pain_points:
                # Calculate intensity for each pain point
                for pain_point in question_pain_points:
                    intensity = self._calculate_intensity(
                        pain_point,
                        question.get('upvotes', 0),
                        question.get('analysis', {}).get('sentiment', '')
                    )

                    pain_point_data = {
                        'pain_point': pain_point,
                        'frequency': 1,  # Will be aggregated later
                        'intensity': intensity,
                        'category': self._categorize_pain_point(pain_point),
                        'sentiment_impact': self._get_sentiment_score(question.get('analysis', {})),
                        'examples': [question_text[:100] + '...' if len(question_text) > 100 else question_text],
                        'associated_solutions': []  # Will be filled from answers
                    }

                    pain_points.append(pain_point_data)
                    pain_point_counter[pain_point] += 1
                    category_counter[pain_point_data['category']] += 1

        # Aggregate and sort pain points
        aggregated_pain_points = self._aggregate_pain_points(pain_points, pain_point_counter)

        # Calculate summary statistics
        total_questions = len(conversations)
        questions_with_pain_points = len([c for c in conversations.values()
                                        if self._extract_from_text(
                                            self._get_full_question_text(c.get('question', {}))
                                        )])

        summary = {
            'total_questions': total_questions,
            'questions_with_pain_points': questions_with_pain_points,
            'unique_pain_points': len(aggregated_pain_points),
            'total_pain_point_mentions': sum(p['frequency'] for p in aggregated_pain_points)
        }

        return {
            'summary': summary,
            'pain_points': aggregated_pain_points,
            'categories': dict(category_counter)
        }

    def _extract_from_text(self, text: str) -> List[str]:
        """Extract pain points from text using keyword matching."""
        if not text:
            return []

        text_lower = text.lower()
        pain_points = []

        for category, keywords in self.PAIN_POINT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    # Extract surrounding context as pain point description
                    pain_point = self._extract_context(text, keyword)
                    if pain_point and pain_point not in pain_points:
                        pain_points.append(pain_point)

        return pain_points

    def _extract_context(self, text: str, keyword: str, context_words: int = 5) -> str:
        """Extract context around a keyword."""
        # Split text into sentences
        sentences = re.split(r'[.!?]+', text)
        keyword_lower = keyword.lower()

        # Find sentence containing keyword
        for sentence in sentences:
            if keyword_lower in sentence.lower():
                # Clean and return the sentence
                clean_sentence = sentence.strip()
                if len(clean_sentence) > 100:
                    return clean_sentence[:100] + "..."
                return clean_sentence

        # Fallback to word-based context if no sentence found
        words = text.split()
        for i, word in enumerate(words):
            if keyword_lower in word.lower():
                start = max(0, i - context_words)
                end = min(len(words), i + context_words + 1)
                context = ' '.join(words[start:end])
                if len(context) > 100:
                    return context[:100] + "..."
                return context

        return keyword

    def _calculate_intensity(self, pain_point: str, upvotes: int, sentiment: str) -> str:
        """Calculate pain point intensity."""
        base_intensity = 1

        # Factor in upvotes
        if upvotes > 10:
            base_intensity += 1
        elif upvotes > 50:
            base_intensity += 2

        # Factor in sentiment
        if sentiment == 'negative':
            base_intensity += 1

        # Factor in keywords indicating severity
        severe_keywords = ['crash', 'broken', 'doesn\'t work', 'failed', 'stuck']
        if any(keyword in pain_point.lower() for keyword in severe_keywords):
            base_intensity += 1

        if base_intensity >= 4:
            return 'high'
        elif base_intensity >= 2:
            return 'medium'
        else:
            return 'low'

    def _categorize_pain_point(self, pain_point: str) -> str:
        """Categorize a pain point."""
        text_lower = pain_point.lower()

        for category, keywords in self.PAIN_POINT_KEYWORDS.items():
            if any(keyword in text_lower for keyword in keywords):
                return category

        return 'other'

    def _get_sentiment_score(self, analysis: Dict[str, Any]) -> float:
        """Get sentiment score from analysis."""
        sentiment = analysis.get('sentiment', '')
        if sentiment == 'positive':
            return 0.5
        elif sentiment == 'negative':
            return -0.5
        else:
            return 0.0

    def _get_full_question_text(self, question: Dict[str, Any]) -> str:
        """Get full question text from title and body."""
        title = question.get('title', '')
        body = question.get('body', '')
        return f"{title} {body}".strip()

    def _aggregate_pain_points(self, pain_points: List[Dict[str, Any]],
                             counter: Counter) -> List[Dict[str, Any]]:
        """Aggregate pain points by frequency."""
        aggregated = {}

        for pp in pain_points:
            name = pp['pain_point']
            if name not in aggregated:
                aggregated[name] = {
                    'frequency': counter[name],
                    'intensity': pp['intensity'],
                    'category': pp['category'],
                    'sentiment_impact': pp['sentiment_impact'],
                    'examples': [pp['examples'][0]],
                    'associated_solutions': []
                }
            elif pp['examples'][0] not in aggregated[name]['examples']:
                aggregated[name]['examples'].append(pp['examples'][0])

        # Sort by frequency descending
        return sorted(
            [{'pain_point': k, **v} for k, v in aggregated.items()],
            key=lambda x: x['frequency'],
            reverse=True
        )


class SolutionExtractor:
    """
    Extracts solutions from answer content.
    """

    # Keywords for solution types
    SOLUTION_KEYWORDS = {
        'tool': [
            'use', 'try', 'install', 'download', 'setup', 'configure', 'run',
            'docker', 'git', 'npm', 'pip', 'vscode', 'chrome'
        ],
        'recommendation': [
            'check', 'make sure', 'ensure', 'verify', 'update', 'upgrade',
            'restart', 'clear', 'reset', 'change', 'set'
        ],
        'workaround': [
            'instead', 'alternative', 'workaround', 'temporary', 'hack',
            'bypass', 'manually', 'copy-paste', 'hardcode'
        ]
    }

    SOLUTION_INDICATORS = [
        'you can', 'try this', 'solution', 'fix', 'here\'s how', 'to resolve',
        'the issue is', 'you need to', 'simply', 'just', 'easy way'
    ]

    def __init__(self):
        self.logger = logger

    def extract_solutions(self, conversations: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract solutions from Q&A conversations.

        Args:
            conversations: Dictionary of Q&A conversations

        Returns:
            Dictionary with solutions analysis
        """
        solutions = []
        solution_counter = Counter()
        type_counter = Counter()

        for conversation in conversations.values():
            answers = conversation.get('answers', [])

            for answer in answers:
                answer_text = answer.get('body', '')

                # Extract solutions from answer
                answer_solutions = self._extract_from_text(answer_text)

                for solution in answer_solutions:
                    solution_type = self._categorize_solution(solution)
                    effectiveness = self._calculate_effectiveness(
                        answer.get('upvotes', 0),
                        solution_type
                    )

                    solution_data = {
                        'solution': solution,
                        'frequency': 1,  # Will be aggregated later
                        'type': solution_type,
                        'effectiveness': effectiveness,
                        'success_rate': effectiveness * 100,  # Percentage
                        'examples': [answer_text[:100] + '...' if len(answer_text) > 100 else answer_text],
                        'associated_pain_points': []  # Will be mapped from questions
                    }

                    solutions.append(solution_data)
                    solution_counter[solution] += 1
                    type_counter[solution_type] += 1

        # Aggregate and sort solutions
        aggregated_solutions = self._aggregate_solutions(solutions, solution_counter)

        # Calculate summary statistics
        total_answers = sum(len(c.get('answers', [])) for c in conversations.values())
        answers_with_solutions = len([s for s in solutions if s['solution']])

        summary = {
            'total_answers': total_answers,
            'answers_with_solutions': answers_with_solutions,
            'unique_solutions': len(aggregated_solutions),
            'total_solution_mentions': sum(s['frequency'] for s in aggregated_solutions)
        }

        return {
            'summary': summary,
            'solutions': aggregated_solutions,
            'solution_types': dict(type_counter)
        }

    def _extract_from_text(self, text: str) -> List[str]:
        """Extract solutions from text."""
        if not text:
            return []

        text_lower = text.lower()
        solutions = []

        # Check for solution indicators
        has_solution_indicator = any(indicator in text_lower for indicator in self.SOLUTION_INDICATORS)

        if has_solution_indicator:
            # Extract sentences that contain solution indicators
            sentences = re.split(r'[.!?]+', text)
            for sentence in sentences:
                sentence_lower = sentence.lower()
                if any(indicator in sentence_lower for indicator in self.SOLUTION_INDICATORS):
                    solution = sentence.strip()
                    if solution and len(solution) > 10:  # Minimum length
                        solutions.append(solution)

        return solutions

    def _categorize_solution(self, solution: str) -> str:
        """Categorize a solution."""
        text_lower = solution.lower()

        for solution_type, keywords in self.SOLUTION_KEYWORDS.items():
            if any(keyword in text_lower for keyword in keywords):
                return solution_type

        return 'recommendation'  # Default

    def _calculate_effectiveness(self, upvotes: int, solution_type: str) -> float:
        """Calculate solution effectiveness based on upvotes and type."""
        base_effectiveness = 0.5

        # Factor in upvotes
        if upvotes > 5:
            base_effectiveness += 0.2
        elif upvotes > 20:
            base_effectiveness += 0.3

        # Factor in solution type
        type_multipliers = {
            'tool': 1.2,      # Tools tend to be more effective
            'recommendation': 1.0,
            'workaround': 0.8  # Workarounds are less ideal
        }

        base_effectiveness *= type_multipliers.get(solution_type, 1.0)

        return min(base_effectiveness, 1.0)  # Cap at 1.0

    def _aggregate_solutions(self, solutions: List[Dict[str, Any]],
                           counter: Counter) -> List[Dict[str, Any]]:
        """Aggregate solutions by frequency."""
        aggregated = {}

        for sol in solutions:
            name = sol['solution']
            if name not in aggregated:
                aggregated[name] = {
                    'frequency': counter[name],
                    'type': sol['type'],
                    'effectiveness': sol['effectiveness'],
                    'success_rate': sol['success_rate'],
                    'examples': [sol['examples'][0]],
                    'associated_pain_points': []
                }
            elif sol['examples'][0] not in aggregated[name]['examples']:
                aggregated[name]['examples'].append(sol['examples'][0])

        # Sort by frequency descending
        return sorted(
            [{'solution': k, **v} for k, v in aggregated.items()],
            key=lambda x: x['frequency'],
            reverse=True
        )