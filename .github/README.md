# GitHub Actions Workflows

This directory contains GitHub Actions workflows for continuous integration and deployment of the NASA API Pipeline project.

## Available Workflows

### 1. CI (`ci.yml`)
**Triggers:** Push and Pull Requests to main, master, and develop branches

**Jobs:**
- **lint-python**: Lints Python code using flake8 to ensure code quality
- **validate-docker**: Validates Docker and docker-compose configuration files

### 2. Docker Build (`docker-build.yml`)
**Triggers:** Push and Pull Requests to main and master branches

**Jobs:**
- **build-airflow**: Builds the Airflow Docker image from `dockerfile`
- **build-spark**: Builds the Spark cluster Docker image from `Dockerfile.spark`

Uses Docker BuildKit with GitHub Actions cache for faster builds.

### 3. Python Validation (`python-validation.yml`)
**Triggers:** Push and Pull Requests to main, master, and develop branches (only when Python files change)

**Jobs:**
- **validate-python-syntax**: Checks Python syntax across all `.py` files
- **check-requirements**: Validates requirements files can be installed

## Workflow Status

You can view the status of these workflows on the [Actions tab](../../actions) of the repository.

## Adding Badges

To add workflow status badges to your README, use:

```markdown
![CI](https://github.com/moumay2003/Nasa-Api-pipeline/workflows/CI/badge.svg)
![Docker Build](https://github.com/moumay2003/Nasa-Api-pipeline/workflows/Docker%20Build/badge.svg)
![Python Validation](https://github.com/moumay2003/Nasa-Api-pipeline/workflows/Python%20Validation/badge.svg)
```

## Local Testing

To test workflows locally, you can use [act](https://github.com/nektos/act):

```bash
# Install act
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run all workflows
act

# Run a specific workflow
act -W .github/workflows/ci.yml
```

## Contributing

When adding new workflows:
1. Ensure YAML syntax is valid
2. Test workflows don't duplicate existing functionality
3. Add appropriate triggers and branch filters
4. Document the workflow purpose in this README
