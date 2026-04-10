from setuptools import setup, find_packages

setup(
    name="moss",
    version="5.4.0",
    description="Multi-Objective Self-Driven System — 自主涌现驱动力 AGI Agent",
    long_description=open("README.md", encoding="utf-8").read() if True else "",
    long_description_content_type="text/markdown",
    author="Cash, Fuxi",
    url="https://github.com/luokaishi/moss",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "numpy>=1.20.0",
        "scipy>=1.6.0",
        "matplotlib>=3.3.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.2.0",
            "flake8>=3.9.0",
        ],
        "vis": [
            "seaborn>=0.11.0",
            "plotly>=5.0.0",
            "networkx>=2.6.0",
            "pandas>=1.2.0",
        ],
        "full": [
            "pytest>=6.2.0",
            "flake8>=3.9.0",
            "seaborn>=0.11.0",
            "plotly>=5.0.0",
            "networkx>=2.6.0",
            "pandas>=1.2.0",
            "scikit-learn>=0.24.0",
            "json5>=0.9.0",
            "tqdm>=4.60.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "moss-demo=moss.demo:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
