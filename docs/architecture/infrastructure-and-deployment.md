# Infrastructure and Deployment

## Infrastructure as Code
- **Tool:** N/A for library itself
- **Location:** N/A
- **Approach:** SDK is distributed via PyPI; users handle their own deployment

## Deployment Strategy
- **Strategy:** Package distribution via PyPI (Python Package Index)
- **CI/CD Platform:** GitHub Actions
- **Pipeline Configuration:** `.github/workflows/`

## Environments
- **Development:** Local development environment with `uv` for dependency management
- **Testing:** GitHub Actions runners for CI testing across Python versions (3.10, 3.11, 3.12)
- **Staging:** TestPyPI for pre-release validation - `https://test.pypi.org/project/ukcompanies/`
- **Production:** PyPI official repository - `https://pypi.org/project/ukcompanies/`

## Environment Promotion Flow
```text
Local Development
    ↓ (git push)
GitHub Branch
    ↓ (PR + tests)
Main Branch
    ↓ (tag release)
GitHub Release
    ↓ (automated)
TestPyPI (optional)
    ↓ (validation)
PyPI Production
    ↓ (pip/uv install)
End User Environment
```

## Rollback Strategy
- **Primary Method:** Version pinning - users can install previous versions via `pip install ukcompanies==1.0.0`
- **Trigger Conditions:** Critical bugs, security vulnerabilities, breaking API changes
- **Recovery Time Objective:** < 1 hour (yank broken version from PyPI, users automatically get previous version)