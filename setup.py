from os import path as os_path

from setuptools import setup, find_packages

import gitee_deleter

this_directory = os_path.abspath(os_path.dirname(__file__))

# python setup.py sdist bdist_wheel && python -m twine upload dist/*
setup(
    name="gitee-deleter",
    version=gitee_deleter.__version__,
    keywords=["gitee", "gitee-deleter"],
    packages=find_packages(include=["gitee_deleter", "LICENSE", "gitee_deleter.*"]),
    url="https://github.com/QIN2DIM/gitee-deleter",
    license="Apache License 2.0",
    author="QIN2DIM",
    author_email="rmalkaid@outlook.com",
    description="一键删光 Gitee 个人项目，非常垂直的账号注销脚本",
    long_description=open(
        os_path.join(this_directory, "README.md"), encoding="utf8"
    ).read(),
    long_description_content_type="text/markdown",
    install_requires=[
        "pyyaml~=6.0",
        "selenium~=4.1.0",
        "loguru~=0.6.0",
        "cloudscraper~=1.2.58",
        "lxml~=4.7.1",
        "webdriver_manager>=3.5.2",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
    ],
)
