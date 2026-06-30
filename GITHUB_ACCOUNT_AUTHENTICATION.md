# GitHub account authentication for this repository

This repository is configured to use the `github-prithvic` SSH host alias, which points to the `PrithviC-rwth` GitHub account.

## What to do for a new repository

1. Create or clone the new repository as usual.
2. Set the remote to use the `github-prithvic` alias.

```bash
git remote set-url origin git@github-prithvic:PrithviC-rwth/REPO_NAME.git
```

3. Confirm the remote:

```bash
git remote -v
```

4. Push normally:

```bash
git push
```

## Notes

- The SSH key is tied to the GitHub account, not to a single repository.
- Any repository that the `PrithviC-rwth` account can access will work as long as its remote uses `git@github-prithvic`.
- If you create a new repo in that account, just use the alias from the start.
- Commit author name and email are separate from SSH authentication and can be configured per repository with `git config user.name` and `git config user.email`.
