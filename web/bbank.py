from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt
import json

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017")
db = client.BankAPI
users = db["Users"]

def UserExist(username):
    if users.find({ "Username": username }).count() == 0:
        return False
    else:
        return True
    
def generateReturnJson(status, msg):
    retJson = {
        "status": status,
        "msg": msg
    }
    return retJson
    
class Register(Resource):
    def post(self):
        postedData = request.get_json()
        
        username = postedData["username"]
        password = postedData["password"]
        
        if UserExist(username):
            jsonify( generateReturnJson( 301, "This username belongs to an existing account" ) )
        
        hashedPW = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())
        
        users.insert({
            "Username": username,
            "Password": hashedPW,
            "Balance": 0,
            "Debt": 0,
        })
        
        retJson = generateReturnJson( 200, "Successfully Registered for Bank API" )
        
        return jsonify( retJson )
    
def verifyPW(username, password):
    if not UserExist(username):
        return False
    
    hashedPW = users.find({
        "Username": username
    })[0]["Password"]
    
    if bcrypt.hashpw(password.encode("utf8"), hashedPW) == hashedPW:
        return True
    else: 
        return False
    
def usersBalance(username):
    balance = users.find({
        "Username": username
    })[0]["Balance"]
    return balance

def usersDebt(username):
    debt = users.find({
        "Username": username
    })[0]["Debt"]
    return debt

# returns Error dictionary and if it is True or False
def verifyCredentials(username, password):
    if not UserExist(username):
        return generateReturnJson( 301, "Not a registered username" ) , True
    
    correctPW = verifyPW(username, password)
    
    if not correctPW:
        return generateReturnJson( 302, "Incorrect Password" ) , True
    
    #There is no errors and the error dictionary is none
    return None , False 
        
def updateAccount(username, balance):
    users.update({
        "Username": username
    }, {
        "$set": {
            "Balance": balance
        }
    })
    
def updateDebt(username, debt):
    users.update({
        "Username": username
    }, {
        "$set": {
            "Debt": debt
        }
    })
    
class Deposit(Resource):
    def post(self):
        postedData = request.get_json()
        
        username = postedData["username"]
        password = postedData["password"]
        amount = postedData["amount"]
        
        retJson, error = verifyCredentials(username, password)
        
        if error:
            return jsonify( retJson )
        
        if amount <= 0:
            return jsonify( generateReturnJson( 304, "Amount must be greater than 0" ) )
        
        balance = usersBalance(username)
        depositFee = 1
        amountAfterFee = amount - depositFee
        bank_balance = usersBalance( "BANK" )
        new_bank_balance = bank_balance + depositFee
        updateAccount( "BANK" , new_bank_balance )
        new_balance = amountAfterFee + balance
        updateAccount( username, new_balance )
        
        retJson = generateReturnJson( 200, "Successfully Deposited. New Balance %s. Depoit fee was %s" % (new_balance, depositFee) )
        
        return jsonify( retJson )
    
class Transfer(Resource):
    def post(self):
        postedData = request.get_json()
        
        username = postedData["username"]
        password = postedData["password"]
        reciever = postedData["reciever"]
        amount   = postedData["amount"]
        
        retJson, error = verifyCredentials(username, password)
        if error:
            return jsonify( retJson )
        
        balance = usersBalance(username)
        
        if balance <= 0:
            return jsonify( generateReturnJson( 304, "Insuffienct Balance for Transfer" ) )
        
        if not UserExist(reciever):
            return jsonify( generateReturnJson( 301, "Recipient with that username does not exist" ) )
        
        sendersBalance = usersBalance(username)
        recieversBalance = usersBalance(reciever)
        bank_balance = usersBalance("BANK")
        transferFee = 1
        
        
        new_bank_balance = bank_balance + transferFee 
        updateAccount( "BANK", new_bank_balance )
        
        new_recieversBalance = recieversBalance + amount - transferFee
        updateAccount( reciever, new_recieversBalance )
        
        new_sendersBalance = sendersBalance - amount
        updateAccount( username, new_sendersBalance )
        
        retJson = generateReturnJson( 200, "Successfully Transfered Money. New Balance %s. Transfer Fee was %s" % (new_sendersBalance, transferFee) )
        
        return jsonify( retJson )

class Balance(Resource):
    def post(self):
        postedData = request.get_json()
        
        username = postedData["username"]
        password = postedData["password"]
        
        retJson, error = verifyCredentials(username, password)
        if error:
            return jsonify( retJson )
        
        # We omit the Password and ID, but return everything else
        retJson = users.find({
            "Username": username
        }, {
            "Password": 0,
            "_id":0
        })[0]
        
        return jsonify( retJson )

class TakeLoan(Resource):
    def post(self):
        postedData = request.get_json()
        
        username = postedData["username"]
        password = postedData["password"]
        amount = postedData["amount"]
        
        retJson, error = verifyCredentials(username, password)
        if error:
            return jsonify( retJson )
        
        balance = usersBalance(username)
        debt = usersDebt(username)
        
        new_balance = balance + amount
        updateAccount(username, new_balance)
        
        total_debt = debt + amount
        updateDebt(username, total_debt)
        
        retJson = generateReturnJson( 200, "Successfully taken out a loan. New Balance %s. Total Debt %s." %(new_balance, total_debt) )
        
        return jsonify( retJson )
    
class PayLoan(Resource):
    def post(self):
        postedData = request.get_json()
        
        username = postedData["username"]
        password = postedData["password"]
        amount = postedData["amount"]
        
        retJson, error = verifyCredentials(username, password)
        if error:
            return jsonify( retJson )
        
        balance = usersBalance(username)
        if balance < amount:
            return jsonify( generateReturnJson(304, "Insufficent balance to make payment"))
        
        debt = usersDebt(username)
        
        new_balance = balance - amount
        updateAccount(username, new_balance)
        
        total_debt = debt - amount
        updateDebt(username, total_debt)
        
        retJson = generateReturnJson( 200, "Successfully made payment for loan. New Balance %s. Total Debt %s." %(new_balance, total_debt) )
        
        return jsonify( retJson )
    
api.add_resource(Register, '/register' )
api.add_resource(Deposit, '/deposit' )
api.add_resource(Transfer, '/transfer' )
api.add_resource(Balance, '/balance' )
api.add_resource(TakeLoan, '/takeloan' )
api.add_resource(PayLoan, '/payloan' )

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug= True)
    
    