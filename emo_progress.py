#!/usr/bin/env python3
"""
EMO Project Progress Evaluator
Specialized interface for evaluating progress on the "emo project" 
and other projects in the WebScrapper repository
"""

import sys
import argparse
import json
from datetime import datetime, timedelta
from progress_evaluator import ProgressEvaluator


def find_emo_related_projects(evaluator: ProgressEvaluator):
    """Find projects that might be related to 'emo' keyword"""
    report = evaluator.evaluate_progress()
    
    # Look for projects with 'emo' in name or containing emo-related files
    emo_related = []
    
    for project in report.projects:
        project_name_lower = project.name.lower()
        
        # Check for potential matches
        if any(keyword in project_name_lower for keyword in ['demo', 'remove', 'emo']):
            emo_related.append(project)
    
    return emo_related, report


def evaluate_emo_progress(since_date=None):
    """Evaluate progress specifically for emo-related projects"""
    print("🔍 EMO Project Progress Evaluator")
    print("=" * 50)
    
    evaluator = ProgressEvaluator()
    emo_projects, full_report = find_emo_related_projects(evaluator)
    
    if not emo_projects:
        print("❓ No projects with 'emo' keyword found in repository.")
        print("📋 However, here are projects that might contain relevant functionality:")
        print()
        
        # Show projects with demo files or remove functionality
        demo_projects = []
        for project in full_report.projects:
            if 'demo' in project.name.lower() or 'remove' in project.name.lower():
                demo_projects.append(project)
        
        if demo_projects:
            for project in demo_projects:
                print(f"  📁 {project.name} - {project.estimated_completion}")
                print(f"     Technologies: {', '.join(project.main_technologies)}")
                print(f"     Health Score: {project.health_score:.1f}/100")
                print()
        
        print("🔎 Checking for files containing 'emo' patterns...")
        _check_for_emo_files()
        
    else:
        print("✅ Found EMO-related projects:")
        print()
        
        for project in emo_projects:
            print(f"📁 {project.name}")
            print(f"   Status: {project.estimated_completion}")
            print(f"   Health Score: {project.health_score:.1f}/100")
            print(f"   Recent Activity: {project.recent_commits_30d} commits in 30d")
            print(f"   Technologies: {', '.join(project.main_technologies)}")
            print()
    
    # Show overall repository status
    print("📊 Overall Repository Status:")
    print(f"   Total Projects: {full_report.total_projects}")
    print(f"   Overall Health: {full_report.overall_activity_score:.1f}/100")
    print(f"   Most Active: {full_report.most_active_project}")
    print(f"   Active Projects (30d): {full_report.summary['active_projects_30d']}")
    
    if since_date:
        print(f"   Analysis Period: Since {since_date}")
    
    return full_report


def _check_for_emo_files():
    """Check for files that might contain 'emo' patterns"""
    import os
    import subprocess
    
    try:
        # Search for files containing 'emo' patterns
        result = subprocess.run(
            ['find', '.', '-type', 'f', '-name', '*.py', '-o', '-name', '*.js', '-not', '-path', '*/node_modules/*'],
            capture_output=True, text=True, timeout=30
        )
        
        if result.returncode == 0:
            files = result.stdout.strip().split('\n')
            emo_files = []
            
            for file_path in files:
                if file_path:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read().lower()
                            if 'emo' in content:
                                emo_files.append(file_path)
                    except:
                        pass
            
            if emo_files:
                print(f"📄 Found {len(emo_files)} files containing 'emo' patterns:")
                for file_path in emo_files[:10]:  # Show first 10
                    print(f"     {file_path}")
                if len(emo_files) > 10:
                    print(f"     ... and {len(emo_files) - 10} more")
            else:
                print("   No files containing 'emo' patterns found")
    except Exception as e:
        print(f"   Error searching files: {e}")


def generate_progress_since(since_date_str: str):
    """Generate progress report since a specific date"""
    try:
        # Validate date format
        since_date = datetime.strptime(since_date_str, '%Y-%m-%d')
        print(f"📅 Generating progress report since {since_date_str}")
        
        evaluator = ProgressEvaluator()
        return evaluator.generate_report(since_date=since_date_str, output_format="text")
        
    except ValueError:
        print(f"❌ Invalid date format: {since_date_str}. Use YYYY-MM-DD format.")
        return None


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="Evaluate progress on the EMO project and related projects",
        epilog="""
Examples:
  python emo_progress.py                    # General EMO project evaluation
  python emo_progress.py --since 2025-01-01  # Progress since January 1st
  python emo_progress.py --all-projects      # Full repository analysis
  python emo_progress.py --search-term demo  # Search for specific term
        """
    )
    
    parser.add_argument("--since", help="Evaluate progress since date (YYYY-MM-DD)")
    parser.add_argument("--all-projects", action="store_true", 
                       help="Show analysis for all projects")
    parser.add_argument("--search-term", help="Search for projects containing specific term")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--output", help="Save report to file")
    
    args = parser.parse_args()
    
    try:
        if args.all_projects:
            evaluator = ProgressEvaluator()
            report = evaluator.generate_report(
                output_format="json" if args.json else "text",
                output_file=args.output,
                since_date=args.since
            )
            if not args.output:
                print(report)
        
        elif args.search_term:
            print(f"🔍 Searching for projects containing: '{args.search_term}'")
            evaluator = ProgressEvaluator()
            report = evaluator.evaluate_progress(args.since)
            
            matching_projects = [
                p for p in report.projects 
                if args.search_term.lower() in p.name.lower()
            ]
            
            if matching_projects:
                print(f"✅ Found {len(matching_projects)} matching projects:")
                for project in matching_projects:
                    print(f"\n📁 {project.name}")
                    print(f"   Status: {project.estimated_completion}")
                    print(f"   Health: {project.health_score:.1f}/100")
                    print(f"   Activity: {project.recent_commits_30d} commits (30d)")
            else:
                print(f"❌ No projects found containing '{args.search_term}'")
        
        elif args.since:
            report_text = generate_progress_since(args.since)
            if report_text:
                if args.output:
                    with open(args.output, 'w') as f:
                        f.write(report_text)
                    print(f"📄 Report saved to: {args.output}")
                else:
                    print(report_text)
        
        else:
            # Default EMO project evaluation
            evaluate_emo_progress(args.since)
            
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()