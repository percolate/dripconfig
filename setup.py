try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages


setup(
    name='dripconfig',
    version='0.1.dev1',
    description="configuration loading utilities for common process setup tasks",
    license="",
    author="Luke Tucker, James O'Beirne",
    author_email="luke@percolate.com, jamesob@percolate.com",
    url="",
    install_requires=[
        "configparser>=3.3.0",
        "voluptuous>=0.8.3",
        "pyyaml",
        "jsmin>=2.0.6"
    ],
    extras_require={
        'builtins': [
            "python-statsd>=1.6.0",
            "raven==1.9.1"
        ],
    },
    tests_require=[
        'mock',
    ],
    dependency_links=[],
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    test_suite='nose.collector',
)
