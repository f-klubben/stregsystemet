Debuggers
========

When running the server, using the argument --waitForDebug will tell the [manage.py](./manage.py) file to wait for a debugger to be attached before initializing the Django environment and running the command.

VSCode
-------
In VSCode to attach the debugger requires you to create a launch.json file, you can do this through the `Run and Debug` menu, which contains the following:
```json
{
    "name": "Attach Debugger",
    "type": "python",
    "request": "attach",
    "connect": {
        "host": "localhost",
        "port": 5678
    }
}
```

After running the server with the debug argument i.e:
```python
python manage.py runserver --waitForDebug
```

You should see something like this:
```
###
 Waiting for debugger on port 5678! Either attach a debugger or run without the '--waitForDebug' arg. 
###
```

You can now run the launch.json file through the `Run and Debug` menu, or by hitting `F5`

[Code related to attaching debugger can be found here.](./setup_utils.py)