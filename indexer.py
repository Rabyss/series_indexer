#!/usr/bin/python3

import os, re, argparse, json, subprocess
from collections import defaultdict

def parse_args():
    parser = argparse.ArgumentParser(description='Index series folder')
    parser.add_argument('directory', nargs='?', metavar='directory', help='Directory to work on, default is current directory', default=os.getcwd())
    parser.add_argument('-i', '--index', dest='index', help='Create index  with specified season/episode pattern (APPLIED BEFORE NEXT/BACK)')
    parser.add_argument('-n', '--next', dest='next', default='0', type=int, help='Move cursor to nth next episode (APPLIED BEFORE WATCH)')
    parser.add_argument('-p', '--prev', dest='prev', default='0', type=int, help='Move cursor to nth previous episode (APPLIED BEFORE WATCH)')
    parser.add_argument('-w', '--watch', dest='do_watch', action='store_true', help='Watch episode then move cursor to next episode')
    parser.add_argument('-s', '--show', dest='do_show', action='store_true', help='Show current episode number')
    parser.add_argument('-l', '--list', dest='do_list', action='store_true', help='Lists the indexed episodes')
    parser.add_argument('-e', '--executable', default='mpv', help='Executable to watch')

    args = parser.parse_args()

    return args

def main():
    args = parse_args()
    if args.index:
        index(args.directory, args.index)

    if args.next:
        move_cursor(args.directory, args.next)

    if args.prev:
        move_cursor(args.directory, -args.prev)

    if args.do_watch:
        watch(args.directory, args.executable)

    if args.do_list:
        list_episodes(args.directory)

    if args.do_show and not args.do_list:
        show_cursor(args.directory)

def get_index(directory):
    index_path = os.path.join(directory, '.index')
    if os.path.isfile(index_path):
        with open(index_path, 'r') as f:
            return json.loads(f.read())
    else:
        return {'items': []}

def write_index(index, directory):
    index_path = os.path.join(directory, '.index')
    with open(index_path, 'w+') as f:
        f.write(json.dumps(index))

def season_episode(index, cursor):
    return index['items'][cursor]['season'], index['items'][cursor]['episode']

def print_cursor(prefix, index):
    print_season_episode(prefix, season_episode(index, index['cursor']))

def print_season_episode(prefix, season_episode):
    season, episode = season_episode
    print(prefix, 'season', season, 'episode', str(episode) + '.')

def index(directory, pattern):
    permitted_files = ['.avi', '.mp4', '.mkv']

    index = get_index(directory)
    new_index = defaultdict(dict)

    for episode in index['items']:
        new_index[episode['season']][episode['episode']] = episode['relpath']

    print('Searching in', directory, 'with', pattern)

    for dirpath, _, filenames in os.walk(directory):
        for filename in filenames:
            if not any(filename.endswith(term) for term in permitted_files):
                continue

            groups = re.search(pattern, filename).groups()
            season = int(groups[0])
            episode = int(groups[1])
            print_season_episode('Found', (season, episode))

            rel_path = os.path.relpath(dirpath, directory)
            new_index[season][episode] = os.path.join(rel_path, filename).split(os.sep)

    flattened = {'items': []}
    for season in sorted(new_index):
        for episode in sorted(new_index[season]):
            flattened['items'].append({'season': season, 'episode': episode, 'relpath': new_index[season][episode]})


    if 'cursor' not in index:
        flattened['cursor'] = 0
    else:
        cursor = index['cursor']
        ep_details = index['items'][cursor]
        matches = [i for i,x in enumerate(flattened['items']) if x['season'] == ep_details['season'] and x['episode'] == ep_details['episode']]
        flattened['cursor'] = matches[0] if matches else 0

    print_cursor('Cursor will be at', flattened)

    write_index(flattened, directory)

def move_cursor(directory, move_increment):
    index = get_index(directory)

    max_cursor = len(index['items']) - 1

    new_cursor = min(max_cursor, max(0, index['cursor'] + move_increment))

    index['cursor'] = new_cursor
    write_index(index, directory)
    print_cursor('New cursor is at', index)

def show_cursor(directory):
    index = get_index(directory)
    print_cursor('Cursor is at', index)

def list_episodes(directory):
    index = get_index(directory)
    cursor = index["cursor"]
    current_season = ''
    print("Episodes in index:")
    for i, episode in enumerate(index["items"]):
        output = ''
        if current_season != episode["season"]:
            print("Season", episode["season"])
            current_season = episode["season"]
        output += 'Episode ' + str(episode["episode"])
        if cursor == i:
            output = '>>> ' + output + ' <<<'
        output = '    ' + output
        print(output)

def watch(directory, executable):
    index = get_index(directory)
    path_to_vid = os.path.join(directory, *(index['items'][index['cursor']]['relpath']))
    print_cursor('Watching', index)
    print('Located at', path_to_vid)
    subprocess.run([executable, path_to_vid])
    move_cursor(directory, 1)

if __name__ == '__main__':
    main()
