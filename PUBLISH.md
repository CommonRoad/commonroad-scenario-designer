Checklist of TODOs for publishing code/documentation to public repository and PyPI
===================================================================

+ Publishing package on PyPI:
    + Update version numbers in code, setup.py and conf.py
    + Update README
    + Build package: `python3 setup.py sdist bdist_wheel`
    + Test the package at the PyPI test server: 
    `twine upload --repository-url https://test.pypi.org/legacy/ dist/*`
    + Push package to actual PyPI server: `twine upload dist/*`

+ Publishing package on public tum-cps server:
    + Build documentation according to readme
    + Remove test cases -> whole test folder
    + Remove PUBLISH.md from public repo
    + Update CHANGELOG
    + Push package to tum-cps repostory
    + Inform website team to update documentation on CommonRoad website