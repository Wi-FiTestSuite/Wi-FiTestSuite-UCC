# **Wi-Fi Test Suite - UCC (Unified Command Console)**
**Latest Release: v9.0.0**

## Introduction
Wi-Fi Test Suite is a software platform originally developed by Wi-Fi Alliance  to support certification program development and device certification. Non-proprietary components are provided under the ISC License and can be accessed at the [Wi-Fi Test Suite] open source project on GitHub. Wi-Fi Alliance members can access the full software package, including proprietary components, on the Wi-Fi Alliance [member site].

## UCC and how to get it
Unified CAPI Console provides the overall control console for Wi-Fi Test Suite.

UCC runs tests defined by input text files containing CAPI commands. The individual CAPI commands within the input files are handled by UCC to perform functions such as DUT configuration, traffic stream definition, and test execution. UCC will direct specific CAPI commands to the appropriate device. This is accomplished via the Control Network.

UCC can be downloaded through the open source repository http://github.com/wifialliance/Wi-FiTestSuite or by members in the most recent Wi-Fi Test Suite package

## Dependencies
Make sure you have python version 2.7 installed:
https://www.python.org/download/releases/2.7/

## Installation from sources
Refer to our Build Guide for instructions on compiling UCC from scratch

## License
Please refer to LICENSE.txt

## Documentation
docs/Build_Guide.pdf

## Issues and Contribution Guidelines
Please submit issues/ideas to support@wi-fi.org.
Both Wi-Fi Alliance members and non-members can contribute to the Wi-Fi Test Suite open source project. Please review the contribution agreement prior to submitting a pull request.
Please read more on contributions in CONTRIBUTING.md.