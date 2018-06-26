# Unfortunately not as nice as godoc.org/rubydoc.info for now: https://www.pydoc.io/about/
set -e

# set up git
git config --global user.email "travis@travis-ci.org"
git config --global user.name "Travis CI"

# build and commit website files
python setup.py install
pip install pdoc
PYTHONPATH=. pdoc beeline --html --html-dir=./docs

# Check out orphan gh-pages branch, get it set up correctly
git checkout --orphan gh-pages
git reset
git add docs/
git mv docs/beeline/*.html ./
git add .gitignore
git clean -fd
git commit -m "Travis build: $TRAVIS_BUILD_NUMBER"

# Pushing via secure GH_TOKEN
git remote add origin-pages https://${GH_TOKEN}@github.com/honeycombio/libhoney-py.git > /dev/null 2>&1
git push --force --quiet --set-upstream origin-pages gh-pages
