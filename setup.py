from setuptools import find_packages, setup

with open(r"README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

with open("requirements.txt", "r") as f:
    reqs = [line.strip() for line in f if ('selenium' not in line and 'webdriver' not in line)]

setup(
    name="gpt-researcher",
    version="0.6.1",
    description="GPT Researcher is an autonomous agent designed for comprehensive online research on a variety of tasks.",
    package_dir={'gpt_researcher': 'gpt_researcher'},
    packages=find_packages(),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/assafelovic/gpt-researcher",
    author="Assaf Elovic",
    author_email="assaf.elovic@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    install_requires=reqs,


)