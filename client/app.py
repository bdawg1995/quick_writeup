import requests
from prompt_toolkit import PromptSession, prompt
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import HTML, FormattedText
from prompt_toolkit.styles import Style
from prompt_toolkit.shortcuts import clear
from prompt_toolkit import print_formatted_text as print_text
from prompt_toolkit.widgets import TextArea, Label
from prompt_toolkit.layout import Layout, HSplit, VSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.application.current import get_app
from prompt_toolkit.layout.containers import DynamicContainer
from prompt_toolkit import Application

import argparse
import time
import datetime
import os
import uuid
import json
import re
from collections import defaultdict

CONFIG_PATH = os.path.expanduser("~/.qw_config.json")

def get_topics_path():
    # Check if the config file exists
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
            return config.get("topics_path")


topics_dir = get_topics_path()


def get_dirs(dir_path):
    if not os.path.isdir(dir_path):
        raise ValueError(f"The path {dir_path} is not a valid directory.")

    dirs = [
        name for name in os.listdir(dir_path)
        if os.path.isdir(os.path.join(dir_path, name))
    ]

    return dirs


def get_and_sort_uuid_date_json_objects(dir_path):
    if not os.path.isdir(dir_path):
        raise ValueError(f"The path {dir_path} is not a valid directory.")

    # Regular expression to match 'uuid_date.json' pattern
    pattern = r"^([a-f0-9\-]{36})_(\d{4}-\d{2}-\d{2})_writeup\.json$"

    json_objects = []

    for file in os.listdir(dir_path):
        match = re.match(pattern, file)
        if match:
            file_path = os.path.join(dir_path, file)
            try:
                # Load JSON content
                with open(file_path, "r") as f:
                    data = json.load(f)

                # Validate required keys
                if all(key in data for key in ["uuid", "date", "writeup"]):
                    json_objects.append(data)


            except json.JSONDecodeError:
                pass
            except Exception as e:
                pass

    # Sort by the 'date' field
    json_objects.sort(key=lambda x: x["date"])

    return json_objects


def get_topic_entries():
    return [
        {"date": "2024-11-01", "topic": "Work", "content": "Completed the project."},
        {"date": "2024-11-05", "topic": "Personal", "content": "Went hiking today."},
        {"date": "2024-11-10", "topic": "Work", "content": "Meeting with clients."},
        {"date": "2024-11-12", "topic": "Hobbies", "content": "Painted a landscape."},
        {"date": "2024-11-15", "topic": "Work", "content": "Prepared the presentation."},
    ]

def get_sorted_topic_entries(topic_entries, filter_topic=None):
    if filter_topic:
        topic_entries = [entry for entry in topic_entries if entry["topic"] == filter_topic]

    return sorted(
        topic_entries,
        key=lambda entry: (entry["topic"], entry["date"])
    )


def clear_text():
    return ""


