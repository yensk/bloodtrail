#!/usr/bin/env python3

from argparse import RawTextHelpFormatter,ArgumentParser, ArgumentDefaultsHelpFormatter
import neo4j
from datetime import datetime
import log
import session_parser
import helpers
from neo4j import Auth, GraphDatabase
from neo4j.exceptions import ServiceUnavailable

def print_list(list):
    for i in list:
        if i != "":
            print(i)

def print_query_results(query):
    results = element_query(query)
    for r in results:
        print(r)

def print_outdated_systems():
    os_attribute="operatingsystem"
    systems = element_query('MATCH (n:Computer) WHERE n.operatingsystem =~ "(?i).*(2000|2003|2008|xp|vista|7|me).*" RETURN n', [os_attribute, "lastlogontimestamp"])

    if output_list:
        print_list(systems)
    else:
        print(f"{'SYSTEM':<25}   {'Last Logon':<15}        Version  ")
        print("")
        for name in sorted(systems.keys()):
            print(f"{name.upper():<25}:  {datetime.utcfromtimestamp(int(systems[name]['lastlogontimestamp'])).strftime('%Y-%m-%d %H:%M:%S')}    {systems[name][os_attribute]}  ")

def print_computers_with_path_to_high_value(withsessions=False):
    computers = element_query("match shortestPath((c:Computer)-[r *]->(g {highvalue:true})) where c <> g return c")

    if withsessions:
        print_computer_sessions(sorted(computers))
    else:
        for u in sorted(computers):
            print(u)

def print_users_with_path_to_high_value(withsessions=False):
    users = element_query("match shortestPath((u:User)-[r *]->(g {highvalue:true})) where u <> g return u")

    if withsessions:
        print_user_sessions(sorted(users))
    else:
        for u in sorted(users):
            print(u)

def print_user_sessions(user_names):
    for user_name in user_names:
        user_name = user_name.upper()
        # Check if we have accurate data from sharphound files
        if session_parser.parsed_user_sessions != None:
            computers = session_parser.parsed_user_sessions[user_name]

            if output_list:
                print_list(computers)
            else:
                sorted_elements = sorted(computers, key=lambda x: len(computers[x]), reverse=True)
                if list_timestamps:
                    print_str = ""
                    user_n = user_name
                    for c in sorted_elements:
                        print_str += f"{user_n.upper():<25}:   {c:<20}: "+f"\n{'':<51}".join([helpers.get_printable_timestamp(x) for x in sorted(computers[c])])+"\n"
                        user_n = ""
                    print(print_str)
                else:
                    print_str = ", ".join([c+" ("+str(len(computers[c]))+")" for c in sorted_elements])
                    print(f"{user_name.upper():<25}:   {print_str}")
        else:
            computers = element_query("MATCH (c:Computer)-[r:HasSession]->(u:User {name:'"+user_name.upper()+"'}) return c")

            if output_list:
                print_list(computers)
            else:
                print_str = ", ".join(sorted(computers))        
                print(f"{user_name.upper():<25}:   {print_str}")

def print_all_user_sessions():
    users = element_query("MATCH (u:User) return u")
    print_user_sessions(sorted(users))

def print_psexec_computers():
    computers = element_query('MATCH (c:Computer) WHERE c.psexec_local_admin <> "not allowed" or c.psexec_builtin_admin <> "not allowed" return c')

    for c in sorted(computers):
        print(c)

def print_object_groups(objects):
    for object_name in objects:
        group_names = element_query("MATCH (c {name:'"+object_name.upper()+"'})-[r *]->(g:Group) return g")

        for g in sorted(group_names):
            print(g)

def print_all_computer_sessions():
    computer_names = element_query("MATCH (c:Computer) return c")
    print_computer_sessions(computer_names)

