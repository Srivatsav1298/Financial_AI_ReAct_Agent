"""
Advanced Analysis with Statistical Testing and Visualizations
Generates publication-quality charts and comprehensive statistics
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from scipy import stats
import numpy as np
from datetime import datetime

# Set style for publication-quality plots
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

class AdvancedAnalyzer:
    """Advanced analysis with statistical tests and visualizations"""
    
    def __init__(self, results_dir: Path):
        self.results_dir = Path(results_dir)
        self.figures_dir = self.results_dir / "figures"
        self.figures_dir.mkdir(exist_ok=True)
        
    def load_latest_results(self):
        """Load the most recent baseline and react results"""
        baseline_files = sorted(self.results_dir.glob("baseline_results_*.json"))
        react_files = sorted(self.results_dir.glob("react_results_*.json"))
        
        if not baseline_files or not react_files:
            raise FileNotFoundError("No results files found. Run evaluation first.")
        
        with open(baseline_files[-1], 'r') as f:
            self.baseline_data = json.load(f)
        
        with open(react_files[-1], 'r') as f:
            self.react_data = json.load(f)
        
        print(f"✅ Loaded results:")
        print(f"   Baseline: {baseline_files[-1].name}")
        print(f"   ReAct: {react_files[-1].name}")
    
    def create_performance_comparison(self):
        """Create comprehensive performance comparison chart"""
        
        baseline_results = self.baseline_data['results']
        react_results = self.react_data['results']
        
        metrics = {
            'Avg Response\nTime (s)': [
                float(np.mean([r['elapsed_time'] for r in baseline_results])),
                float(np.mean([r['elapsed_time'] for r in react_results]))
            ],
            'Tool Usage\nRate (%)': [
                float(sum(1 for r in baseline_results if r.get('tool_used', False)) / len(baseline_results) * 100),
                100.0
            ],
            'Avg Iterations': [
                1.0,
                float(np.mean([r.get('iterations', 1) for r in react_results]))
            ],
            'Error Rate (%)': [
                float(sum(1 for r in baseline_results if 'ERROR' in r['answer']) / len(baseline_results) * 100),
                float(sum(1 for r in react_results if 'ERROR' in r['answer']) / len(react_results) * 100)
            ]
        }
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Performance Comparison: Baseline vs ReAct Agent', fontsize=16, fontweight='bold')
        
        agents = ['Baseline', 'ReAct']
        colors = ['#3498db', '#e74c3c']
        
        for idx, (metric, values) in enumerate(metrics.items()):
            ax = axes[idx // 2, idx % 2]
            bars = ax.bar(agents, values, color=colors, alpha=0.7, edgecolor='black')
            ax.set_ylabel('Value', fontsize=11)
            ax.set_title(metric, fontsize=12, fontweight='bold')
            ax.grid(axis='y', alpha=0.3)
            
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                        f'{value:.2f}', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        output_path = self.figures_dir / 'performance_comparison.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✅ Saved: {output_path}")
        plt.close()
    
    def create_response_time_distribution(self):
        """Visualize response time distributions"""
        
        baseline_times = [float(r['elapsed_time']) for r in self.baseline_data['results']]
        react_times = [float(r['elapsed_time']) for r in self.react_data['results']]
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        fig.suptitle('Response Time Distributions', fontsize=16, fontweight='bold')
        
        ax1 = axes[0]
        ax1.hist(baseline_times, bins=10, alpha=0.6, label='Baseline', color='#3498db', edgecolor='black')
        ax1.hist(react_times, bins=10, alpha=0.6, label='ReAct', color='#e74c3c', edgecolor='black')
        ax1.set_xlabel('Response Time (seconds)', fontsize=11)
        ax1.set_ylabel('Frequency', fontsize=11)
        ax1.set_title('Distribution Histogram', fontsize=12, fontweight='bold')
        ax1.legend()
        ax1.grid(alpha=0.3)
        
        ax2 = axes[1]
        box_data = [baseline_times, react_times]
        bp = ax2.boxplot(box_data, tick_labels=['Baseline', 'ReAct'], patch_artist=True, widths=0.6)
        
        colors = ['#3498db', '#e74c3c']
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.6)
        
        means = [np.mean(baseline_times), np.mean(react_times)]
        ax2.plot([1, 2], means, 'D', color='green', markersize=8, label='Mean', zorder=10)
        ax2.legend()
        ax2.set_ylabel('Response Time (seconds)', fontsize=11)
        ax2.set_title('Distribution Box Plot', fontsize=12, fontweight='bold')
        ax2.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        output_path = self.figures_dir / 'response_time_distribution.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✅ Saved: {output_path}")
        plt.close()
    
    def create_category_performance(self):
        """Analyze performance by question category"""
        
        react_results = self.react_data['results']
        
        categories = {}
        for r in react_results:
            cat = r['category']
            categories.setdefault(cat, {"times": [], "iterations": []})
            categories[cat]["times"].append(float(r['elapsed_time']))
            categories[cat]["iterations"].append(float(r.get('iterations', 1)))
        
        cat_names = list(categories.keys())
        avg_times = [float(np.mean(categories[c]["times"])) for c in cat_names]
        avg_iters = [float(np.mean(categories[c]["iterations"])) for c in cat_names]
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        fig.suptitle("ReAct Performance by Question Category", fontsize=16, fontweight='bold')
        
        ax1 = axes[0]
        bars1 = ax1.barh(cat_names, avg_times, color='#3498db', alpha=0.7, edgecolor='black')
        ax1.set_xlabel('Average Response Time (seconds)', fontsize=11)
        ax1.set_title('Response Time', fontsize=12, fontweight='bold')
        ax1.grid(axis='x', alpha=0.3)
        
        for bar, value in zip(bars1, avg_times):
            ax1.text(bar.get_width(), bar.get_y() + bar.get_height()/2., f'{value:.1f}s', ha='left', va='center')
        
        ax2 = axes[1]
        bars2 = ax2.barh(cat_names, avg_iters, color='#e74c3c', alpha=0.7, edgecolor='black')
        ax2.set_xlabel('Average Iterations', fontsize=11)
        ax2.set_title('Reasoning Iterations', fontsize=12, fontweight='bold')
        ax2.grid(axis='x', alpha=0.3)
        
        for bar, value in zip(bars2, avg_iters):
            ax2.text(bar.get_width(), bar.get_y() + bar.get_height()/2., f'{value:.1f}', ha='left', va='center')
        
        plt.tight_layout()
        output_path = self.figures_dir / 'category_performance.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✅ Saved: {output_path}")
        plt.close()
    
    def perform_statistical_tests(self):
        """Perform statistical significance tests"""
        
        baseline_times = [float(r['elapsed_time']) for r in self.baseline_data['results']]
        react_times = [float(r['elapsed_time']) for r in self.react_data['results']]
        
        t_stat, p_value = stats.ttest_rel(baseline_times, react_times)
        
        mean_diff = float(np.mean(react_times) - np.mean(baseline_times))
        pooled_std = float(np.sqrt((np.std(baseline_times)**2 + np.std(react_times)**2) / 2))
        cohens_d = float(mean_diff / pooled_std)
        
        wilcoxon_stat, wilcoxon_p = stats.wilcoxon(baseline_times, react_times)
        
        results = {
            "Paired t-test": {
                "t-statistic": float(t_stat),
                "p-value": float(p_value),
                "significant": bool(p_value < 0.05)
            },
            "Effect Size (Cohen's d)": {
                "value": float(cohens_d),
                "interpretation": self._interpret_cohens_d(cohens_d)
            },
            "Wilcoxon test": {
                "statistic": float(wilcoxon_stat),
                "p-value": float(wilcoxon_p),
                "significant": bool(wilcoxon_p < 0.05)
            },
            "Descriptive Statistics": {
                "Baseline": {
                    "mean": float(np.mean(baseline_times)),
                    "std": float(np.std(baseline_times)),
                    "median": float(np.median(baseline_times))
                },
                "ReAct": {
                    "mean": float(np.mean(react_times)),
                    "std": float(np.std(react_times)),
                    "median": float(np.median(react_times))
                }
            }
        }
        
        stats_file = self.results_dir / "statistical_tests.json"
        with open(stats_file, "w") as f:
            json.dump(results, f, indent=2)
        
        print("\n✅ Statistical Analysis:")
        print(f"   Paired t-test: t={t_stat:.3f}, p={p_value:.4f}")
        print(f"   Effect size (d): {cohens_d:.3f}")
        
        return results
    
    def _interpret_cohens_d(self, d):
        """Interpret Cohen's d effect size"""
        d = abs(float(d))
        if d < 0.2:
            return "negligible"
        elif d < 0.5:
            return "small"
        elif d < 0.8:
            return "medium"
        else:
            return "large"
    
    def generate_html_report(self):
        baseline_results = self.baseline_data['results']
        react_results = self.react_data['results']
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Norfain ReAct Agent - Analysis Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .highlight {{
            background-color: #ffffcc;
        }}
    </style>
