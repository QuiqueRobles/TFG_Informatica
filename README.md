# GREMA Events

Effortlessly manage and organize your events with GREMA Events.

## Table of Contents

- [Introduction](#introduction)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)

## Introduction

GREMA Events is a web application developed using Flask to help users manage and organize events seamlessly. The application offers a range of features to facilitate event creation, management, and tracking.


## Getting Started

Follow these instructions to get a copy of the project up and running on your local machine.

### Prerequisites

Ensure you have the following software and tools installed:

- Python 3.x
- Git
- Docker (optional, for running the application in a container)

### Installation

You can set up and run the GREMA Events application either directly on your machine or using Docker. Below are the steps for both methods.

#### Local Execution with Git Clone

1. Open a terminal or command prompt in the directory where you want to clone the repository.
2. Execute the following command to clone the repository:
    ```sh
    git clone https://github.com/QuiqueRobles/TFG_Informatica.git
    ```
3. Once the repository is cloned, navigate to the project directory:
    ```sh
    cd TFG_Informatica
    ```
4. Run the main application file using Python. Depending on the project's structure, the main file might have a different name. In this case, execute the following command:
    ```sh
    python main.py
    ```

#### Local Execution with Docker

The developed software is available in the following GitHub repository:

- [TFG_Informatica Repository](https://github.com/QuiqueRobles/TFG_Informatica)

To run the application using Docker, follow these steps:

1. Clone the repository using the following command in a terminal or command prompt:
    ```sh
    git clone https://github.com/QuiqueRobles/TFG_Informatica.git
    ```
2. Navigate to the project directory:
    ```sh
    cd TFG_Informatica
    ```
3. Run the application using Docker:
    ```sh
    docker run -p 5000:5000 quiqueru/tfg-informatica
    ```
   This will start the container, and the application will be available at [http://localhost:5000](http://localhost:5000).

## Usage

Instructions on how to use the application, including any command-line tools, web interfaces, or additional configuration settings.

## Contributing

Information on how to contribute to the project, including guidelines for submitting issues and pull requests.

## License

Details about the project's license.

## Acknowledgements

Credits and acknowledgements for those who have contributed to the project, as well as any resources or libraries used.