def print_computer_sessions(computer_names):
    for computer_name in computer_names:
        computer_name = computer_name.upper()
        # Check if we have accurate data from sharphound files
        if session_parser.parsed_computer_sessions != None:
            users = session_parser.parsed_computer_sessions[computer_name]

            if output_list:
                print_list(users)
            else:
                sorted_elements = sorted(users, key=lambda x: len(users[x]), reverse=True)
                if list_timestamps:
                    print_str = ""
                    computer_n = computer_name
                    for c in sorted_elements:
                        print_str += f"{computer_n.upper():<25}:   {c:<20}: "+f"\n{'':<51}".join([helpers.get_printable_timestamp(x) for x in sorted(users[c])])+"\n"
                        computer_n = ""
                    print(print_str)
                else:
                    print_str = ", ".join([c+" ("+str(len(users[c]))+")" for c in sorted_elements])
                    print(f"{computer_name.upper():<25}:   {print_str}")
        else:
            logged_in_users = element_query("MATCH p=(c:Computer {name:'"+computer_name.upper()+"'})-[r:HasSession]->(u)  return u")

            if output_list:
                print_list(logged_in_users)
            else:
                users = ", ".join(sorted(logged_in_users))
                print(f"{computer_name:<25}:  {users}")

def element_query(query, attributes=[]):
    results = session.run(query)
    results = results.values()
    
    res = {}

    for i in results:
        for i2 in i:
            res_item = {}
            for attr in attributes:
                if attr in i2.keys():
                    res_item[attr] = i2[attr]
                else:
                    print("ERROR, entry does not contain requested key: "+str(i2))

            if "name" in i2.keys():
                res[i2["name"]]=res_item
            elif "azname" in i2.keys():
                res[i2["azname"]]=res_item
            elif "objectid" in i2.keys():
                res[i2["objectid"]]=res_item
            else:
                print("ERROR: "+str(i2))
                continue

    if len(attributes) == 0:
        return sorted(res.keys())
    return res

def print_smb_signing_targets(typefilter=[]):
    f = ""
    if len(typefilter) > 0:
        f=":"+"|".join(typefilter)
    res = element_query('MATCH (a'+f+' {hassigning: false}) RETURN a')
    print_list(res)

def print_high_value_targets(typefilter=[]):
    f = ""
    if len(typefilter) > 0:
        f=":"+"|".join(typefilter)
    res = element_query('MATCH (a'+f+' {highvalue: true}) RETURN a')
    print_list(res)

def print_owned_targets(typefilter=[]):
    f = ""
    if len(typefilter) > 0:
        f=":"+"|".join(typefilter)
    res = element_query('MATCH (a'+f+' {owned: true}) RETURN a')
    print_list(res)

def get_objects_with_path_to_high_value(typefilter=[]):
    f = ""
    if len(typefilter) > 0:
        f=":"+"|".join(typefilter)
    res = element_query('MATCH p = allShortestPaths((u'+f+')-[r *1..]->(h)) WHERE u<>h AND h.highvalue = true RETURN u')
    return res

def print_objects_with_path_to_high_value(filter=[]):
    objects = get_objects_with_path_to_high_value(filter)
    print_list(objects)

def print_names(graph_objects, filter =""):
    out = set()

    for item in graph_objects:
        for item2 in item:
            if isinstance(item2, neo4j.graph.Path):
                item2 = item2.start_node
            if filter in item2.labels:
                if "name" in item2.keys():
                    out.add(item2["name"])
                elif "azname" in item2.keys():
                    out.add(item2["azname"])
                else:
                    out.add("ERROR")
    for item in sorted(out):
        print(item)

def set_object_prop(object_names, property_to_set, comment = ""):
    log_comment = '(comment: ' + comment + ')'
    for o_name in object_names:
        item = o_name.strip().upper()
        log.logger.debug('[+] Setting properties for: ' + item)
        query = 'MATCH (a {name: $name}) SET a.' + property_to_set + ', a.bloodtrail = $comment RETURN COUNT(*) AS count'
        results = session.run(query, name = item, comment = log_comment)

        count = results.single()['count']

        if count > 0:
            log.logger.info('[ ] Done: ' + item)
        else:
            log.logger.error('[-] Modification failed: ' + item)



