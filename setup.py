from setuptools import setup


# Project metadata was moved to pyproject.toml (which is read by pip). However, custom
# build commands and setuptools extension modules are still defined here.
setup(
    # silence "Package would be ignored" warnings
    include_package_data=True,
)
