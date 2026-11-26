# Sample pull requests for human labeling.

# To run: .venv/bin/python scripts/sampling.py

import pandas as pd


SEED = 200
TARGET_PER_AGENT = 40


comments = pd.read_csv("data/filtered_comments.csv")

# Group all comments from the same pull request
grouped_comments = comments.groupby("pr_id", group_keys=False)
# Choose a random comment from each pull request
one_per_pr = grouped_comments.sample(n=1, random_state=SEED)

# Group each comment by the agent used
agent_groups = one_per_pr.groupby("agent")
# Checks how many unique pull requests there are for each agent
usable_pr_counts = agent_groups["pr_id"].nunique()
# Sort agents by name
usable_pr_counts = usable_pr_counts.sort_index()


sampled_groups = []

# Step 2: Group pull requests by agent
agent_groups = one_per_pr.groupby("agent")

# Loop through each agent
for agent, group in agent_groups:

    # Step 4: Select a sample of pull requests
    selected = group.sample(
        min(TARGET_PER_AGENT, len(group)),
        random_state=SEED
    )

    # Add the selected rows to the list
    sampled_groups.append(selected)

sample = pd.concat(sampled_groups)

# Add a row_id column starting from 1
sample.insert(0, "row_id", range(1, len(sample) + 1))

sample.to_csv("data/sample.csv", index=False)

print("usable PRs per agent after one-comment-per-PR sampling:")
print(usable_pr_counts.to_string())
print("\nsampled rows per agent:")
print(sample.groupby("agent").size().sort_index().to_string())
print("\noutcome counts:")
print(sample["outcome"].value_counts(dropna=False).sort_index().to_string())
print(f"\nsaved {len(sample)} rows to data/sample.csv")
