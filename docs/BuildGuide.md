# Build Guide
These instructions will guide you through the process of setting up a Wi-Fi Test Suite UCC (Unified CAPI Console) clone for the first time. We also have an automated install script for Windows 7.

## Prerequisites
Make sure you have [python version 2.7](https://www.python.org/download/releases/2.7/) installed.

## Get the code and build
Before continuing with this guide, make sure you have all of the UCC dependencies installed.
Clone the [Wi-Fi Test Suite](https://github.com/Wi-FiTestSuite/Wi-FiTestSuite-UCC) git repository available on github.

Once this is done, you will need to compile the python UCC code with a script located in the root directory.

Execute the following command in root directory of Wi-FiTestSuite-UCC: buildUcc.bat

The executable wfa_ucc.exe and required python binaries will be generated and placed in the “python/dist” folder. 