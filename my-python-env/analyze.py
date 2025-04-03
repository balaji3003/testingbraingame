import os
import shutil
import tempfile
import subprocess
import pandas as pd
import matplotlib.pyplot as plt
from radon.complexity import cc_visit
from radon.metrics import mi_visit
from pydriller import RepositoryMining
from collections import defaultdict, Counter
import math


def clone_repo(git_url, clone_path):
    print(f"Cloning repository from {git_url}...")
    subprocess.run(["git", "clone", git_url, clone_path], check=True)


def calculate_entropy(change_counts):
    total = sum(change_counts.values())
    if total == 0:
        return 0
    entropy = -sum((count / total) * math.log2(count / total) for count in change_counts.values())
    return entropy


def analyze_repository(repo_path):
    print("Starting longitudinal analysis...")
    data = []
    file_ownership = defaultdict(set)
    commit_counts_by_author = Counter()
    file_change_counter = defaultdict(int)

    for commit in RepositoryMining(repo_path).traverse_commits():
        churn_add = 0
        churn_del = 0
        file_count = 0
        complexity_total = 0
        mi_total = 0
        files_analyzed = 0
        author_email = commit.author.email
        commit_counts_by_author[author_email] += 1

        cohesion_metric = 0
        coupling_metric = 0

        for m in commit.modifications:
            filename = m.new_path or m.old_path
            if not filename:
                continue

            file_change_counter[filename] += 1
            file_ownership[filename].add(author_email)

            if filename.endswith(".py") and m.source_code is not None:
                file_count += 1
                churn_add += m.added
                churn_del += m.removed
                try:
                    complexity_list = cc_visit(m.source_code)
                    complexity_sum = sum([c.complexity for c in complexity_list])
                    complexity_total += complexity_sum
                    mi_total += mi_visit(m.source_code, False)
                    cohesion_metric += len(m.source_code.split()) / (len(complexity_list) + 1)
                    coupling_metric += len([c for c in complexity_list if c.name.startswith("_")])
                    files_analyzed += 1
                except Exception:
                    continue

        if files_analyzed > 0:
            avg_complexity = complexity_total / files_analyzed
            avg_mi = mi_total / files_analyzed
            avg_cohesion = cohesion_metric / files_analyzed
            avg_coupling = coupling_metric / files_analyzed
        else:
            avg_complexity = 0
            avg_mi = 0
            avg_cohesion = 0
            avg_coupling = 0

        entropy = calculate_entropy(file_change_counter)

        data.append({
            "commit_hash": commit.hash,
            "commit_date": commit.committer_date,
            "author": author_email,
            "files_changed": file_count,
            "lines_added": churn_add,
            "lines_deleted": churn_del,
            "avg_cyclomatic_complexity": avg_complexity,
            "avg_maintainability_index": avg_mi,
            "avg_cohesion_metric": avg_cohesion,
            "avg_coupling_metric": avg_coupling,
            "code_entropy": entropy,
            "commit_frequency_by_author": commit_counts_by_author[author_email],
            "unique_authors_per_file_avg": sum(len(owners) for owners in file_ownership.values()) / len(file_ownership)
        })

    df = pd.DataFrame(data)
    df['commit_date'] = pd.to_datetime(df['commit_date'])
    df.sort_values('commit_date', inplace=True)

    output_file = "longitudinal_metrics.csv"
    df.to_csv(output_file, index=False)
    print(f"✅ Analysis complete. Data saved to {output_file}")
    return df


def plot_metrics(df):
    print("Generating plot...")
    plt.figure(figsize=(14, 8))
    plt.plot(df['commit_date'], df['avg_cyclomatic_complexity'], label='Avg Cyclomatic Complexity')
    plt.plot(df['commit_date'], df['avg_maintainability_index'], label='Avg Maintainability Index')
    plt.plot(df['commit_date'], df['code_entropy'], label='Code Entropy')
    plt.xlabel("Date")
    plt.ylabel("Metric Value")
    plt.title("Software Quality Metrics Over Time")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("quality_metrics_plot.png")
    plt.show()
    print("📊 Plot saved as quality_metrics_plot.png")


def run_analysis_from_url(git_url):
    with tempfile.TemporaryDirectory() as tmpdir:
        clone_repo(git_url, tmpdir)
        df = analyze_repository(tmpdir)
        plot_metrics(df)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Longitudinal Software Quality Analyzer")
    parser.add_argument("--url", type=str, required=True, help="GitHub repository URL to analyze")
    args = parser.parse_args()

    run_analysis_from_url(args.url)
