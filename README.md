# Quick Writeup CLI

Quick Writeup is a command-line tool designed to simplify the management of writeup entries. The application allows users to create, edit, and maintain their writeups efficiently.

## Features
- **Create Writeups:** Quickly create new writeups and organize them by topics.
- **Edit Writeups:** Modify existing writeups with ease.
- **Sorted by date and topics:** Automatically sort writeups by date and topics.

## Usage
This application is designed for Linux users. Follow the steps below to start the application:

### Using Source Code
1. Clone the repository:
   ```bash
   git clone <repository_url>
   ```
2. Set up a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration
Before launching the application, you need to manually configure the path for topics by setting it in the configuration file.
```bash
~/.quick_writeup_config.json
```

Within the .json
```bash
{
  "topics_path": "/path/to/your/topics"
}
```

Manually edit this file when needed to update the topics path.

## License
This project is licensed under the MIT License. See the LICENSE file for details.
