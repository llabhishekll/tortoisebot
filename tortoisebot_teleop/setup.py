import os
from glob import glob

from setuptools import find_packages, setup

package_name = "tortoisebot_teleop"

setup(
    name=package_name,
    version="1.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        (
            "share/ament_index/resource_index/packages",
            ["resource/" + package_name],
        ),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
        (os.path.join("share", package_name, "config"), glob("config/*")),
        (os.path.join("share", package_name, "www"), glob("www/*")),
    ],
    package_data={"": ["py.typed"]},
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Abhishek Verma",
    maintainer_email="llabhishekll@users.noreply.github.com",
    description="TortoiseBot teleoperation: keyboard, web, and waypoint routes",
    license="Apache-2.0",
    extras_require={
        "test": [
            "pytest",
        ],
    },
    entry_points={
        "console_scripts": [
            "teleop_twist_keyboard = tortoisebot_teleop.teleop_twist_keyboard:main",
            "waypoints = tortoisebot_teleop.waypoints:main",
        ],
    },
)