mode_help=[
"* hosts: List all hosts.",
"* users: List all users.",
"* juicy_computers: List all computers that have a path to a highvalue target.",
"* juicy_computer_sessions: List all computers that have a path to a highvalue target and the users that have a session on them. This can provide you a hint at login rights, that Bloodhound is not able to capture by itself.",
"* juicy_users: List all users that have a path to a highvalue target.",
"* juicy_user_sessions: List all users that have a path to a highvalue target and the machines that they are logged on to.",
"* juicy_objects: List all objects that have a path to a highvalue target.",
"* all_user_sessions: List all users and their open sessions. Provides session count if raw Sharphound files are provided with -r.", 
"* user_sessions: List open sessions for the provided users. Users can be provided either as arguments or using the -i switch. Provides session count if raw Sharphound files are provided with -r.",
"* all_computer_sessions: List all computers and their open sessions. Provides session count if raw Sharphound files are provided with -r.",
"* computer_sessions: List open sessions on the provided computers. Computers can be provided either as arguments or using the -i switch. Provides session count if raw Sharphound files are provided with -r.",
"* outdated_systems: List outdated systems.",
"* high_value: List highvalue objects.",
"* owned: List owned objects.",
"* psexec_computers: List of computers that have psexec enabled",
"* groups: List groups of the provided objects. Objects can be provided either as arguments or using the -i switch.",
"* query: List the resulting objects of a custom query. The query has to be provided as argument.",
"* set_owned: Set the owned attribute for specified objects in the Bloodhound database. Objects can be provided either as arguments or using the -i switch.",
"* unset_owned: Unset the owned attribute for specified objects in the Bloodhound database. Objects can be provided either as arguments or using the -i switch.",
"* set_highvalue: Set the highvalue attribute for specified objects in the Bloodhound database. Objects can be provided either as arguments or using the -i switch.",
"* unset_highvalue: Unset the highvalue attribute for specified objects in the Bloodhound database. Objects can be provided either as arguments or using the -i switch.",
"* set: Set a custom attribute for specified objects in the Bloodhound database. The custom attribute has to be set using the -a switch (e.g., 'owned=true'). Objects can be provided either as arguments or using the -i switch."
]

parser = ArgumentParser(description = 'bloodtrail, console interface to important Bloodhound data.', formatter_class = RawTextHelpFormatter)
parser.add_argument('-v', dest = 'verbose', help = 'Verbose output', action = 'store_true')
parser.add_argument('-m', dest = 'mode', help = "Mode, possible values:\n"+"\n".join(mode_help), required = True)

parser.add_argument('-r', dest = 'bh_files', help = 'Path to folder that contains the .zip files produced by Sharphound. Gets additional information for session modes.')
parser.add_argument('-t', dest = 'list_timestamps', help = 'Lists timestamps for modes that print sessions. Warning: can be messy.', action = 'store_true')

parser.add_argument('-a', dest = 'set_attribute', help = 'Defines the attribute that is to be set in set-mode, e.g. "owned=true"')
parser.add_argument('-c', dest = 'comment', help = 'Comment for the log. Only used together with "set*" commands.', default = '')

parser.add_argument('-l', dest = 'output_list', help = 'Force the output to be a parseable list.', action = 'store_true')

parser.add_argument('-i',  dest = 'input_file', help = 'Path to a file that contains the arguments for the selected mode.')
parser.add_argument('args', nargs = '*', help = 'Arguments for the selected mode', default = '') 
parser.add_argument('--dburi', dest = 'databaseUri', help = 'Database URI (default: bolt://localhost:7687)', default = 'bolt://localhost:7687')
parser.add_argument('--dbuser', dest = 'databaseUser', help = 'Database user (default: neo4j)', default = 'neo4j')
parser.add_argument('--dbpassword', dest = 'databasePassword', help = 'Database password (default: kali)', default = 'kali')
arguments = parser.parse_args()

log.init_logging(arguments.verbose)

try:
    driver = GraphDatabase.driver(arguments.databaseUri, auth = Auth(scheme = 'basic', principal = arguments.databaseUser, credentials = arguments.databasePassword))
    session = driver.session()
