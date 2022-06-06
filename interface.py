import tkinter as tk
from tkinter import ttk
from tkinter import messagebox



'''
+---------------
| Widget Events
+---------------
'''
# exit button event
def exitButtonEvent(root):
	root.quit()



# login button event
def loginButtonEvent(usernameTextVariable):
	#print("Logging in!")
	messagebox.showinfo("Message", f"Logging in as {usernameTextVariable.get()}!")



# logoff button event
def logoffButtonEvent():
	#print("Logging off!")
	messagebox.showinfo("Message", "Logging off!")



# chat button event
def chatButtonEvent(userListBox):
	#print("Chatting!")
	messagebox.showinfo("Message", f"Chatting with {userListBox.get(tk.ANCHOR)}!")



root = tk.Tk()
root.title("Interface")
root.geometry("320x240")
#root.resizable(False, False)



'''
+---------------
| Widgets
+---------------
'''
# frames
leftFrame = ttk.Frame(root, padding = 8, borderwidth = 8, relief = "groove")
rightFrame = ttk.Frame(root, padding = 8, borderwidth = 8, relief = "groove")
loginLogoutFrame = ttk.Frame(rightFrame)

# list of users
userListVariable = tk.StringVar(leftFrame, value = [f"random {i}" for i in range(1, 101)])
userListBox = tk.Listbox(leftFrame, listvariable = userListVariable)

# username label
usernameLabel = ttk.Label(rightFrame, text = "Username:")

# username entry
usernameTextVariable = tk.StringVar(rightFrame, value = "Nata da Nata")
usernameEntry = ttk.Entry(rightFrame, textvariable = usernameTextVariable)

# login buttom
loginButtom = ttk.Button(loginLogoutFrame, text = "Log in", command = lambda: loginButtonEvent(usernameEntry))

# logoff buttom
logoffButtom = ttk.Button(loginLogoutFrame, text = "Log off", command = lambda: logoffButtonEvent())

# chat buttom
chatButton = ttk.Button(rightFrame, text = "Chat!", command = lambda: chatButtonEvent(userListBox))

# exit buttom
exitButtom = ttk.Button(rightFrame, text = "Exit", command = lambda: exitButtonEvent(root))



'''
+---------------
| Packing
+---------------
'''
# main frames
leftFrame.pack(side = tk.LEFT, fill = "y")#, expand=True)
rightFrame.pack(side = tk.LEFT, fill = "both", expand=True)

# left frame
userListBox.pack(side = tk.TOP, fill = "both", expand=True)

# right frame
usernameLabel.pack(side = tk.TOP)
usernameEntry.pack(side = tk.TOP)

loginLogoutFrame.pack(side = tk.TOP)
loginButtom.pack(side = tk.LEFT)
logoffButtom.pack(side = tk.RIGHT)

chatButton.pack(side = tk.TOP)

exitButtom.pack(side = tk.BOTTOM)



'''
+---------------
| Main
+---------------
'''
root.mainloop()