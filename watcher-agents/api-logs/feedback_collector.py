#!/usr/bin/env python3
"""
Feedback Collection System
Collects human feedback on generated reports to improve analysis
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class FeedbackCollector:
    """Collects and stores feedback on analysis reports"""
    
    def __init__(self):
        self.feedback_dir = Path(__file__).parent / "feedback"
        self.feedback_dir.mkdir(exist_ok=True)
        self.feedback_file = self.feedback_dir / "feedback_log.json"
        self.feedback_data = self._load_feedback()
    
    def _load_feedback(self) -> list:
        """Load existing feedback data"""
        if self.feedback_file.exists():
            with open(self.feedback_file, 'r') as f:
                return json.load(f)
        return []
    
    def _save_feedback(self):
        """Save feedback data to file"""
        with open(self.feedback_file, 'w') as f:
            json.dump(self.feedback_data, f, indent=2)
    
    def collect_feedback(self, report_file: str) -> Dict:
        """Interactively collect feedback on a report"""
        print("\n" + "="*60)
        print("FEEDBACK COLLECTION")
        print("="*60)
        print(f"Report: {report_file}")
        print("\nPlease provide feedback on the analysis report:")
        print("-" * 60)
        
        feedback = {
            'report_file': report_file,
            'timestamp': datetime.now().isoformat(),
            'ratings': {},
            'comments': {},
            'action_taken': None
        }
        
        # Collect ratings
        print("\nRate the following aspects (1-5, or press Enter to skip):")
        
        aspects = [
            ('accuracy', 'How accurate was the error detection?'),
            ('relevance', 'How relevant were the identified patterns?'),
            ('actionability', 'How actionable were the recommendations?'),
            ('clarity', 'How clear was the report presentation?'),
            ('completeness', 'How complete was the analysis?')
        ]
        
        for aspect, question in aspects:
            while True:
                response = input(f"{question} (1-5): ").strip()
                if not response:
                    break
                try:
                    rating = int(response)
                    if 1 <= rating <= 5:
                        feedback['ratings'][aspect] = rating
                        break
                    else:
                        print("Please enter a number between 1 and 5")
                except ValueError:
                    print("Please enter a valid number or press Enter to skip")
        
        # Collect specific feedback
        print("\n" + "-" * 60)
        
        # False positives
        false_positives = input("Were there any false positives? (describe or press Enter): ").strip()
        if false_positives:
            feedback['comments']['false_positives'] = false_positives
        
        # Missed issues
        missed = input("Were any issues missed? (describe or press Enter): ").strip()
        if missed:
            feedback['comments']['missed_issues'] = missed
        
        # Useful insights
        useful = input("What was most useful? (describe or press Enter): ").strip()
        if useful:
            feedback['comments']['useful_insights'] = useful
        
        # Improvements
        improvements = input("Suggested improvements? (describe or press Enter): ").strip()
        if improvements:
            feedback['comments']['improvements'] = improvements
        
        # Action taken
        print("\n" + "-" * 60)
        print("What action did you take based on this report?")
        print("1. Investigated and fixed issues")
        print("2. Monitored but no action needed")
        print("3. False alarm - ignored")
        print("4. Escalated to team")
        print("5. Other")
        
        action_choice = input("Enter choice (1-5) or press Enter to skip: ").strip()
        
        action_map = {
            '1': 'fixed_issues',
            '2': 'monitored',
            '3': 'false_alarm',
            '4': 'escalated',
            '5': 'other'
        }
        
        if action_choice in action_map:
            feedback['action_taken'] = action_map[action_choice]
            if action_choice == '5':
                other_action = input("Describe other action: ").strip()
                if other_action:
                    feedback['comments']['other_action'] = other_action
        
        # Overall comments
        overall = input("\nAny other comments? (press Enter to skip): ").strip()
        if overall:
            feedback['comments']['overall'] = overall
        
        # Save feedback
        self.feedback_data.append(feedback)
        self._save_feedback()
        
        print("\n" + "="*60)
        print("Thank you for your feedback!")
        print("="*60)
        
        return feedback
    
    def analyze_feedback(self) -> Dict:
        """Analyze collected feedback to identify improvement areas"""
        if not self.feedback_data:
            return {'message': 'No feedback data available'}
        
        analysis = {
            'total_feedback': len(self.feedback_data),
            'average_ratings': {},
            'common_issues': [],
            'action_distribution': {},
            'improvement_suggestions': []
        }
        
        # Calculate average ratings
        rating_sums = {}
        rating_counts = {}
        
        for feedback in self.feedback_data:
            for aspect, rating in feedback.get('ratings', {}).items():
                rating_sums[aspect] = rating_sums.get(aspect, 0) + rating
                rating_counts[aspect] = rating_counts.get(aspect, 0) + 1
        
        for aspect in rating_sums:
            analysis['average_ratings'][aspect] = round(
                rating_sums[aspect] / rating_counts[aspect], 2
            )
        
        # Analyze actions taken
        for feedback in self.feedback_data:
            action = feedback.get('action_taken')
            if action:
                analysis['action_distribution'][action] = \
                    analysis['action_distribution'].get(action, 0) + 1
        
        # Collect improvement suggestions
        for feedback in self.feedback_data:
            if 'improvements' in feedback.get('comments', {}):
                analysis['improvement_suggestions'].append(
                    feedback['comments']['improvements']
                )
        
        # Identify common issues
        false_positive_count = sum(
            1 for f in self.feedback_data 
            if 'false_positives' in f.get('comments', {})
        )
        missed_issues_count = sum(
            1 for f in self.feedback_data 
            if 'missed_issues' in f.get('comments', {})
        )
        
        if false_positive_count > len(self.feedback_data) * 0.3:
            analysis['common_issues'].append('High false positive rate')
        
        if missed_issues_count > len(self.feedback_data) * 0.3:
            analysis['common_issues'].append('Missing important issues')
        
        return analysis
    
    def generate_feedback_report(self) -> str:
        """Generate a report on collected feedback"""
        analysis = self.analyze_feedback()
        
        report = ["# Feedback Analysis Report", ""]
        report.append(f"Total feedback collected: {analysis['total_feedback']}")
        report.append("")
        
        if analysis['average_ratings']:
            report.append("## Average Ratings")
            for aspect, rating in analysis['average_ratings'].items():
                stars = '⭐' * int(rating)
                report.append(f"- {aspect.capitalize()}: {rating}/5 {stars}")
            report.append("")
        
        if analysis['action_distribution']:
            report.append("## Actions Taken")
            for action, count in analysis['action_distribution'].items():
                percentage = (count / analysis['total_feedback']) * 100
                report.append(f"- {action.replace('_', ' ').capitalize()}: "
                            f"{count} ({percentage:.1f}%)")
            report.append("")
        
        if analysis['common_issues']:
            report.append("## Common Issues")
            for issue in analysis['common_issues']:
                report.append(f"- {issue}")
            report.append("")
        
        if analysis['improvement_suggestions']:
            report.append("## Improvement Suggestions")
            for i, suggestion in enumerate(analysis['improvement_suggestions'][:5], 1):
                report.append(f"{i}. {suggestion}")
            report.append("")
        
        return '\n'.join(report)


def main():
    """Main function for collecting feedback"""
    import sys
    
    collector = FeedbackCollector()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--analyze':
            print(collector.generate_feedback_report())
        else:
            # Assume it's a report file
            collector.collect_feedback(sys.argv[1])
    else:
        # Find most recent report
        reports_dir = Path(__file__).parent / "reports"
        if reports_dir.exists():
            reports = sorted(reports_dir.glob("*.md"))
            if reports:
                latest_report = reports[-1]
                print(f"Collecting feedback for: {latest_report}")
                collector.collect_feedback(str(latest_report))
            else:
                print("No reports found to provide feedback on")
        else:
            print("No reports directory found")


if __name__ == "__main__":
    main()