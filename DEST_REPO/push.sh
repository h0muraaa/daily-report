#!/bin/bash
git remote set-url origin "https://${GITHUB_TOKEN}@github.com/${GITHUB_USER}/${GITHUB_REPO}.git"
git p\ush origin HEAD:main
