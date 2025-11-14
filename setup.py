"""Setup script for BatteryPack simulation library."""

from pathlib import Path

from setuptools import find_packages, setup

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
	requirements = [
		line.strip()
		for line in requirements_file.read_text().splitlines()
		if line.strip() and not line.startswith("#")
	]

setup(
	name="battery-pack-sim",
	version="2.0.0",
	description="Enterprise-grade battery pack simulation and analysis toolkit",
	long_description=long_description,
	long_description_content_type="text/markdown",
	author="BatteryPack Contributors",
	packages=find_packages(),
	python_requires=">=3.10",
	install_requires=requirements,
	extras_require={
		"dev": [
			"pytest>=7.4",
			"pytest-cov>=4.1",
			"black>=23.0",
			"mypy>=1.0",
			"flake8>=6.0",
			"pylint>=2.17",
		],
		"optional": [
			"pybamm>=23.0",  # For PyBaMM integration
		],
	},
	classifiers=[
		"Development Status :: 4 - Beta",
		"Intended Audience :: Science/Research",
		"Intended Audience :: Developers",
		"Topic :: Scientific/Engineering",
		"Programming Language :: Python :: 3",
		"Programming Language :: Python :: 3.10",
		"Programming Language :: Python :: 3.11",
		"Programming Language :: Python :: 3.12",
		"License :: OSI Approved :: MIT License",
	],
)

