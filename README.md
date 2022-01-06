# Bloodtrail

Bloodtrail is a python tool to enable efficient work with Bloodhound results. It can act as an interface between Bloodhound and other commandline tools. It is also useful for quick lookups that are better done in a console than in a graph representation. The tool is work-in-progress and primarily used by me in my own assignments, so use it with a grain of salt.

Bloodhound is a great tool that probably is a cornerstone for many pentesters. However, it currently lacks interoperability with other tools as it is hard to extract data in textual form. Luckily, it provides nice interfaces that can be used by scripts like Bloodtrail.

## Features

* Export lists of entities to be used in other tools: 
  * Want to nmap scan all computers that have a path to domain admin? Bloodtrail quickly gets you a list of targets that can be fed to nmap (or [nettrail](https://github.com/yensk/nettrail)).
  * Want to get a list of users that are logged on to a particular juicy machine to password-spray them? Bloodtrail gives you a list that you can feed to tools like *crackmapexec*.
  * Want to get a list of potentially outdated systems that you can focus your enumeration on? Bloodtrail has a predefined query for that.
  * ...
* Get information that is cumbersome to extract in Bloodhound itself:
  * Want to know at which times users logged on to a given machine? Bloodtrail gives you that information (if you provide it with the original SharpHound zip files).
  * Want to get a sorted list of entities that you can grep through rather than a graph? Bloodtrail can provide that even for custom Cypher queries.
  * Want to know which workstation belongs to which user? Even if Bloodhound contains ambiguos session information due to frequent IP reuse in VPNs, Bloodtrail *tries* to help you by counting sessions.
* Set properties of a batch of Bloodhound entities (e.g., mark them as high value)

## Setup

Bloodtrail has to establish a connection to the Bloodhound neo4j database. The following python module has to be installed:

~~~
pip3 install neo4j
~~~

## How to use

~~~
usage: bloodtrail [-h] [-v] -m MODE [-r BH_FILES] [-t] [-a SET_ATTRIBUTE] [-c COMMENT] [-l] [-i INPUT_FILE] [--dburi DATABASEURI] [--dbuser DATABASEUSER] [--dbpassword DATABASEPASSWORD] [args ...]

bloodtrail, console interface to important Bloodhound data.

positional arguments:
  args                  Arguments for the selected mode

optional arguments:
  -h, --help            show this help message and exit
  -v                    Verbose output
  -m MODE               Mode, possible values:
                        * juicy_computers: List all computers that have a path to a highvalue target.
                        * juicy_computer_sessions: List all computers that have a path to a highvalue target and the users that have a session on them. This can provide you a hint at login rights, that Bloodhound is not able to capture by itself.
                        * juicy_users: List all users that have a path to a highvalue target.
                        * juicy_user_sessions: List all users that have a path to a highvalue target and the machines that they are logged on to.
                        * juicy_objects: List all objects that have a path to a highvalue target.
                        * all_user_sessions: List all users and their open sessions. Provides session count if raw Sharphound files are provided with -r.
                        * user_sessions: List open sessions for the provided users. Users can be provided either as arguments or using the -i switch. Provides session count if raw Sharphound files are provided with -r.
                        * all_computer_sessions: List all computers and their open sessions. Provides session count if raw Sharphound files are provided with -r.
                        * computer_sessions: List open sessions on the provided computers. Computers can be provided either as arguments or using the -i switch. Provides session count if raw Sharphound files are provided with -r.
                        * outdated_systems: List outdated systems.
                        * high_value: List highvalue objects.
                        * owned: List owned objects.
                        * groups: List groups of the provided objects. Objects can be provided either as arguments or using the -i switch.
                        * query: List the resulting objects of a custom query. The query has to be provided as argument.
                        * set_owned: Set the owned attribute for specified objects in the Bloodhound database. Objects can be provided either as arguments or using the -i switch.
                        * unset_owned: Unset the owned attribute for specified objects in the Bloodhound database. Objects can be provided either as arguments or using the -i switch.
                        * set_highvalue: Set the highvalue attribute for specified objects in the Bloodhound database. Objects can be provided either as arguments or using the -i switch.
                        * unset_highvalue: Unset the highvalue attribute for specified objects in the Bloodhound database. Objects can be provided either as arguments or using the -i switch.
                        * set: Set a custom attribute for specified objects in the Bloodhound database. The custom attribute has to be set using the -a switch (e.g., 'owned=true'). Objects can be provided either as arguments or using the -i switch.
  -r BH_FILES           Path to folder that contains the .zip files produced by Sharphound. Gets additional information for session modes.
  -t                    Lists timestamps for modes that print sessions. Warning: can be messy.
  -a SET_ATTRIBUTE      Defines the attribute that is to be set in set-mode, e.g. "owned=true"
  -c COMMENT            Comment for the log. Only used together with "set*" commands.
  -l                    Force the output to be a parseable list.
  -i INPUT_FILE         Path to a file that contains the arguments for the selected mode.
  --dburi DATABASEURI   Database URI (default: bolt://localhost:7687)
  --dbuser DATABASEUSER
                        Database user (default: neo4j)
  --dbpassword DATABASEPASSWORD
                        Database password (default: kali)
~~~