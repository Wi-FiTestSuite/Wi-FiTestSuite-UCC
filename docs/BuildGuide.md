# Build Guide
These instructions will guide you through the process of setting up a Wi-Fi Test Suite UCC (Unified Communications Console) clone for the first time. We also have an automated install script for Windows 7.

## Prerequisites and get the code
Make sure you have [python version 2.7](https://www.python.org/download/releases/2.7/) installed

Before continuing with this guide, make sure you have all of UCC's dependencies installed.
Clone the [Wi-Fi Test Suite](https://github.com/Wi-FiTestSuite/Wi-FiTestSuite-UCC) git repository available on github

## Get the code and build
Once this is done, you'll need to compile the python UCC code with a script located in the root directory.

Execute command in root directory of Wi-FiTestSuite-UCC: buildUcc.bat

The executable wfa_ucc.exe will be generated and placed in “python/dist” folder. The required python binaries are also place in there as well.