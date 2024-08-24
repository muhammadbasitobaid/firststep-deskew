
#!/bin/bash

# Check if git-filter-repo is installed
if ! command -v git-filter-repo &> /dev/null
then
    echo "git-filter-repo could not be found. Please install it first."
    exit
fi

# Change author and committer details using git filter-repo
git filter-repo --commit-callback '
if commit.author_name == "sohaib.anwaar" and commit.author_email == "sohaib.anwaar@firststep.ai":
    commit.author_name = "muhammadbasitobaid"
    commit.author_email = "muhammadbasitobaid@gmail.com"
if commit.committer_name == "sohaib.anwaar" and commit.committer_email == "sohaib.anwaar@firststep.ai":
    commit.committer_name = "muhammadbasitobaid"
    commit.committer_email = "muhammadbasitobaid@gmail.com"
' --force