except ServiceUnavailable:
    log.logger.exception('[-] Connection to BloodHound Neo4j database failed')
    exit
except Exception:
    log.logger.exception('[-] Error')
    exit

log.logger.debug('[*] Arguments: ' + str(arguments))

output_list = arguments.output_list

input_data = arguments.args

if arguments.input_file:
    with open(arguments.input_file, "r") as f:
        input_data.extend(f.readlines())

if arguments.bh_files:
    session_parser.parse(arguments.bh_files)

list_timestamps = False
if arguments.list_timestamps:
    list_timestamps = True

if arguments.mode == 'owned':
    print_owned_targets(input_data)
elif arguments.mode == 'groups':
    if len(input_data) == 0:
        print("You have to specify the name of the user/computers for which you want to receive groups or provide a file with the '-i' switch.")
        exit
    print_object_groups(input_data)
elif arguments.mode == 'high_value':
    print_high_value_targets(input_data)
elif arguments.mode == 'juicy_objects':
    print_objects_with_path_to_high_value(input_data)
elif arguments.mode == 'juicy_computers':
    print_computers_with_path_to_high_value()
elif arguments.mode == 'juicy_computer_sessions':
    print_computers_with_path_to_high_value(True)
elif arguments.mode == 'juicy_users':
    print_users_with_path_to_high_value()
elif arguments.mode == 'juicy_user_sessions':
    print_users_with_path_to_high_value(True)
elif arguments.mode == 'user_sessions':
    if len(input_data) == 0:
        print("You have to specify the names of the users for which you want to receive sessions or provide a file with the '-i' switch.")
        exit
    print_user_sessions(input_data)
elif arguments.mode == 'all_user_sessions':
    print_all_user_sessions()
elif arguments.mode == 'computer_sessions':
    if len(input_data) == 0:
        print("You have to specify the names of the computers for which you want to receive sessions or provide a file with the '-i' switch.")
        exit
    print_computer_sessions(input_data)
elif arguments.mode == 'all_computer_sessions':
    print_all_computer_sessions()
elif arguments.mode == 'outdated_systems':
    print_outdated_systems()
elif arguments.mode == 'psexec_computers':
    print_psexec_computers()
elif arguments.mode == 'query':
    if len(input_data) == 0:
        print("You have to specify the query.")
        exit
    print_query_results(input_data[0])
elif arguments.mode == 'hosts':
    print_query_results('MATCH (n:Computer) RETURN n')
elif arguments.mode == 'users':
    print_query_results('MATCH (n:User) RETURN n')
elif arguments.mode == 'set_owned':
    if len(input_data) == 0:
        print("You have to specify the object_names that should be marked or provide a file with the '-i' switch.")
        exit
    set_object_prop(input_data, "owned=true", arguments.comment)
elif arguments.mode == 'set_highvalue':
    if len(input_data) == 0:
        print("You have to specify the object_names that should be marked or provide a file with the '-i' switch.")
        exit
    set_object_prop(input_data, "highvalue=true", arguments.comment)
elif arguments.mode == 'unset_owned':
    if len(input_data) == 0:
        print("You have to specify the object_names that should be marked or provide a file with the '-i' switch.")
        exit
    set_object_prop(input_data, "owned=false", arguments.comment)
elif arguments.mode == 'unset_highvalue':
    if len(input_data) == 0:
        print("You have to specify the object_names that should be marked or provide a file with the '-i' switch.")
        exit
    set_object_prop(input_data, "highvalue=false", arguments.comment)
elif arguments.mode == 'set':
    if not arguments.set_attribute:
        print("You have to specify the attribute that you want to set using the '-a' switch, e.g., '-a owned=true'")
    if len(input_data) == 0:
        print("You have to specify the object_names that should be marked or provide a file with the '-i' switch.")
        exit
    set_object_prop(input_data, arguments.set_attribute, arguments.comment)
else:
    print("Mode not recognized. Exiting.")
    exit

exit
