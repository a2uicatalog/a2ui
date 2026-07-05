---
id: gh-cli-quickstart
domain: training
subtype: tool-kt
name: "GitHub CLI Quickstart"
audience: "Developers starting to work with GitHub from the command line"
source: "GitHub Docs — GitHub CLI quickstart"
source_url: "https://docs.github.com/en/github-cli/github-cli/quickstart"
license: "CC-BY-4.0"
est_minutes: 15
---

A tour of the GitHub CLI: check your work status, manage repositories, issues, pull requests and codespaces, and customize gh to fit how you work.

# Prerequisites {#prerequisite_checklist}
- GitHub CLI (gh) installed and authenticated — see GitHub's install-and-auth guide

# Concepts {#key_value}
- **alias** — A shortcut you define for a command you commonly run
- **extension** — A custom command created or added to extend the GitHub CLI
- **cs** — Shorthand you can substitute for codespace in any codespace command

# Steps

## 1 · Status & Repositories
> When you use some commands for the first time — for example gh codespace subcommands — you'll be prompted to add extra scopes to your authentication token. Follow the onscreen instructions.

### 1. View your status across subscribed repositories {#command_step}
cmd: gh status
expect: Details of your current work on GitHub across all the repositories you're subscribed to

### 2. View a repository's description and README {#command_step}
cmd: gh repo view OWNER/REPO
note: Add --web to open the repository in your default browser. Inside a local repo with a GitHub remote you can omit OWNER/REPO.

### 3. Clone a repository {#command_step}
cmd: gh repo clone OWNER/REPO
expect: The repository is cloned to the directory from which you ran the command

### 4. Create a repository {#command_step}
cmd: gh repo create
note: Follow the on-screen instructions. You can create a new empty repository and optionally clone it, or push an existing local repository and optionally set it as the remote.

## 2 · Issues & Pull Requests

### 1. List open issues for a repository {#command_step}
cmd: gh issue list --repo OWNER/REPO
note: Inside a local repo with a GitHub remote you can omit --repo. Try gh issue list --assignee "@me" for your issues, or --author monalisa for a specific user's.

### 2. List open pull requests {#command_step}
cmd: gh pr list --repo OWNER/REPO
note: gh pr list --author "@me" lists PRs you created; --label LABEL-NAME filters by label.

### 3. List pull requests awaiting your review {#command_step}
cmd: gh search prs --review-requested=@me --state=open

### 4. Create a pull request {#command_step}
cmd: gh pr create
note: Follow the on-screen instructions.

## 3 · Codespaces

### 1. Create a new codespace {#command_step}
cmd: gh codespace create
note: Follow the on-screen instructions.

### 2. List and open your codespaces {#command_step}
cmd: gh codespace list
note: gh codespace code -w opens a chosen codespace in the web version of VS Code. cs works as shorthand for codespace.

## 4 · Help & Customization
**Customization options**
- gh config set :: Adjust settings — e.g. gh config set editor "code -w" sets VS Code as your editor (the -w flag waits for the file to close)
- gh alias set :: Define shortcuts — e.g. gh alias set prd "pr create --draft" lets you run gh prd for a draft PR
- extensions :: Create or add custom commands via GitHub CLI extensions

### 1. See the top-level commands {#command_step}
cmd: gh
expect: A reminder of the top-level commands you can use — issue, pr, repo, and so on

### 2. Get help on any command {#command_step}
cmd: gh issue --help
note: Append --help to any command or subcommand, e.g. gh issue create --help.

## 5 · Multiple Accounts

### 1. Switch between accounts on the same platform {#command_step}
cmd: gh auth switch
note: Authenticate to each account first; use this to switch between them. For use across multiple GitHub platforms, see GitHub's multiple-accounts guide.

# References {#resources_list}
- GitHub CLI online manual — https://cli.github.com/manual/gh
- gh config set — https://cli.github.com/manual/gh_config_set
- gh alias — https://cli.github.com/manual/gh_alias
- gh auth switch — https://cli.github.com/manual/gh_auth_switch
