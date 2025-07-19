#!/usr/bin/env python3
"""
Project Progress Evaluator
Analyzes and evaluates progress on projects within the WebScrapper repository
"""

import os
import sys
import json
import subprocess
import datetime
from pathlib import Path
from typing import Dict, List, Optional, NamedTuple
from dataclasses import dataclass, asdict
import argparse


@dataclass
class ProjectMetrics:
    """Metrics for a single project"""
    name: str
    path: str
    total_files: int
    python_files: int
    js_files: int
    html_files: int
    total_lines: int
    python_lines: int
    js_lines: int
    last_modified: str
    has_tests: bool
    has_docs: bool
    has_package_file: bool
    git_commits: int
    recent_commits_30d: int
    recent_commits_7d: int
    main_technologies: List[str]
    estimated_completion: str
    health_score: float


@dataclass
class ProgressReport:
    """Complete progress report for the repository"""
    generated_at: str
    repository_name: str
    total_projects: int
    projects: List[ProjectMetrics]
    overall_activity_score: float
    most_active_project: str
    least_active_project: str
    summary: Dict[str, str]


class ProgressEvaluator:
    """Main class for evaluating project progress"""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()
        self.known_projects = {
            "WebScraper": "Web scraping tools and services",
            "NC Parser": "CNC G-code parser and visualizer",
            "GimmeDaTools": "Machine Learning Production System tools",
            "NotebookAI": "AI notebook interface",
            "EVEMap": "EVE game mapping tools",
            "STEPViewer": "STEP file viewer application",
            "machinist-runner-game": "Machinist-themed runner game",
            "BOB": "Book of Becoming website",
            "MachineBooking": "Machine booking system",
            "Machinist Game": "Machinist game interface"
        }
    
    def evaluate_progress(self, since_date: Optional[str] = None) -> ProgressReport:
        """Evaluate progress on all projects"""
        print(f"🔍 Evaluating progress in repository: {self.repo_path}")
        
        if since_date:
            print(f"📅 Analyzing changes since: {since_date}")
        else:
            print("📅 Analyzing all-time progress")
        
        projects = []
        
        for project_name in self.known_projects:
            project_path = self.repo_path / project_name
            if project_path.exists():
                print(f"📊 Analyzing project: {project_name}")
                metrics = self._analyze_project(project_name, project_path, since_date)
                projects.append(metrics)
        
        # Calculate overall metrics
        overall_activity = self._calculate_overall_activity(projects)
        most_active = max(projects, key=lambda p: p.health_score) if projects else None
        least_active = min(projects, key=lambda p: p.health_score) if projects else None
        
        return ProgressReport(
            generated_at=datetime.datetime.now().isoformat(),
            repository_name="WebScrapper",
            total_projects=len(projects),
            projects=projects,
            overall_activity_score=overall_activity,
            most_active_project=most_active.name if most_active else "None",
            least_active_project=least_active.name if least_active else "None",
            summary=self._generate_summary(projects)
        )
    
    def _analyze_project(self, name: str, path: Path, since_date: Optional[str]) -> ProjectMetrics:
        """Analyze a single project"""
        
        # File analysis
        files_info = self._analyze_files(path)
        
        # Git analysis
        git_info = self._analyze_git_history(path, since_date)
        
        # Technology detection
        technologies = self._detect_technologies(path)
        
        # Health score calculation
        health_score = self._calculate_health_score(files_info, git_info, path)
        
        # Estimated completion
        completion = self._estimate_completion(files_info, git_info, path)
        
        return ProjectMetrics(
            name=name,
            path=str(path.relative_to(self.repo_path)),
            total_files=files_info['total_files'],
            python_files=files_info['python_files'],
            js_files=files_info['js_files'],
            html_files=files_info['html_files'],
            total_lines=files_info['total_lines'],
            python_lines=files_info['python_lines'],
            js_lines=files_info['js_lines'],
            last_modified=files_info['last_modified'],
            has_tests=files_info['has_tests'],
            has_docs=files_info['has_docs'],
            has_package_file=files_info['has_package_file'],
            git_commits=git_info['total_commits'],
            recent_commits_30d=git_info['commits_30d'],
            recent_commits_7d=git_info['commits_7d'],
            main_technologies=technologies,
            estimated_completion=completion,
            health_score=health_score
        )
    
    def _analyze_files(self, path: Path) -> Dict:
        """Analyze files in a project directory"""
        info = {
            'total_files': 0,
            'python_files': 0,
            'js_files': 0,
            'html_files': 0,
            'total_lines': 0,
            'python_lines': 0,
            'js_lines': 0,
            'last_modified': '1970-01-01T00:00:00',
            'has_tests': False,
            'has_docs': False,
            'has_package_file': False
        }
        
        try:
            for file_path in path.rglob('*'):
                if file_path.is_file() and not self._should_ignore_file(file_path):
                    info['total_files'] += 1
                    
                    # Count lines
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = len(f.readlines())
                            info['total_lines'] += lines
                            
                            if file_path.suffix == '.py':
                                info['python_files'] += 1
                                info['python_lines'] += lines
                            elif file_path.suffix == '.js':
                                info['js_files'] += 1
                                info['js_lines'] += lines
                            elif file_path.suffix in ['.html', '.htm']:
                                info['html_files'] += 1
                    except:
                        pass
                    
                    # Check modification time
                    try:
                        mtime = file_path.stat().st_mtime
                        file_time = datetime.datetime.fromtimestamp(mtime).isoformat()
                        if file_time > info['last_modified']:
                            info['last_modified'] = file_time
                    except:
                        pass
                    
                    # Check for special files
                    filename = file_path.name.lower()
                    if 'test' in filename or filename.startswith('test_'):
                        info['has_tests'] = True
                    if filename in ['readme.md', 'readme.txt', 'docs']:
                        info['has_docs'] = True
                    if filename in ['package.json', 'requirements.txt', 'setup.py']:
                        info['has_package_file'] = True
        
        except Exception as e:
            print(f"  ⚠️  Error analyzing files in {path}: {e}")
        
        return info
    
    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if file should be ignored in analysis"""
        ignore_patterns = [
            'node_modules', '__pycache__', '.git', '.DS_Store',
            'package-lock.json', '.pyc', '.log'
        ]
        
        path_str = str(file_path)
        return any(pattern in path_str for pattern in ignore_patterns)
    
    def _analyze_git_history(self, path: Path, since_date: Optional[str]) -> Dict:
        """Analyze git history for a project"""
        info = {
            'total_commits': 0,
            'commits_30d': 0,
            'commits_7d': 0,
            'last_commit_date': None
        }
        
        try:
            # Change to project directory for git commands
            original_cwd = os.getcwd()
            os.chdir(self.repo_path)
            
            # Get total commits for this path
            result = subprocess.run(
                ['git', 'log', '--oneline', '--', str(path.relative_to(self.repo_path))],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                info['total_commits'] = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            
            # Get commits in last 30 days
            since_30d = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
            result = subprocess.run(
                ['git', 'log', '--oneline', f'--since={since_30d}', '--', str(path.relative_to(self.repo_path))],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                info['commits_30d'] = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            
            # Get commits in last 7 days
            since_7d = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
            result = subprocess.run(
                ['git', 'log', '--oneline', f'--since={since_7d}', '--', str(path.relative_to(self.repo_path))],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                info['commits_7d'] = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            
            os.chdir(original_cwd)
            
        except Exception as e:
            print(f"  ⚠️  Error analyzing git history for {path}: {e}")
            try:
                os.chdir(original_cwd)
            except:
                pass
        
        return info
    
    def _detect_technologies(self, path: Path) -> List[str]:
        """Detect main technologies used in project"""
        technologies = []
        
        # Check for package files
        if (path / 'package.json').exists():
            technologies.append('Node.js')
        if (path / 'requirements.txt').exists() or (path / 'setup.py').exists():
            technologies.append('Python')
        if (path / 'CMakeLists.txt').exists():
            technologies.append('C++')
        
        # Check file extensions
        has_python = any(path.rglob('*.py'))
        has_js = any(path.rglob('*.js'))
        has_html = any(path.rglob('*.html'))
        has_cpp = any(path.rglob('*.cpp')) or any(path.rglob('*.cc'))
        
        if has_python and 'Python' not in technologies:
            technologies.append('Python')
        if has_js and 'JavaScript' not in technologies:
            technologies.append('JavaScript')
        if has_html:
            technologies.append('HTML')
        if has_cpp:
            technologies.append('C++')
        
        return technologies
    
    def _calculate_health_score(self, files_info: Dict, git_info: Dict, path: Path) -> float:
        """Calculate project health score (0-100)"""
        score = 0.0
        
        # File activity (30 points)
        if files_info['total_files'] > 0:
            score += min(30, files_info['total_files'] * 2)
        
        # Code quality indicators (25 points)
        if files_info['has_tests']:
            score += 10
        if files_info['has_docs']:
            score += 10
        if files_info['has_package_file']:
            score += 5
        
        # Recent activity (25 points)
        score += min(15, git_info['commits_30d'] * 3)
        score += min(10, git_info['commits_7d'] * 5)
        
        # Code volume (20 points)
        if files_info['total_lines'] > 100:
            score += min(20, files_info['total_lines'] / 100)
        
        return min(100.0, score)
    
    def _estimate_completion(self, files_info: Dict, git_info: Dict, path: Path) -> str:
        """Estimate project completion status"""
        # Check for obvious indicators
        if (path / 'README.md').exists() and files_info['has_tests'] and files_info['total_lines'] > 1000:
            return "Production Ready"
        elif files_info['has_package_file'] and files_info['total_lines'] > 500:
            return "Beta/Testing"
        elif files_info['total_lines'] > 100:
            return "Alpha/Development"
        elif files_info['total_files'] > 0:
            return "Early Development"
        else:
            return "Not Started"
    
    def _calculate_overall_activity(self, projects: List[ProjectMetrics]) -> float:
        """Calculate overall repository activity score"""
        if not projects:
            return 0.0
        
        return sum(p.health_score for p in projects) / len(projects)
    
    def _generate_summary(self, projects: List[ProjectMetrics]) -> Dict[str, str]:
        """Generate summary insights"""
        if not projects:
            return {"status": "No projects found"}
        
        total_files = sum(p.total_files for p in projects)
        total_lines = sum(p.total_lines for p in projects)
        python_projects = len([p for p in projects if 'Python' in p.main_technologies])
        js_projects = len([p for p in projects if 'JavaScript' in p.main_technologies or 'Node.js' in p.main_technologies])
        
        active_projects = len([p for p in projects if p.recent_commits_30d > 0])
        
        return {
            "total_files": str(total_files),
            "total_lines_of_code": str(total_lines),
            "python_projects": str(python_projects),
            "javascript_projects": str(js_projects),
            "active_projects_30d": f"{active_projects}/{len(projects)}",
            "repository_health": "Good" if sum(p.health_score for p in projects) / len(projects) > 50 else "Needs Attention"
        }
    
    def generate_report(self, output_format: str = "json", output_file: Optional[str] = None, 
                       since_date: Optional[str] = None) -> str:
        """Generate and output progress report"""
        print("🚀 Starting progress evaluation...")
        report = self.evaluate_progress(since_date)
        
        if output_format.lower() == "json":
            output = json.dumps(asdict(report), indent=2, default=str)
        elif output_format.lower() == "text":
            output = self._format_text_report(report)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(output)
            print(f"📄 Report saved to: {output_file}")
        
        return output
    
    def _format_text_report(self, report: ProgressReport) -> str:
        """Format report as human-readable text"""
        lines = []
        lines.append("=" * 80)
        lines.append("PROJECT PROGRESS EVALUATION REPORT")
        lines.append("=" * 80)
        lines.append(f"Generated: {report.generated_at}")
        lines.append(f"Repository: {report.repository_name}")
        lines.append(f"Total Projects: {report.total_projects}")
        lines.append(f"Overall Activity Score: {report.overall_activity_score:.1f}/100")
        lines.append("")
        
        lines.append("SUMMARY:")
        lines.append("-" * 40)
        for key, value in report.summary.items():
            lines.append(f"  {key.replace('_', ' ').title()}: {value}")
        lines.append("")
        
        lines.append("PROJECT DETAILS:")
        lines.append("-" * 40)
        
        # Sort projects by health score (descending)
        sorted_projects = sorted(report.projects, key=lambda p: p.health_score, reverse=True)
        
        for project in sorted_projects:
            lines.append(f"\n📁 {project.name}")
            lines.append(f"   Path: {project.path}")
            lines.append(f"   Health Score: {project.health_score:.1f}/100")
            lines.append(f"   Status: {project.estimated_completion}")
            lines.append(f"   Technologies: {', '.join(project.main_technologies) if project.main_technologies else 'Unknown'}")
            lines.append(f"   Files: {project.total_files} ({project.python_files} Python, {project.js_files} JS)")
            lines.append(f"   Lines of Code: {project.total_lines:,}")
            lines.append(f"   Git Commits: {project.git_commits} total, {project.recent_commits_30d} in 30d, {project.recent_commits_7d} in 7d")
            lines.append(f"   Features: {'Tests' if project.has_tests else 'No Tests'}, {'Docs' if project.has_docs else 'No Docs'}, {'Package' if project.has_package_file else 'No Package'}")
            lines.append(f"   Last Modified: {project.last_modified}")
        
        lines.append("\n" + "=" * 80)
        lines.append(f"Most Active Project: {report.most_active_project}")
        lines.append(f"Least Active Project: {report.least_active_project}")
        lines.append("=" * 80)
        
        return "\n".join(lines)


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="Evaluate progress on projects in the WebScrapper repository")
    parser.add_argument("--since", help="Evaluate progress since date (YYYY-MM-DD)")
    parser.add_argument("--format", choices=["json", "text"], default="text", help="Output format")
    parser.add_argument("--output", help="Output file (default: print to stdout)")
    parser.add_argument("--path", default=".", help="Repository path")
    
    args = parser.parse_args()
    
    try:
        evaluator = ProgressEvaluator(args.path)
        report = evaluator.generate_report(
            output_format=args.format,
            output_file=args.output,
            since_date=args.since
        )
        
        if not args.output:
            print(report)
            
    except Exception as e:
        print(f"❌ Error generating progress report: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()