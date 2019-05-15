from functools import reduce
import operator
from bs4 import BeautifulSoup
import re
import signal
import pprint
import urllib3
pp = pprint.PrettyPrinter(indent=1)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class CONFIG(object):
    domain = "https://en.wikipedia.org/wiki/"
    initial_subpage = "Vince_Evans"
    end_subpage = "Modern_history_of_American_football"
    max_links_per_page = 30
    # max_depth = 5  # Not sure how to implement :/


global wikipedia_tree, known_articles
wikipedia_tree = {}
known_articles = {}


def get_from_dict(dictionary: dict, path: list) -> dict:
    return reduce(operator.getitem, path, dictionary)


def set_in_dict(dictionary: dict, path: list, value):
    for key in path[:-1]:
        dictionary = dictionary.setdefault(key, {})
    dictionary[path[-1]] = value


def get_links(article: str, path: list, http_manager: urllib3.PoolManager):
    global wikipedia_tree, known_articles

    if article in known_articles:
        return known_articles[article]

    res = http_manager.request('GET', CONFIG.domain + article)
    if res.status != 200:
        print("bad request")
        return []

    soup = BeautifulSoup(res.data, "html.parser")
    all_links = soup.find_all('a',
                              href=re.compile(r'^/wiki/(?!file)'),
                              title=True,
                              alt=False,
                              style=False,
                              src=False,
                              target=False,
                              attrs={'class': None, 'id': None, 'rel': None})

    # Extract links, remove duplicates and remove '/wiki/'
    href_list = list(dict.fromkeys(element.get('href')[6:] for element in all_links))

    if len(soup.find_all('a',
                         href=f'/wiki/{CONFIG.end_subpage}',
                         title=True,
                         attrs={'class': None, 'id': None, 'rel': None})
           ) != 0:
        print("Found the target article, the path is: " + ' / '.join(path + [CONFIG.end_subpage]))

    if CONFIG.max_links_per_page == 0:
        links_to_add = len(href_list)
    else:
        links_to_add = min(len(href_list), CONFIG.max_links_per_page)

    known_articles[article] = href_list[:links_to_add]

    links = {}
    for i in range(links_to_add):
        links[href_list[i]] = {}

    set_in_dict(wikipedia_tree, path, links)
    # print(f"Added {links_to_add} to path: {'/'.join(path)}")
    return href_list[:links_to_add]


def signal_handler(sig, frame):
    global running
    print("Exiting loop...")
    running = False


signal.signal(signal.SIGINT, signal_handler)


http = urllib3.PoolManager()
queue = [(CONFIG.initial_subpage, [CONFIG.initial_subpage])]

running = True
while 0 < len(queue) and running:
    new_links = get_links(queue[0][0], queue[0][1], http)
    print("Path: " + '/'.join(queue[0][1]))
    for i in range(len(new_links)):
        queue.append((
            new_links[i],
            queue[0][1] + [new_links[i]]
        ))
    queue.pop(0)


print("\n\n")
pp.pprint(wikipedia_tree)


example_tree = {
    "Vince_Evans": {
        "American_football": {
            "Team_sport": {
                "Sport": {},
                "Sports_team": {},
                "Members_of_the_Red_Army_Faction": {}
            },
            "American_football_field": {
                "Pitch_(sports field)": {},
                "American_football": {},
                "Hash_marks": {}
            },
            "Offense_(sports)": {
                "American_English": {},
                "Canadian_English": {},
                "American_and_British_English_spelling_differences": {}
            }
        },
        "Quarterback": {

        },
        "Chicago_Bears": {

        }
    }
}


'''
current_layer_index = 0
for L in range(max_depth):
    layer = [*get_from_dict(wikipedia_tree, current_path)]
    current_path.append(None)
    for i in range(len(layer)):
        current_path[-1] = layer[i]
        get_links(layer[i], current_path, http)
    current_path[-1] = layer[current_layer_index]
    current_layer_index += 1
''''''
for L in range(max_depth):
    print(f"\nCurrent depth: {L + 1}, current path: {current_path}")
    current_layer = [*get_from_dict(wikipedia_tree, current_path)]

    current_path.append(None)
    for i in range(len(current_layer)):
        current_path[-1] = current_layer[i]
        get_links(current_layer[i], current_path, http)

    #current_path.append(None)
    #for x in range(len(current_layer)):
    #    current_path[-1] = current_layer[x]
    #    print(f"Current path: {'/'.join(current_path)}")
    #    get_links(current_layer[x], current_path, http)

    #print(f"\nCurrent depth: {i + 1}, current path: {current_path}")

    #current_path[-1] = current_layer[0]
    current_layer = [*get_from_dict(wikipedia_tree, current_path)]
    current_path.append(None)
    for x in range(len(current_layer)):
        current_path[-1] = current_layer[x]
        #print(f"Current path: {'/'.join(current_path)}")
        get_links(current_layer[x], current_path, http)
        #if not len(current_layer) == x+1:
        #    current_path[-1] = current_layer[x+1]
'''

