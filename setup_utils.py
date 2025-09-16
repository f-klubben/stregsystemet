
import debugpy


def check_for_debugger(args: list[str]):
    """
    Checks whether a debugger is expected and if so waits for it.
    """

    waitForDebugArg = "--waitForDebug"

    if waitForDebugArg in args: 
        debugPort = 5678
        attachDebuggerNotification = f"###\n Waiting for debugger on port {debugPort}! Either attach a debugger or run without the '{waitForDebugArg}' arg. \n###"
        print(attachDebuggerNotification)
        debugpy.listen(("localhost", debugPort))
        debugpy.wait_for_client()  # execution pauses until VS Code attaches

        debuggerAttachedNotification = f"###\n Debugger attached! Happy debugging d=====(￣▽￣*)b \n###"
        print(debuggerAttachedNotification)