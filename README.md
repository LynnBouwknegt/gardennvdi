# Project Name

A brief description of what your project does and why it is useful.

## Overview

This project uses **Pixi** to manage Python virtual environments. **Pixi** makes it easy to isolate project dependencies, ensuring reproducible installations and clean development environments.

## Prerequisites

1. **Python 3.7+** (Make sure Python is on your `PATH`).
2. **Git** (optional, but generally recommended if you are cloning this repository).
3. **Pixi** installed (see [Installation(Windows)] below).

## Installation (Windows)

Follow these steps to install **Pixi** on Windows:

1. **Check your Python version**  
   Open PowerShell or Command Prompt and run:
   ```sh
   python --version
   ```
2. **Install Pixi**

    If Pixi is published on PyPI, you can install it with `pip`:
    ```sh
    pip install pixi
    ```
3. **Verify Pixi Installation**
Once installed, verify Pixi is working by running:
    ```sh
    pixi --help
    ```
4. **Initiate project with Pixi**
    Go to your project directory:
    ```sh
    cd path/to/your/project
    ```
    And run:
    ```sh
    pixi install
    ```