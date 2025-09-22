import debugpy

waitForDebugArg = "--waitForDebug"
debugPort = 5678


def check_for_debugger(args: list[str]) -> list[str]:
    """
    Checks whether a debugger is expected and if so waits for it. Return the args not containing the waitForDebugArg.
    """

    if waitForDebugArg in args:
        listen_and_wait_for_debugger()
        args.remove(waitForDebugArg)

    return args


def listen_and_wait_for_debugger():
    """
    Listens for a debugger to attach and waits until it does.
    """

    attachDebuggerNotification = f"###\n Waiting for debugger on port {debugPort}! Either attach a debugger or run without the '{waitForDebugArg}' arg. \n###"
    print(attachDebuggerNotification)
    debugpy.listen(("localhost", debugPort))
    debugpy.wait_for_client()  # execution pauses until VS Code attaches

    debuggerAttachedNotification = (
        "###\n Debugger attached! Happy debugging d=====(￣▽￣*)b \n###"
    )
    print(debuggerAttachedNotification)
