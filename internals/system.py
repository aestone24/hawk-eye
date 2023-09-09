from rich.console import Console
from rich.table import Table
import random
import yaml
import re
import os
import argparse
import requests
import json

console = Console()
parser = argparse.ArgumentParser(description='CLI Command Executor')
parser.add_argument('--debug', action='store_true', help='Enable debug mode')
parser.add_argument('--shutup', action='store_true', help='Suppress the Hawk Eye banner 🫣', default=False)
args, extra_args = parser.parse_known_args()

def print_info(message):
    console.print(f"[yellow][INFO][/yellow] {message}")

def print_debug(message):
    if args.debug:
        console.print(f"[blue][DEBUG][/blue] {message}")

def print_error(message):
    console.print(f"[bold red]❌ {message}")

def print_success(message):
    console.print(f"[bold green]✅ {message}")

def print_info(message):
    console.print(f"[yellow][INFO][/yellow] {message}")
def print_alert(message):
    console.print(f"[bold red][ALERT][/bold red] {message}")

def print_banner():
    banner = r"""
                                /T /I
                                / |/ | .-~/
                            T\ Y  I  |/  /  _
            /T               | \I  |  I  Y.-~/
            I l   /I       T\ |  |  l  |  T  /
        T\ |  \ Y l  /T   | \I  l   \ `  l Y
    __  | \l   \l  \I l __l  l   \   `  _. |
    \ ~-l  `\   `\  \  \\ ~\  \   `. .-~   |
    \   ~-. "-.  `  \  ^._ ^. "-.  /  \   |
    .--~-._  ~-  `  _  ~-_.-"-." ._ /._ ." ./
    >--.  ~-.   ._  ~>-"    "\\   7   7   ]
    ^.___~"--._    ~-{  .-~ .  `\ Y . /    |
    <__ ~"-.  ~       /_/   \   \I  Y   : |
    ^-.__           ~(_/   \   >._:   | l______
        ^--.,___.-~"  /_/   !  `-.~"--l_ /     ~"-.                 + ================================================== +
                (_/ .  ~(   /'     "~"--,Y   -=b-. _)               + [bold yellow]H[/bold yellow].[bold yellow]A[/bold yellow].[bold yellow]W[/bold yellow].[bold yellow]K[/bold yellow] [bold yellow]Eye[/bold yellow] - [bold blue]Highly Advanced Watchful Keeper Eye[/bold blue] +
                (_/ .  \  :           / l      c"~o \               + ================================================== +
                    \ /    `.    .     .^   \_.-~"~--.  )                 
                    (_/ .   `  /     /       !       )/                   Hunt for Secrets & PII Data, like never before!
                    / / _.   '.   .':      /        '                           A Tool by [bold red]Rohit Kumar (@rohitcoder)[/bold red]
                    ~(_/ .   /    _  `  .-<_                                    
                        /_/ . ' .-~" `.  / \  \          ,z=.
                        ~( /   '  :   | K   "-.~-.______//
                        "-,.    l   I/ \_______{--->._(=====.
                        //(     \  <                  \\
                        /' /\     \  \                 \\
                        .^. / /\     "  }__ //===--`\\
                    / / ' '  "-.,__ {---(==-
                    .^ '       :  T  ~"   ll       
                    / .  .  . : | :!        \\
                (_/  /   | | j-"             ~^~^
                    ~-<_(_.^-~"
    """
    if not args.shutup:
        console.print(banner)

def get_patterns_from_file(file_path):
    with open(file_path, 'r') as file:
        patterns = yaml.safe_load(file)
        return patterns

def match_strings(content):
    matched_strings = []
    fingerprint_file = 'fingerprint.yml'
    patterns = get_patterns_from_file(fingerprint_file)

    for pattern_name, pattern_regex in patterns.items():
        print_debug(f"Matching pattern: {pattern_name}")
        found = {} 
        ## parse pattern_regex as Regex
        complied_regex = re.compile(pattern_regex, re.IGNORECASE)
        matches = re.findall(complied_regex, content)
        if matches:
            found['pattern_name'] = pattern_name
            found['matches'] = matches
            found['sample_text'] = content[:50]
            matched_strings.append(found)
    return matched_strings

def should_exclude_file(file_name, exclude_patterns):
    _, extension = os.path.splitext(file_name)
    if extension in exclude_patterns:
        print_debug(f"Excluding file: {file_name} because of extension: {extension}")
        return True
    
    for pattern in exclude_patterns:
        if pattern in file_name:
            print_debug(f"Excluding file: {file_name} because of pattern: {pattern}")
            return True
    return False

def should_exclude_folder(folder_name, exclude_patterns):
    for pattern in exclude_patterns:
        if pattern in folder_name:
            return True
    return False

def list_all_files_iteratively(path, exclude_patterns):
    for root, dirs, files in os.walk(path, topdown=True):
        dirs[:] = [d for d in dirs if not should_exclude_folder(os.path.join(root, d), exclude_patterns)]

        for file in files:
            if not should_exclude_file(file, exclude_patterns):
                yield os.path.join(root, file)

def read_match_strings(file_path, source):
    print_info(f"Scanning file: {file_path}")
    content = ''
    try:
        with open(file_path, 'r') as file:
            content = file.read()
    except Exception as e:
        pass
    matched_strings = match_strings(content)
    return matched_strings

def SlackNotify(msg):
    with open('connection.yml', 'r') as file:
        connections = yaml.safe_load(file)

    if 'notify' in connections:
        slack_config = connections['notify'].get('slack', {})
        webhook_url = slack_config.get('webhook_url', '')
        if webhook_url != '':
            try:
                payload = {
                    'text': msg,
                }
                headers = {'Content-Type': 'application/json'}
                requests.post(webhook_url, data=json.dumps(payload), headers=headers)
            except Exception as e:
                print_error(f"An error occurred: {str(e)}")
