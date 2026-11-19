# Publishing a release

Register a GitHub pending publisher in [PyPI Publishing](https://pypi.org/manage/account/publishing/) for project `purifier-stats`, owner `thepushkarp`, repository `purifier-stats`, workflow `release.yml`, environment `pypi`. Merge the release PR with the version in `pyproject.toml` and the matching README, website, and skill instructions. Publish a GitHub Release tagged `v<version>` from that merge commit. CI tests the wheel before the release job uploads the wheel and source distribution through OIDC.
