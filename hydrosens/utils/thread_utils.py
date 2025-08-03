import ctypes
import threading


def terminate_thread(thread):
    """Terminate a thread forcefully"""
    if not thread or not thread.is_alive():
        return
    
    try:
        # Get the thread ID
        thread_id = thread.ident
        if thread_id is None:
            return
            
        # Force terminate the thread
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            ctypes.c_long(thread_id), 
            ctypes.py_object(SystemExit)
        )
        
        if res == 0:
            print("Failed to terminate thread - invalid thread ID")
        elif res != 1:
            # If it returns a number greater than one, you're in trouble,
            # and you should call it again with exc=NULL to revert the effect
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, None)
            print("Exception raise failure")
        else:
            print(f"Thread {thread_id} terminated successfully")
            
    except Exception as e:
        print(f"Error terminating thread: {str(e)}") 