from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.db"
db = SQLAlchemy(app)

class Warehouse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    count = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Integer, nullable=False)


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    balance = db.Column(db.Integer, nullable=False)
    

class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    command = db.Column(db.String(10), nullable=False)


with app.app_context():
    db.create_all()

cmd_archive = []
stock_whs = {}
purchase_whs = {}
sell_count = 0
purchase_count = 0



@app.route("/")
def homepage():
    # reading warehouse
    whs = Warehouse.query.filter(Warehouse.count>0).all()
    for i in whs:
        product_name = i.name
        product_count = i.count
        product_price = i.price
        
        whs_in = {f"{product_name}": product_count}
        stock_whs.update(whs_in)

        purchase_whs_in = {f"{product_name}": product_price}
        purchase_whs.update(purchase_whs_in)

    # reading balance
    try:
        preaccount = []
        acc = Account.query.all()
        for i in acc:
            val = i.balance
            preaccount.append(val)
        # last row is the balance 
        account = preaccount[-1]
    except IndexError:
        account = 0

    return render_template("main.html", availability=stock_whs, account=account)


@app.route("/add_product", methods=["POST"])
def add_product():
    if request.method == "POST":
        purchased_product = request.form["product_name"]
        purchase_count = int(request.form["units"])
        purchase_price = int(request.form["buy_price"])

        if purchased_product not in stock_whs.keys():
            stock_whs[purchased_product] = purchase_count
            purchase_whs[purchased_product] = purchase_price
            # update database
            product = Warehouse(name=purchased_product, count=purchase_count, price=purchase_price)
            db.session.add(product)
            db.session.commit()

        else:
            stock_whs[purchased_product] += purchase_count
            purchase_whs[purchased_product] += purchase_price
            # update database
            product = db.session.query(Warehouse).filter(Warehouse.name==purchased_product).first()
            temp_count = product.count
            temp_price = product.price
            temp_count += purchase_count
            temp_price += purchase_price
            product.count = temp_count
            product.price = temp_price
            db.session.commit()

        # save balance
        try:
            acc = Account.query.all()
            list = []
            for i in acc:
                list.append(i.balance)
            temp_balance = list[-1]
        except IndexError:
            temp_balance = 0
        temp_balance -= purchase_price * purchase_count
        balance = Account(balance=temp_balance)
        db.session.add(balance)
        db.session.commit()

        # save history
        cmd = "zakup"
        his = History(command=cmd)
        db.session.add(his)
        db.session.commit()

        purchase_count = 0
    return render_template("main.html", availability=stock_whs, account=temp_balance)

@app.route("/sell_product", methods=["POST"])
def sell_product():
    if request.method == "POST":
        sold_product = request.form["product_name"]  
        
        # read warehouse
        whs = Warehouse.query.filter(Warehouse.count>0).all()
        for i in whs:
            product_name = i.name
            product_count = i.count
            product_price = i.price
        
            whs_in = {f"{product_name}": product_count}
            stock_whs.update(whs_in)

            purchase_whs_in = {f"{product_name}": product_price}
            purchase_whs.update(purchase_whs_in)   

        if sold_product not in stock_whs.keys():
            return "Brak towaru w magazynie!"
        
        else:
            sell_count = int(request.form["units"])

            if sell_count > stock_whs.get(sold_product):
                return "Brak towaru w magazynie!"
            else:
                stock_whs[sold_product] -= sell_count
                sell_price = int(request.form["sell_price"])
                # save warehouse
                product = db.session.query(Warehouse).filter(Warehouse.name==sold_product).first()
                temp_count = product.count
                temp_count -= sell_count
                product_count = temp_count
                db.session.commit()
                
                # save balance
                try:
                    acc = Account.query.all()
                    list = []
                    for i in acc:
                        list.append(i.balance)
                    temp_balance = list[-1]
                except IndexError:
                    temp_balance = 0
                temp_balance += sell_price * sell_count
                balance = Account(balance=temp_balance)
                db.session.add(balance)
                db.session.commit()
        
        sell_count = 0
        # save history
        cmd = "sprzedaz"
        his = History(command=cmd)
        db.session.add(his)
        db.session.commit()
    return render_template("main.html", availability=stock_whs, account=temp_balance)


@app.route("/balance_update", methods=["POST"])
def balance_update():
    if request.method == "POST":
        if request.form["balance_update"] == "":
            return "Wprowadź wartość"
        else:
            try:
                # save balance
                acc = Account.query.all()
                list = []
                for i in acc:
                    list.append(i.balance)
                temp_balance = list[-1]
            except IndexError:
                temp_balance = 0
            temp_balance += int(request.form["balance_update"])
            balance = Account(balance=temp_balance)
            db.session.add(balance)
            db.session.commit()
            # save history
            cmd = "saldo"
            his = History(command=cmd)
            db.session.add(his)
            db.session.commit()         
    return render_template("main.html", availability=stock_whs, account=temp_balance)


@app.route("/historia/<from>/<to>/")
def historypage(od, do):
    # history form action id to action id
    return render_template("historia.html", history=cmd_archive[int(od):int(do)])


@app.route("/history")
def historyfull():
    # odczyt archiwum
    cmd_archive = []
    arc = History.query.all()
    for i in arc:
        cmd_archive.append(i.command)
    return render_template("historia.html", history=cmd_archive)


if __name__ == "__main__":
    # app.run(debug=True)
    app.run()