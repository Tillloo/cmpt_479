# Filter AIDev data to human review comments on only TypeScript pull requests

# To run: .venv/bin/python scripts/01_filter.py

import pandas as pd


repo_df = pd.read_parquet(f"hf://datasets/hao-li/AIDev/repository.parquet")
pr_df = pd.read_parquet(f"hf://datasets/hao-li/AIDev/pull_request.parquet")
reviews_df = pd.read_parquet(f"hf://datasets/hao-li/AIDev/pr_reviews.parquet")
comments_df = pd.read_parquet(f"hf://datasets/hao-li/AIDev/pr_review_comments.parquet")

curr_num_rows = []

print(f"loading repository: {len(repo_df):,} rows")
print(f"loading pull_request: {len(pr_df):,} rows")
print(f"loading pr_reviews: {len(reviews_df):,} rows")
print(f"loading pr_review_comments: {len(comments_df):,} rows")

curr_num_rows.append({"step": "all_repositories", "rows": len(repo_df)})
curr_num_rows.append({"step": "all_pull_requests", "rows": len(pr_df)})
curr_num_rows.append({"step": "all_reviews", "rows": len(reviews_df)})
curr_num_rows.append({"step": "all_review_comments", "rows": len(comments_df)})

# Only keep TypeScript repositories with at least 100 stars and 
# only keep pull requests and review comments for those repositories. 
ts_repos = repo_df[(repo_df["language"] == "TypeScript") & (repo_df["stars"] >= 100)]
ts_repos = ts_repos[["id", "full_name"]]
ts_repos = ts_repos.rename(
    columns={
        "id": "repo_id",
        "full_name": "repo"
    }
)
curr_num_rows.append({"step": "typescript_repositories_100plus_stars", "rows": len(ts_repos)})

prs = pr_df.merge(ts_repos, on="repo_id", how="inner")
curr_num_rows.append({"step": "pull_requests_in_kept_repositories", "rows": len(prs)})

# Only keep reviews that match an existing pull request comment
reviews = reviews_df[["id", "pr_id"]]
reviews = reviews.rename(columns={"id": "review_id"})
comments = comments_df.merge(
    reviews,
    left_on="pull_request_review_id",
    right_on="review_id",
    how="inner"
)

curr_num_rows.append({"step": "review_comments_joined_to_reviews", "rows": len(comments)})

comments = comments[comments["pr_id"].isin(prs["id"])].copy()
curr_num_rows.append({"step": "review_comments_in_kept_pull_requests", "rows": len(comments)})

# Only keep PRs that match an existing pull request comment
prs_columns = prs[["id", "html_url", "agent", "repo", "state", "merged_at"]]
prs_columns = prs_columns.rename(columns={
    "id": "pr_id",
    "html_url": "pr_url"
})
comments = comments.merge(
    prs_columns,
    on="pr_id",
    how="inner"
)

comments = comments[comments["user_type"].eq("User")].copy()
curr_num_rows.append({"step": "human_review_comments", "rows": len(comments)})


body = comments["body"].fillna("")
comments = comments[body.str.len() >= 35].copy()
curr_num_rows.append({"step": "review_comments_at_least_35_characters", "rows": len(comments)})

comments["outcome"] = "not merged"
# All comments that have a date for "merged_at" are marked as" "merged"
comments.loc[comments["merged_at"].notna(), "outcome"] = "merged"
#All comments that don't have a "merged_at" date and have a state of "open" are marked as "open"
comments.loc[comments["merged_at"].isna() & comments["state"].str.lower().eq("open"),"outcome",] = "open"
curr_num_rows.append({"step": "review_comments_with_outcome", "rows": len(comments)})

output_columns = [
    "id",
    "pr_id",
    "pr_url",
    "agent",
    "repo",
    "outcome",
    "body",
    "diff_hunk",
    "path",
]

output = comments[output_columns].rename(columns={"id": "comment_id"})
output.to_csv("data/filtered_comments.csv", index=False)
print(f"\nsaved {len(output):,} rows to filtered_comments.csv")

usable_prs = output.groupby("agent", dropna=False)
# Only count PRs max once per agent even if there are multiple comments on the same PR
usable_prs = usable_prs["pr_id"].nunique()
usable_prs = usable_prs.reset_index(name="usable_prs")

funnel_df = pd.DataFrame(curr_num_rows)
funnel_df.to_csv("results/funnel.csv", index=False)
usable_prs.to_csv("results/usable_prs.csv", index=False)

print(f"\nsaved funnel to results/funnel.csv")
print("saved usable PR counts to results/usable_prs.csv")
print(pd.DataFrame(curr_num_rows).to_string(index=False))
print("\nusable PRs per agent:")
print(usable_prs.to_string(index=False))
