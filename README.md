![Dibi](https://raw.githubusercontent.com/janza/dibi/7608d161d16217243322d7ff7d2f996ae3c0b046/dibi.png)

Utilitarian cross-platform MySQL GUI client

# Features

- No auto-commit
- Basic autocomplete of databases and tables
- Export output of queries to other programs - using `-- !program`, eg: `SELECT * FROM table -- !cat > output.txt` will save the output of the select query to output.txt
- Change existing values using GUI
- Cmd/Alt + Click on a foreign key opens the referenced row
- Cmd/Alt + Click on a table shows column details of the table
- GUI Connection manager
- AUR package `dibi-git`

# Usage

Connection parameters can be passed through as CLI parameters:

    dibi --host 127.0.0.1 --user root --password password --port 3306

Otherwise connections can be configured with a config file at: `~/.dibi.conf`. An example of the config file:

    [connection_label]
    host=127.0.0.1
    user=root
    port=3306
    password=password             # optional if password_cmd is given
    password_cmd=echo mypassword  # optional command that is ran to get connection password
    ssh_host=ssh.tunnel.com       # optional host to use for creating ssh tunnel
    ssh_user=root                 # optional ssh user for the tunnel

    [another_connection]
    ...

GUI interface can also be used to configure connections.

## Todo

- [x] Commit/Rollback
- [x] List columns of a table
- [X] Basic Documentation
- [x] Better gfx
- [x] Nicer editing experience
- [x] Export results
- [ ] MacOS and windows distribution
- [ ] Simple scripting options


Icons made by [Smashicons](https://www.flaticon.com/authors/smashicons)