def start():
    session = PromptSession()

    kbt = KeyBindings()

    topic_choices_index = 0
    journal_list_index = 0

    is_topic_list = True
    is_journal_list = False
    is_writeup = False

    is_exited = False;

    topic_choices = []

    topic_entries = []

    last_topic_choice = ""
    last_topic_entry_uuid = ""

    state = ""
    last_state = ""

    header = None
    content = None
    footer = None

    show_msg = False
    msg = ""

    show_warning_msg = False
    warning_msg = ""

    text_edit = None

    debug_mode = True


    # Styling for the highlighted selection
    style = Style.from_dict({
        "highlighted": "reverse",
        "header": "bg:#ffffff fg:#000000",
        "normal": "",
    })

    editable_text = "Enter your writeup here..."
    doc_content = TextArea(text=editable_text, scrollbar=True, line_numbers=False)

    get_topic_list_prompt_texts = [clear_text]
    get_journal_list_prompt_texts = [clear_text]


    def init_last_topic_choice(topic_choices):
        nonlocal last_topic_choice, topic_choices_index

        if len(topic_choices) == 0:
            last_topic_choice = ""
            return

        if last_topic_choice == "" and len(topic_choices) > 0:
            last_topic_choice = topic_choices[0]
            topic_choices_index = 0
            return

        if not last_topic_choice == "":
            if last_topic_choice in topic_choices:
                topic_choices_index = topic_choices.index(last_topic_choice)

            elif len(topic_choices) > 0:
                last_topic_choice = ""

            else:
                last_topic_choice = ""

            return


    def init_last_topic_entry(topic_entries):
        nonlocal last_topic_entry_uuid, journal_list_index

        if len(topic_entries) == 0:
            last_topic_entry_uuid = ""
            return

        if last_topic_entry_uuid == "" and len(topic_entries) > 0:
            last_topic_entry_uuid = topic_entries[0]["uuid"]
            journal_list_index = 0
            return

        if not last_topic_entry_uuid == "":
            if any(obj.get("uuid") == last_topic_entry_uuid for obj in topic_entries):
                journal_list_index = next((i for i, obj in enumerate(topic_entries) if obj["uuid"] == last_topic_entry_uuid), -1)


            elif len(topic_entries) > 0:
                last_topic_entry_uuid = ""

            else:
                last_topic_entry_uuid = ""

            return

    def get_topic_list_prompt_text():
        nonlocal topic_choices, topic_choices_index

        topic_choices = get_dirs(topics_dir)

        init_last_topic_choice(topic_choices)

        lines = []

        lines.append( (("class:normal", f"{"|===   Writeup Topics   ===|"}\n")) )
        lines.append(("class:normal",f"{"============================="}"))
        lines.append(("class:normal",f"{'\n'}"))

        for i, choice in enumerate(topic_choices):
            if i == topic_choices_index:
                lines.append(("class:highlighted", f" {'>'} {choice}{'  '}\n"))

            else:
                lines.append(("class:normal", f"  {choice}{'  '}\n"))

        lines.append(("class:normal",f"{'\n\n'}"))

        return FormattedText(lines)


    def get_journal_list_prompt_text():
        nonlocal topic_choices, topic_choices_index, journal_list_index, topic_entries

        topic_entries = get_and_sort_uuid_date_json_objects(f"{topics_dir}{"/"}{topic_choices[topic_choices_index]}")

        init_last_topic_entry(topic_entries)

        lines = []

        lines.append(("class:normal", f"{"|===   Writeup Entries  "}{"<"}{topic_choices[topic_choices_index]}{">"}{"   ===|"}\n"))
        lines.append(("class:normal",f"{"==================================" + "="*len(topic_choices[topic_choices_index])}"))
        lines.append(("class:normal",f"{'\n'}"))

        for i, entry in enumerate(topic_entries):
            if i == journal_list_index:
                lines.append(("class:highlighted", f" {">"} {topic_entries[i]['date']}{"  "}{"["}{topic_entries[i]['uuid'][:4]}{"]"}{"  "}\n"))

            else:
                lines.append(("class:normal", f"  {topic_entries[i]['date']}{"  "}{"["}{topic_entries[i]['uuid'][:4]}{"]"}{"  "}\n"))


        lines.append(("class:normal",f"{'\n\n'}"))

        return FormattedText(lines)


    def get_prompt_text():
        nonlocal state, last_state

        if state == "topic_list":
            return get_topic_list_prompt_text()

        if state == "journal_list":
            return get_journal_list_prompt_text()

        if state == "writeup":
            return clear_text()

        if state == "create_writeup":
            return clear_text()


    def ensure_topic_directory(topic, dir):
        topic_dir = os.path.join(dir, topic)
        if not os.path.exists(topic_dir):
            os.makedirs(topic_dir)

        return topic_dir


    def validate_date_format(date_str):
        parts = date_str.split("-")

        if len(parts) != 3:
            raise ValueError(f"Invalid date format: {date_str}. Expected format is YYYY-MM-DD.")

        year, month, day = parts

        if not (year.isdigit() and len(year) == 4):
            raise ValueError(f"Invalid year in date: {date_str}. Expected format is YYYY-MM-DD.")

        if not (month.isdigit() and 1 <= int(month) <= 12):
            raise ValueError(f"Invalid month in date: {date_str}. Month must be between 01 and 12.")

        if not (day.isdigit() and 1 <= int(day) <= 31):
            raise ValueError(f"Invalid day in date: {date_str}. Day must be between 01 and 31.")

        # Optional: Check for valid days in a specific month
        if int(month) in {4, 6, 9, 11} and int(day) > 30:
            raise ValueError(f"Invalid day in date: {date_str}. Month {month} has only 30 days.")
        if int(month) == 2:
            # Check for February (leap year logic)
            year = int(year)
            if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):  # Leap year
                if int(day) > 29:
                    raise ValueError(f"Invalid day in date: {date_str}. February has only 29 days in a leap year.")
            else:
                if int(day) > 28:
                    raise ValueError(f"Invalid day in date: {date_str}. February has only 28 days in a non-leap year.")


    def extract_writeup_details(buffer_text, uuid_str):
        lines = buffer_text.splitlines()

        topic = None
        date = None
        writeup = None

        try:
            if len(lines) < 3 or not lines[0].startswith("Topic:") or not lines[1].startswith("Date :") or not lines[2].startswith("=============================="):
                print(len(lines), lines[0].startswith("Topics:"))
                raise ValueError(f"Buffer text is not formatted correctly.")

            topic  = lines[0].split(":", 1)[1].strip()
            date = lines[1].split(":", 1)[1].strip()

            if not topic:
                raise ValueError("Topic is empty!")

            if not date:
                raise ValueError("Date is empty!")


            validate_date_format(date)

            # when writeup is empty
            if len(lines) == 3:
                return {
                    "uuid": uuid_str,
                    "topic": topic,
                    "date": date,
                    "writeup": "",
                }

            writeup = "\n".join(lines[3:])

        except Exception as e:
            raise ValueError(f"Error processing buffer text: {e}")

        return {
            "uuid": uuid_str,
            "topic": topic,
            "date": date,
            "writeup": writeup,
        }


    @kbt.add("c-g")
    def create_writeup(event):
        nonlocal state, last_state

        last_state = state
        state = "create_writeup"

        # Clear previous text
        text_edit.buffer.text = ""

        event.app.layout.focus(text_edit)

        # text_edit.buffer.insert_text("||!!  DO NOT MODIFY or REMOVE the default text below. Doing so may prevent the CREATION of the new writeup. !!||")
        # text_edit.buffer.insert_text("\n\n")

        text_edit.buffer.insert_text("Topic:")
        text_edit.buffer.insert_text("\n")
        text_edit.buffer.insert_text("Date :")
        text_edit.buffer.insert_text("\n")

        text_edit.buffer.insert_text("==============================")
        text_edit.buffer.insert_text("\n")
        text_edit.buffer.insert_text("Type your writeup here  ......")


    @kbt.add("c-s")
    def save(event):
        global topics_dir
        nonlocal state, last_state, show_msg, msg, last_topic_choice

        if state == "writeup":
            entry = topic_entries[journal_list_index]

            buffer_text = text_edit.buffer.text
            uuid_str = entry["uuid"]

            try:
                new_details = extract_writeup_details(buffer_text, uuid_str)

                # Retain the old topic directory as is
                old_topic_dir = os.path.join(topics_dir, last_topic_choice)

                old_filename = f"{entry['uuid']}_{entry['date']}_writeup.json"

                # Sanitize only the new topic directory
                new_topic_dir = os.path.join(topics_dir, new_details["topic"].replace(" ", "_"))

                # Keep the same filename
                new_file_path = os.path.join(new_topic_dir, old_filename)

                # Remove 'topic' key from the details
                new_details.pop("topic", None)

                os.makedirs(new_topic_dir, exist_ok=True)

                with open(new_file_path, "w") as f:
                    json.dump(new_details, f, indent=4)

                    show_msg = True
                    msg = new_file_path

                # Remove the old file after successfully saving the new one
                old_file_path = os.path.join(old_topic_dir, old_filename)
                if not old_file_path == new_file_path:
                    if os.path.isfile(old_file_path):
                        os.remove(old_file_path)

            except ValueError as e:
                # Notify user of error
                footer.content = FormattedTextControl(f"Error: {e}")

            state = last_state
            last_state = "writeup"

        if state == "create_writeup":
            buffer_text = text_edit.buffer.text
            uuid_str = str(uuid.uuid4())

            try:
                # Parse the writeup details
                details = extract_writeup_details(buffer_text, uuid_str)

                # Sanitize only the new topic directory
                topic_dir = os.path.join(topics_dir, details["topic"].replace(" ", "_"))

                details.pop("topic", None)

                os.makedirs(topic_dir, exist_ok=True)

                # Generate the filename
                filename = f"{uuid_str}_{details['date']}_writeup.json"
                file_path = os.path.join(topic_dir, filename)

                # Save the details as a JSON file
                with open(file_path, "w") as f:
                    json.dump(details, f, indent=4)

                    show_msg = True
                    msg = "Successfully created writeup!"

            except ValueError as e:
                # Notify user of error
                footer.content = FormattedTextControl(f"Error: {e}")

            state = last_state
            last_state = "create_writeup"


    @kbt.add("c-b")
    def back(event):
        nonlocal state, last_state, topic_choices_index, journal_list_index, last_topic_choice

        if state == "journal_list":
            last_state = state
            state = "topic_list"

            return

        if state == "create_writeup":
            state = last_state

            return

        if state == "writeup":
            state = last_state

            return


    @kbt.add("up")
    def move_up(event):
        nonlocal state, topic_choices_index, journal_list_index, last_topic_choice, last_topic_entry_uuid

        if state == "topic_list":
            if topic_choices_index > 0:
                topic_choices_index -= 1

                # Cache the last selected topic
                last_topic_choice = topic_choices[topic_choices_index]

            return

        if state == "journal_list":
            if journal_list_index > 0:
                journal_list_index -= 1

                # Cache the last selected entry
                last_topic_entry_uuid = topic_entries[journal_list_index]["uuid"]

            return

        if state == "writeup":
            text_edit.buffer.cursor_up()
            return

        if state == "create_writeup":
            if text_edit.buffer.cursor_position < 17:
                text_edit.buffer.cursor_right()

            text_edit.buffer.cursor_up()
            return


    @kbt.add("c-x")
    def exit(event):
        event.app.exit()


    @kbt.add("down")
    def move_down(event):
        nonlocal state, topic_entries, topic_choices, topic_choices_index, journal_list_index, last_topic_choice, last_topic_entry_uuid

        if state == "topic_list":
            if topic_choices_index < len(topic_choices) - 1:
                topic_choices_index += 1

                # Cache the last selected topic
                last_topic_choice = topic_choices[topic_choices_index]

            return

        if state == "journal_list":
            if journal_list_index < len(topic_entries) - 1:
                journal_list_index += 1

                # Cache the last selected entry
                last_topic_entry_uuid = topic_entries[journal_list_index]["uuid"]

            return

        if state == "writeup":
            text_edit.buffer.cursor_down()
            return


        if state == "create_writeup":
            text_edit.buffer.cursor_down()
            return


    @kbt.add("enter")
    def enter(event):
        nonlocal state, last_state, topic_entries, topic_choices_index, journal_list_index, last_topic_choice, journal_list_index


        if state == "topic_list":
            last_state = state
            state = "journal_list"

            # Cache the last selected topic
            last_topic_choice = topic_choices[topic_choices_index]

            # Start from 1st entry
            journal_list_index = 0

            return

        if state == "journal_list":
            last_state = state
            state = "writeup"

            text_edit.buffer.text = ""
            text_edit.buffer.insert_text(f"Topic:{topic_choices[topic_choices_index]}\n")
            text_edit.buffer.insert_text(f"Date :{topic_entries[journal_list_index]["date"]}\n")
            text_edit.buffer.insert_text("==============================\n")
            text_edit.buffer.insert_text(topic_entries[journal_list_index]["writeup"])

            event.app.layout.focus(text_edit)
            return

        if state == "writeup":
            text_edit.buffer.insert_text("\n")
            return

        if state == "create_writeup":
            text_edit.buffer.insert_text("\n")
            return


    def get_msg():
        nonlocal state, last_state, show_msg, msg

        # Dynamically calculate center alignment
        terminal_width = get_app().output.get_size().columns
        centered_text = msg
        padding = (terminal_width - len(centered_text)) // 2

        if not state == "create_writeup" and show_msg and last_state == "create_writeup":
            return HTML(
                f'{" " * padding}<b>{centered_text}</b>\n'
            )

        if not state == "writeup" and show_msg and last_state == "writeup":
            return HTML(
                f'{" " * padding}<b>{centered_text}</b>\n'
            )

        if debug_mode:
            return HTML(f"<b>{journal_list_index}\n{last_topic_entry_uuid}</b>")


        return HTML("<b></b>")


    def get_footer():
        nonlocal state, last_state

        if state == "topic_list":
            return HTML(
                '<b><style fg="yellow">Options ~</style></b>\n'
                '<b><style fg="yellow">&lt;-</style></b> <b><style fg="white">View</style></b>\n'
                '<b><style fg="yellow">^G</style></b> <b><style fg="white">Writeup</style></b>\n'
                '<b><style fg="yellow">^X</style></b> <b><style fg="white">Exit</style></b>'
                )

        if state == "journal_list":
            return HTML(
                    '<b><style fg="yellow">Options ~</style></b>\n'
                    '<b><style fg="yellow">&lt;-</style></b> <b><style fg="white">Edit</style></b>\n'
                    '<b><style fg="yellow">^G</style></b> <b><style fg="white">Writeup</style></b>\n'
                    '<b><style fg="yellow">^B</style></b> <b><style fg="white">Back</style></b>\n'
                    '<b><style fg="yellow">^X</style></b> <b><style fg="white">Exit</style></b>'
                )


        if state == "writeup":
            return HTML(
                    '<b><style fg="yellow">Options ~</style></b>\n'
                    '<b><style fg="yellow">^S</style></b> <b><style fg="white">Save</style></b>\n'
                    '<b><style fg="yellow">^B</style></b> <b><style fg="white">Back</style></b>\n'
                    '<b><style fg="yellow">^X</style></b> <b><style fg="white">Exit</style></b>'
                )

        if state == "create_writeup":
            return HTML(
                    '<b><style fg="yellow">Options ~</style></b>\n'
                    '<b><style fg="yellow">^S</style></b> <b><style fg="white">Create</style></b>\n'
                    '<b><style fg="yellow">^B</style></b> <b><style fg="white">Back</style></b>\n'
                    '<b><style fg="yellow">^X</style></b> <b><style fg="white">Exit</style></b>'
                )


    def is_writeup_mode():
        return state == "writeup" or state == "create_writeup"


    state = "topic_list"
    last_state = state

    text_edit = TextArea(text="", scrollbar=True)

    header = Window(
        content=FormattedTextControl(text=" QWup - Quick Writeup  "),
        style="class:header",
        height=1,
        always_hide_cursor=True,
    )

    edit_msg = Window(
        content=FormattedTextControl(lambda: get_msg()),
            always_hide_cursor=True,
            )

    footer = Window(
        content=FormattedTextControl(lambda: get_footer()),
            always_hide_cursor=True,
            )

    content = DynamicContainer(lambda: text_edit if is_writeup_mode() else Window(
        content=FormattedTextControl(text=get_prompt_text),
        always_hide_cursor=True,
    ))

    # Define layout
    layout = Layout(
        HSplit(
            [header, content, edit_msg, footer]
                )
            )

    # Create the application
    app = Application(
        layout=layout,
        key_bindings=kbt,
        full_screen=True,
        refresh_interval=0.3,
        style=style,
        )

    app.run()


def view_entry_content():
    """Retrieve and display the content of a specific journal entry based on date and topic."""
    # Prompt user for date and topic of the specific entry
    date = get_date()
    topic = input("Enter the topic for this journal entry: ")

    # Prepare payload to retrieve specific entry content
    payload = {
        "date": date,
        "topic": topic,
        "key": VIEW_KEY
    }

    # Send request to retrieve entry content
    try:
        response = requests.post(f"{VIEW_URL}/content", json=payload)
        if response.status_code == 200:
            print("Journal entry for", date)
            print(response.json().get("content", "No content found."))
        else:
            print("Failed to retrieve entry:", response.json())
    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve entry content due to a request error: {e}")


# Function to display help information
def show_help():
    """Display usage instructions for the CLI tool."""
    help_text = """
    Quick Writeup Client CLI

    Usage:
    - To start Quick Writeup: Start running with `-s`.
    """
    print(help_text)


if __name__ == "__main__":
    # Parse command-line arguments for different actions
    parser = argparse.ArgumentParser(description="Journal CLI tool")
    parser.add_argument('-s', action='store_true', help="Start Quick Writeup")
    args = parser.parse_args()

    if args.s:
        start()
    else:
        show_help()