</head>
<body>
    <h1>🚀 Norfain ReAct Agent - Comprehensive Analysis Report</h1>

    <div>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Total Questions:</strong> {len(baseline_results)}</p>
    </div>

    <h2>📈 Performance Visualizations</h2>
    <img src="figures/performance_comparison.png">
    <img src="figures/response_time_distribution.png">
    <img src="figures/category_performance.png">
</body>
</html>
"""
        
        report_path = self.results_dir / "analysis_report.html"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print(f"✅ Generated HTML report: {report_path}")
    
    def run_full_analysis(self):
        print("\n" + "="*80)
        print("🔬 ADVANCED ANALYSIS")
        print("="*80 + "\n")
        
        self.load_latest_results()
        
        print("\n📊 Generating visualizations...")
        self.create_performance_comparison()
        self.create_response_time_distribution()
        self.create_category_performance()
        
        print("\n📈 Performing statistical tests...")
        self.perform_statistical_tests()
        
        print("\n📄 Generating HTML report...")
        self.generate_html_report()
        
        print("\n" + "="*80)
        print("✅ ANALYSIS COMPLETE!")
        print("="*80)
        print(f"\nAll outputs saved to: {self.results_dir}")


def main():
    results_dir = Path(__file__).parent.parent / "results"
    analyzer = AdvancedAnalyzer(results_dir)
    analyzer.run_full_analysis()


if __name__ == "__main__":
    main()
