"""
Q&A Report Generator

Generates JSON and Markdown reports for Q&A analysis.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class QAReportGenerator:
    """
    Generates comprehensive Q&A analysis reports.
    """

    def __init__(self):
        self.logger = logger

    def generate_reports(self, community: str, conversations: Dict[str, Dict[str, Any]],
                        pain_points_data: Dict[str, Any], solutions_data: Dict[str, Any],
                        output_dir: Path) -> Dict[str, Path]:
        """
        Generate all Q&A reports for a community.

        Args:
            community: Community name (e.g., 'r/replit')
            conversations: Q&A conversations data
            pain_points_data: Pain points analysis
            solutions_data: Solutions analysis
            output_dir: Output directory

        Returns:
            Dictionary mapping report types to file paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        reports = {}

        # Generate JSON report
        json_report = self._generate_json_report(
            community, conversations, pain_points_data, solutions_data
        )
        json_file = output_dir / f"q-n-a_report_{community.replace('r/', '')}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_report, f, indent=2, ensure_ascii=False)
        reports['json'] = json_file

        # Generate Markdown report
        md_report = self._generate_markdown_report(
            community, conversations, pain_points_data, solutions_data
        )
        md_file = output_dir / f"q-n-a_report_{community.replace('r/', '')}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_report)
        reports['markdown'] = md_file

        # Generate conversations JSON
        conversations_file = output_dir / f"q-n-a_conversations_{community.replace('r/', '')}.json"
        conversations_data = {
            'community': community,
            'generatedAt': datetime.utcnow().isoformat(),
            'conversations': conversations
        }
        with open(conversations_file, 'w', encoding='utf-8') as f:
            json.dump(conversations_data, f, indent=2, ensure_ascii=False)
        reports['conversations'] = conversations_file

        # Generate pain points JSON
        pain_points_file = output_dir / f"pain_points_{community.replace('r/', '')}.json"
        pain_points_full = dict(pain_points_data)
        pain_points_full.update({
            'community': community,
            'generatedAt': datetime.utcnow().isoformat()
        })
        with open(pain_points_file, 'w', encoding='utf-8') as f:
            json.dump(pain_points_full, f, indent=2, ensure_ascii=False)
        reports['pain_points'] = pain_points_file

        # Generate solutions JSON
        solutions_file = output_dir / f"solutions_{community.replace('r/', '')}.json"
        solutions_full = dict(solutions_data)
        solutions_full.update({
            'community': community,
            'generatedAt': datetime.utcnow().isoformat()
        })
        with open(solutions_file, 'w', encoding='utf-8') as f:
            json.dump(solutions_full, f, indent=2, ensure_ascii=False)
        reports['solutions'] = solutions_file

        self.logger.info(f"Generated {len(reports)} reports for {community}")
        return reports

    def _generate_json_report(self, community: str, conversations: Dict[str, Dict[str, Any]],
                             pain_points_data: Dict[str, Any], solutions_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive JSON report."""
        return {
            'community': community,
            'generatedAt': datetime.utcnow().isoformat(),
            'summary': {
                'total_conversations': len(conversations),
                'total_questions': len(conversations),
                'total_answers': sum(len(c.get('answers', [])) for c in conversations.values()),
                'pain_points': pain_points_data.get('summary', {}),
                'solutions': solutions_data.get('summary', {})
            },
            'pain_points': pain_points_data,
            'solutions': solutions_data,
            'top_conversations': self._get_top_conversations(conversations, limit=10)
        }

    def _generate_markdown_report(self, community: str, conversations: Dict[str, Dict[str, Any]],
                                 pain_points_data: Dict[str, Any], solutions_data: Dict[str, Any]) -> str:
        """Generate human-readable Markdown report."""
        lines = []

        # Header
        lines.append(f"# Q&A Analysis Report for {community}")
        lines.append("")

        # Executive Summary
        lines.append("## Executive Summary")
        lines.append("")

        summary = pain_points_data.get('summary', {})
        total_questions = summary.get('total_questions', 0)
        questions_with_pain_points = summary.get('questions_with_pain_points', 0)

        solutions_summary = solutions_data.get('summary', {})
        total_answers = solutions_summary.get('total_answers', 0)
        answers_with_solutions = solutions_summary.get('answers_with_solutions', 0)

        lines.append(f"- Total questions analyzed: {total_questions}")
        lines.append(f"- Questions with answers: {len([c for c in conversations.values() if c.get('answers')])} "
                    f"({len([c for c in conversations.values() if c.get('answers')])/max(total_questions, 1)*100:.1f}%)")

        if pain_points_data.get('pain_points'):
            top_pain_point = pain_points_data['pain_points'][0]['pain_point'] if pain_points_data['pain_points'] else 'None'
            lines.append(f"- Key pain points identified: {top_pain_point}")

        if solutions_data.get('solutions'):
            top_solution = solutions_data['solutions'][0]['solution'][:50] + '...' if solutions_data['solutions'] else 'None'
            lines.append(f"- Most common solution: {top_solution}")

        lines.append("")

        # Pain Points Section
        lines.append("## Pain Points")
        lines.append("")
        lines.append("| Pain Point | Frequency | Intensity | Category | Example Questions |")
        lines.append("|------------|-----------|-----------|----------|-------------------|")

        for pp in pain_points_data.get('pain_points', [])[:10]:  # Top 10
            pain_point = pp['pain_point'][:50] + '...' if len(pp['pain_point']) > 50 else pp['pain_point']
            example = pp.get('examples', [''])[0][:50] + '...' if pp.get('examples') else ''
            lines.append(f"| {pain_point} | {pp['frequency']} | {pp['intensity']} | {pp['category']} | {example} |")

        lines.append("")

        # Solutions Section
        lines.append("## Solutions")
        lines.append("")
        lines.append("| Problem | Solution Mentioned | Frequency | Type | Effectiveness |")
        lines.append("|---------|-------------------|-----------|------|---------------|")

        for sol in solutions_data.get('solutions', [])[:10]:  # Top 10
            problem = "General"  # Could be enhanced to map to specific problems
            solution = sol['solution'][:50] + '...' if len(sol['solution']) > 50 else sol['solution']
            lines.append(f"| {problem} | {solution} | {sol['frequency']} | {sol['type']} | {sol['effectiveness']:.2f} |")

        lines.append("")

        # Top Questions + Answers
        lines.append("## Top Questions + Answers")
        lines.append("")

        top_conversations = self._get_top_conversations(conversations, limit=5)
        for i, conv in enumerate(top_conversations, 1):
            question = conv.get('question', {})
            answers = conv.get('answers', [])

            lines.append(f"### Question {i}: {question.get('title', 'No title')}")
            lines.append(f"**Question**: {question.get('body', '')[:200]}{'...' if len(question.get('body', '')) > 200 else ''}")
            lines.append(f"**Asked by**: User ({question.get('upvotes', 0)} upvotes)")
            lines.append("")

            if answers:
                top_answer = answers[0]
                lines.append(f"**Top Answer** (by User, {top_answer.get('upvotes', 0)} upvotes):")
                lines.append(f"{top_answer.get('body', '')[:300]}{'...' if len(top_answer.get('body', '')) > 300 else ''}")
                lines.append("")

                if len(answers) > 1:
                    lines.append("**Other Answers**:")
                    for j, answer in enumerate(answers[1:3], 1):  # Show next 2
                        brief = answer.get('body', '')[:100] + '...' if len(answer.get('body', '')) > 100 else answer.get('body', '')
                        lines.append(f"- {brief}")
                    lines.append("")

        return "\n".join(lines)

    def _get_top_conversations(self, conversations: Dict[str, Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
        """Get top conversations by total engagement."""
        conv_list = list(conversations.values())

        # Sort by question upvotes + top answer upvotes
        conv_list.sort(key=lambda c: c.get('question', {}).get('upvotes', 0) +
                      (c.get('answers', [{}])[0].get('upvotes', 0) if c.get('answers') else 0),
                      reverse=True)

        return conv_list[:limit]