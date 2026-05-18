from flask import Flask, request
from twilio.rest import Client
from pyngrok import ngrok, conf
import pandas as pd
import os
from datetime import datetime

app = Flask(__name__)

account_sid = "ACd1dd442531ac5bf39ae85ac1ae4a1720"
auth_token  = "0fd6c0a563f3fe51d738d109beb1ad72"
to_number   = "whatsapp:+919663084587"
ngrok_token = "3DDDPlnei5o7Cs0FW714MgC8JOi_6gARcrPadczhvdU5uhx4m"

from_number  = "whatsapp:+14155238886"
EXCEL_FILE   = "/Users/rachit/Desktop/expenses.xlsx"
MONTHLY_BUDGET = 70000

CATEGORIES = [
    "groceries", "petrol", "shopping",
    "electricity", "medicine", "dine out",
    "emis", "other"
]

if not os.path.exists(EXCEL_FILE):
    df = pd.DataFrame(columns=["date", "category", "amount", "note"])
    df.to_excel(EXCEL_FILE, index=False)
    print("Created expenses.xlsx on Desktop!")

def send_whatsapp(message):
    try:
        client = Client(account_sid, auth_token)
        client.messages.create(
            from_=from_number,
            to=to_number,
            body=message
        )
        print("WhatsApp sent!")
    except Exception as e:
        print("Error: " + str(e))

def add_expense(category, amount, note=""):
    df = pd.read_excel(EXCEL_FILE)
    new_row = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "category": category,
        "amount": amount,
        "note": note
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_excel(EXCEL_FILE, index=False)
    return "Added! Rs." + str(amount) + " for " + category

def get_today_summary():
    df = pd.read_excel(EXCEL_FILE)
    today = datetime.now().strftime("%Y-%m-%d")
    today_df = df[df["date"] == today]
    if len(today_df) == 0:
        return "No expenses recorded today!"
    msg = "Today's Expenses:\n"
    for cat in CATEGORIES:
        cat_total = today_df[today_df["category"] == cat]["amount"].sum()
        if cat_total > 0:
            msg += cat.capitalize() + ": Rs." + str(int(cat_total)) + "\n"
    msg += "Total: Rs." + str(int(today_df["amount"].sum()))
    return msg

def get_monthly_summary():
    df = pd.read_excel(EXCEL_FILE)
    month = datetime.now().strftime("%Y-%m")
    month_df = df[df["date"].str.startswith(month)]
    total_spent = int(month_df["amount"].sum())
    budget_left = MONTHLY_BUDGET - total_spent
    msg = "This Month's Expenses:\n"
    for cat in CATEGORIES:
        cat_total = month_df[month_df["category"] == cat]["amount"].sum()
        if cat_total > 0:
            msg += cat.capitalize() + ": Rs." + str(int(cat_total)) + "\n"
    msg += "Total Spent: Rs." + str(total_spent) + "\n"
    msg += "Budget Left: Rs." + str(budget_left)
    if budget_left < 0:
        msg += "\nOver budget by Rs." + str(abs(budget_left)) + "!"
    return msg

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming = request.form.get("Body", "").strip().lower()
    print("Message received: " + incoming)
    if incoming.startswith("spent"):
        parts = incoming.split()
        try:
            amount   = float(parts[1])
            category = parts[2] if len(parts) > 2 else "other"
            note     = " ".join(parts[3:]) if len(parts) > 3 else ""
            if category not in CATEGORIES:
                category = "other"
            result = add_expense(category, amount, note)
            reply  = result + "\nSend 'summary' to see today's expenses!"
        except:
            reply = "Please type like this:\nspent 500 groceries\nspent 200 petrol"
    elif incoming == "summary":
        reply = get_today_summary()
    elif incoming == "monthly":
        reply = get_monthly_summary()
    elif incoming == "budget":
        df       = pd.read_excel(EXCEL_FILE)
        month    = datetime.now().strftime("%Y-%m")
        month_df = df[df["date"].str.startswith(month)]
        spent    = int(month_df["amount"].sum())
        left     = MONTHLY_BUDGET - spent
        reply    = "Budget Status:\nMonthly Budget: Rs." + str(MONTHLY_BUDGET) + "\nSpent: Rs." + str(spent) + "\nLeft: Rs." + str(left)
    elif incoming == "help":
        reply = "Commands:\nspent 500 groceries\nspent 200 petrol\nsummary\nmonthly\nbudget"
    else:
        reply = "Commands:\nspent 500 groceries\nspent 200 petrol\nsummary\nmonthly\nbudget\nhelp"
    send_whatsapp(reply)
    return "OK"

if __name__ == "__main__":
    conf.get_default().auth_token = ngrok_token
    public_url = ngrok.connect(5000).public_url
    print("\nBot is running!")
    print("Your ngrok URL: " + public_url + "/whatsapp")
    print("\nCopy this URL and paste it in Twilio WhatsApp Sandbox settings!")
    print("\nWaiting for WhatsApp messages...\n")
    app.run(port=5000)