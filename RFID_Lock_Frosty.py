#imports needed

import RPi.GPIO as GPIO
from mfrc522 import MFRC522
import tkinter as tk
from tkinter import messagebox
import random
import time
import threading

# GPIO and lock setup
lock_pin = 16
GPIO.setmode(GPIO.BCM)
GPIO.setup(lock_pin, GPIO.OUT)

reader = MFRC522()

# Engage the lock (locked state)
def engage_lock():
    print("Lock engaged (locked)")
    GPIO.output(lock_pin, GPIO.HIGH)

# Disengage the lock (unlocked state)
def disengage_lock():
    print("Lock disengaged (unlocked)")
    GPIO.output(lock_pin, GPIO.LOW)

# Function to handle the question after user is authenticated
def load_question_after_auth():
    question, choices, correct_answer = random.choice(questions)
    question_label.config(text=question)

    # Update radio buttons for the new question
    for i, choice in enumerate(choices):
        radio_buttons[i].config(text=choice, value=choice)

    # Store the correct answer in selected_answer variable
    selected_answer.set(correct_answer)

# Function to check the answer and unlock if correct
def check_answer():
    if selected_choice.get() == selected_answer.get():
        print("Correct answer! Unlocking the lock...")
        disengage_lock()
        # Show a congratulatory popup
        messagebox.showinfo("Access Granted", "Congratulations!!")
        root.after(5000, engage_lock)  # Re-engage lock after 5 seconds
    else:
        print("Incorrect answer. Access denied.")
        # Show "Loser!!" popup for incorrect answer
        messagebox.showwarning("Access Denied", "Loser!!")
    
    # Reset for the next RFID scan
    reset_for_next_scan()

# Function to reset UI for next RFID scan
def reset_for_next_scan():
    question_label.config(text="Please scan your RFID card.")
    for radio in radio_buttons:
        radio.config(text="", value="")
    selected_choice.set("")  # Reset choice
    selected_answer.set("")  # Clear stored correct answer
    rfid_ready.set(True)  # Signal that RFID can be scanned again

# Function to monitor RFID scanning
def monitor_rfid():
    try:
        while True:
            # Wait for RFID scan only if RFID is ready
            if rfid_ready.get():
                (status, TagType) = reader.MFRC522_Request(reader.PICC_REQIDL)
                if status == reader.MI_OK:
                    # Get UID of the scanned card
                    (status, uid) = reader.MFRC522_Anticoll()
                    if status == reader.MI_OK:
                        uid_string = ''.join(format(b, '02x') for b in uid)
                        print(f'RFID Badge Number: {uid_string}')
                        
                        # Check if the scanned UID is authorized
                        access_granted = False
                        for name, authorized_uid in authorized_uids.items():
                            if uid[:len(authorized_uid)] == authorized_uid:
                                print(f'Access Granted for {name}')
                                access_granted = True
                                
                                # Prepare to display a question and stop RFID scanning
                                rfid_ready.set(False)
                                root.after(0, load_question_after_auth)
                                break
                        if not access_granted:
                            print(f'Access denied for UID: {uid_string}')
                            # Show "Loser!!" popup for unauthorized UID
                            messagebox.showwarning("Access Denied", "Loser!!")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Program interrupted")
    finally:
        GPIO.cleanup()

# Tkinter GUI setup
root = tk.Tk()
root.title("RFID Authenticated Question for Access")

# Questions, each with a question text, choices, and correct answer to add more questions simply follow the below style
questions = [
    ("What IT group is the best?", ["Service delivery", "Infrastructure", "Apps", "Other"], "Service delivery")
]

# Dictionary of authorized users and their UIDs simply add to this list for the UIDs that you want to authorize
authorized_uids = {
    "Test": [0x13, 0x4c, 0x50, 0x9c, 0x93],
}

# GUI Elements
question_label = tk.Label(root, text="Please scan your RFID card.", font=("Helvetica", 16))
question_label.grid(row=0, column=0, padx=20, pady=20)

selected_choice = tk.StringVar()
selected_answer = tk.StringVar()  # Store the correct answer
rfid_ready = tk.BooleanVar(value=True)  # State variable to control RFID readiness

# Create radio buttons for choices
radio_buttons = [
    tk.Radiobutton(root, text="", variable=selected_choice, command=check_answer)
    for _ in range(4)
]
for i, radio in enumerate(radio_buttons):
    radio.grid(row=i+1, column=0, sticky='w')

# Start RFID monitoring in a separate thread
rfid_thread = threading.Thread(target=monitor_rfid, daemon=True)
rfid_thread.start()

# Start the Tkinter event loop
root.mainloop()
