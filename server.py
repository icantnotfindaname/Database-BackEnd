from flask import Flask
import pymysql
from flask import request
import json
import jwt
from datetime import datetime,timedelta
from multiprocessing import Lock
lock = Lock()
conn = pymysql.connect(host='localhost',port=3306,user='root',password='mzy108431',database='shop',charset='utf8')
cursor = conn.cursor()
message = 'message'
success = 'success'
key='dkslakdalsdklsadklsakdlsa@9%'
app = Flask(__name__)
def valid_login(usr,psw):
	sql = 'select * from userImf where user=%s and pass=%s'
	res = cursor.execute(sql,[usr,psw])
	if res:
		now = datetime.utcnow()
		exp_datetime=now+timedelta(days=1)
		access_payload = {'exp':exp_datetime,'flag':0,'iat':now,'iss':'mzy','user_name':usr}
		token = jwt.encode(access_payload,key)
		result = cursor.fetchone()
		return json.dumps({message:'success',success:1,'token':str(token,encoding = 'utf8'),'college':result[2],'sex':result[6],'major':result[3],'name':result[1],'dormitory':result[4]})
	else:
		return json.dumps({message:'failed',success:0})
@app.route('/api/register',methods=['GET'])
def register():
	sql = 'select * from userImf where user=%s'
	user = request.args.get('user','')
	name = request.args.get('name','')
	sex = request.args.get('sex','')
	college = request.args.get('college','')
	major = request.args.get('major','')
	dormitory = request.args.get('dormitory','')
	passw = request.args.get('pass','')
	res = cursor.execute(sql,[request.args.get('user','')])
	print(user)
	if res:
		return json.dumps({'message':'账号已被注册','seccess':False})
	else:
		sql = 'insert into userImf values(%s,%s,%s,%s,%s,%s,%s)'
		cursor.execute(sql,[user,name,college,major,dormitory,passw,sex])
		conn.commit()
		sql = 'insert into cartList values(%s,%s)'
		cursor.execute(sql,[user,json.dumps([])])
		conn.commit()
		return json.dumps({'message':'注册成功','success':True})
		
@app.route('/api/login',methods=['GET','POST'])
def login():
	return valid_login(request.args.get('user',''),request.args.get('pass',''))
@app.route('/api/userInfo')
def userinfo():
	
	user = request.args.get('id','')
	name = request.args.get('name','')
	sex = request.args.get('sex','')
	college = request.args.get('college','')
	major = request.args.get('major','')
	dormitory = request.args.get('dormitory','')
	sql = 'update userImf set name=%s, college=%s, sex=%s, major=%s, dormitory=%s where user=%s'
	cursor.execute(sql,[name,college,sex,major,dormitory,user])
	conn.commit()
	return json.dumps({'message':'修改成功','success':True})
@app.route('/api/goods/allGoods')
def allgoods():
	page = request.args.get('page','')
	size = request.args.get('size','')
	sort = request.args.get('sort','')
	GT = request.args.get('priceGt','')
	LT = request.args.get('priceLte','')
	lock.acquire()
	if int(sort) == -1:
		sql = 'select * from goods where price >= %s and price <= %s order by price desc limit %s,%s'
		cursor.execute(sql,[int(GT),int(LT),(int(page)-1)*int(size),int(size)])
	elif int(sort) == 0:
		sql = 'select * from goods where price >= %s and price <= %s limit %s,%s'
		results = cursor.execute(sql,[int(GT),int(LT),(int(page)-1)*int(size),int(size)])
	else:
		sql = 'select * from goods where price >= %s and price <= %s order by price limit %s,%s'
		results = cursor.execute(sql,[int(GT),int(LT),(int(page)-1)*int(size),int(size)])
	lock.release()
	results = cursor.fetchall()
	data = []
	for row in results:
		pdata = {}
		pdata['productId'] = row[0]
		pdata['user'] = row[1]
		pdata['salePrice'] = row[7]
		pdata['productName'] = row[2]
		pdata['subTitle'] = row[3]
		pdata['productImageBig'] = row[4]
		pdata['productImageSmall'] =json.loads(row[5])
		pdata['num'] = row[6]
		data.append(pdata)
	sql = 'select * from goods'
	cursor.execute(sql)
	results = cursor.fetchall()
	return json.dumps({'data':data,'total':len(results)})
@app.route('/api/goods/productDet')
def pdet():
	pid = request.args.get('productId','')
	sql = 'select * from goods where pid = %s'
	cursor.execute(sql,[pid])
	row = cursor.fetchone()
	if not row:
		return json.dumps({'message':'false','success':False})
	pdata = {}
	pdata['productId'] = row[0]
	pdata['user'] = row[1]
	pdata['salePrice'] = row[7]
	pdata['productName'] = row[2]
	pdata['subTitle'] = row[3]
	pdata['productImageBig'] = row[4]
	pdata['productImageSmall'] =json.loads(row[5])
	pdata['num'] = row[6]
	sql = 'select * from comment where productId = %s'
	cursor.execute(sql,[pid])
	results = cursor.fetchall()
	commentList = []	
	for row in results:
		comment = {}		
		comment['userName'] = row[1]
		comment['comment']= row[2]
		commentList.append(comment)
	return json.dumps({'item':pdata,'commentList':commentList,'success':True})

@app.route('/api/goods/userGood')
def ugood():
	user = request.args.get('user','')
	sql = 'select * from goods where user = %s'
	cursor.execute(sql,[user])
	results = cursor.fetchall()
	data = []
	
	for row in results:
		pdata = {}	
		pdata['productId'] = row[0]
		pdata['user'] = row[1]
		pdata['salePrice'] = row[7]
		pdata['productName'] = row[2]
		pdata['subTitle'] = row[3]
		pdata['productImageBig'] = row[4]
		pdata['productImageSmall'] =json.loads(row[5])
		pdata['num'] = row[6]
		data.append(pdata)
	return json.dumps({'data':data,'success':True})

@app.route('/api/addgoods')
def addgood():
	
	user = request.args.get('user','')
	pname = request.args.get('productName','')
	price = request.args.get('salePrice','')
	num = request.args.get('num','')
	subtitle = request.args.get('subTitle','')
	pb  = request.args.get('productImageBig','')
	ps = request.args.get('productImageSmall','')
	pid = user + str(datetime.now())
	sql = 'insert into goods values(%s,%s,%s,%s,%s,%s,%s,%s)'
	cursor.execute(sql,[pid,user,pname,subtitle,pb,ps,num,price])
	conn.commit()
	item = {}
	item['productId'] = pid
	item['productName'] = pname
	item['salePrice'] = price
	item['num'] = float(num)
	item['subTitle'] = subtitle
	item['productImageBig'] = pb
	item['productImageSmall'] = ps
	item['user'] = user
	return json.dumps({'item':item,'success':True})
@app.route('/api/delgoods')
def defgood():
	pid = request.args.get('productId','')
	sql = 'delete from goods where pid = %s'
	cursor.execute(sql,[pid])
	conn.commit()
	return json.dumps({'success':True})

@app.route('/api/cartList')
def cart():
	user = request.args.get('userId','')
	sql = 'select * from cartList where id = %s'
	cursor.execute(sql,[user])
	res =  cursor.fetchone()
	cartlist = json.loads(res[1])
	return_cart = []
	new_cartList = []
	for product in cartlist:
		sql = 'select * from goods where pid = %s'
		cursor.execute(sql,[product['pid']])
		row = cursor.fetchone()
		pdata = {}
		if row:
			
			pdata['productId'] = row[0]
			pdata['user'] = row[1]
			pdata['salePrice'] = row[7]
			pdata['productName'] = row[2]
			pdata['subTitle'] = row[3]
			pdata['productImageBig'] = row[4]
			pdata['productImageSmall'] =json.loads(row[5])
			pdata['productNum'] = product['num']
			new_cartList.append(product)
			return_cart.append(pdata)
	sql = 'update cartList set cartList = %s where id = %s'
	cursor.execute(sql,[json.dumps(new_cartList),user])
	conn.commit()
	return json.dumps({'cartList':return_cart,'message':'success','success':True})

@app.route('/api/validate')
def valid():
	token = request.args.get('authorization','')
	if token == 'null':
		return json.dumps({message:'当前用户未登录',success:False})
		
	payload = jwt.decode(bytes(token,encoding='utf-8'),key)
	user = payload['user_name']
	sql = 'select * from userImf where user=%s'
	cursor.execute(sql,[user])
	result = cursor.fetchone()
	if result:
		now = datetime.utcnow()
		exp_datetime=now+timedelta(days=1)
		access_payload = {'exp':exp_datetime,'flag':0,'iat':now,'iss':'mzy','user_name':user}
		token = jwt.encode(access_payload,key)
	
		return json.dumps({message:'已登录',success:True,'token':str(token,encoding='utf8'),'id':user,'college':result[2],'sex':result[6],'major':result[3],'name':result[1],'dormitory':result[4]})
	else:
		return json.dumps({message:'当前用户未登录',success:False})
		 	

@app.route('/api/addCart')
def addcart():
	user = request.args.get('userId','')
	pid = request.args.get('productId','')
	num = request.args.get('productNum','')
	sql = 'select cartList from cartList where id = %s'
	cursor.execute(sql,[user])
	res = cursor.fetchone()
	clist = json.loads(res[0])
	print(clist)
	found = False
	for product in clist:
		if product['pid'] == pid:
			found = True
			product['num'] =str( float(product['num'])+float(num))
	if not found:
		clist.append({'pid':pid,'num':num})
	sql = 'update cartList set cartList = %s where id= %s'
	print(clist)
	cursor.execute(sql,[json.dumps(clist),user])
	conn.commit()
	return json.dumps({'message':'success','success':True})

@app.route('/api/delCart')
def delcart():
	user = request.args.get('userId','')
	pid = request.args.get('productId','')
	sql = 'select cartList from cartList where id = %s'
	cursor.execute(sql,[user])
	res = cursor.fetchone()
	clist = json.loads(res[0])
	found = -1
	for i in range(len(clist)):
		if clist[i]['pid'] == pid:
			found = i
			break
	if found != -1:
		del clist[found]
		sql = 'update cartList set cartList = %s where id = %s'
		cursor.execute(sql,[json.dumps(clist),user])
		conn.commit()
		return json.dumps({'message':'success','success':True})
	else:
		return json.dumps({'message':'false','success':False})

@app.route('/checkOut/productDet')
def productdet():
	pid = request.args.get('productId','')
	sql = 'select price,pname,image from goods where pid = %s'
	cursor.execute(sql,[pid])
	res = cursor.fetchone()
	return json.dumps({'productId':pid,'salePrice':res[0],'productName':res[1],'productImageBig':res[2]})
@app.route('/admin/allgoods')
def adminallgoods():
	sql = 'select * from goods'
	cursor.execute(sql)
	results = cursor.fetchall()
	data = []
	
	for row in results:
		pdata = {}	
		pdata['productId'] = row[0]
		pdata['user'] = row[1]
		pdata['salePrice'] = row[7]
		pdata['productName'] = row[2]
		pdata['subTitle'] = row[3]
		pdata['productImageBig'] = row[4]
		pdata['productImageSmall'] =json.loads(row[5])
		pdata['num'] = row[6]
		data.append(pdata)
	return json.dumps({'data':data,'success':True})

@app.route('/admin/deletegood')
def admindelgood():
	pid = request.args.get('productId','')
	sql = 'delete from goods where pid = %s'
	cursor.execute(sql,[pid])
	conn.commit()
	return json.dumps({'success':True,'message':'success'})

@app.route('/admin/orders')
def adminorder():
	page = int(request.args.get('page',''))
	size = int(request.args.get('size',''))
	sql = 'select * from ootable'
	cursor.execute(sql) 
	results = cursor.fetchall()
	total = len(results)
	sql = 'select * from ootable limit %s,%s'
	cursor.execute(sql,[(page-1)*size,size])
	results = cursor.fetchall()
	orderList = []
	for row in results:
		orderdata = {}
		orderdata['createDate'] = row[3]
		orderdata['goodsList'] = json.loads(row[5])
		orderdata['orderTotal'] = row[6]
		orderdata['orderStatus'] = row[7]
		orderdata['orderId'] = row[0]
		orderList.append(orderdata)
	return json.dumps({'orderList':orderList,'total':total,'message':'success','success':True})
	
@app.route('/getUserAddress')
def getaddr():
	user = request.args.get('userId','')
	sql = 'select name,dormitory from userImf where user = %s'
	cursor.execute(sql,[user])
	res = cursor.fetchone()
	if res:
		return json.dumps({'userinfo':{'address':res[1],'userName':res[0]},'message':'success','success':True})
	else:
		return json.dumps({'message':'false','success':False})

@app.route('/user/orderList/getOrders')
def getorder():
	user = request.args.get('userId','')
	size = int(request.args.get('size',''))
	page = int(request.args.get('page',''))
	sql = 'select * from ootable where user = %s'
	cursor.execute(sql,[user])
	results = cursor.fetchall()	
	total = len(results)
	sql = 'select * from ootable where user = %s limit %s,%s'
	cursor.execute(sql,[user,(page-1)*size,size])
	results = cursor.fetchall()
	orderList = []
	for row in results:
		orderdata = {}
		orderdata['createDate'] = row[3]
		orderdata['goodsList'] = json.loads(row[5])
		orderdata['orderTotal'] = row[6]
		orderdata['orderStatus'] = row[7]
		orderdata['orderId'] = row[0]
		orderList.append(orderdata)
	return json.dumps({'orderList':orderList,'total':total,'message':'success','success':True})


@app.route('/user/orderDetail')
def orderdetail():
	oid = request.args.get('orderId','')
	sql = 'select * from ootable where oid = %s'
	cursor.execute(sql,[oid])
	row = cursor.fetchone()
	if row:
		orderdata = {}
		orderdata['orderStatus'] = row[7]
		orderdata['orderList'] = json.loads(row[5])
		orderdata['userName'] = row[1]
		orderdata['address'] = row[9]
		orderdata['sellerName'] = row[2]
		orderdata['createTime'] = row[3]
		orderdata['finishTime'] = row[4]
		orderdata['orderTotal'] = row[6]
		orderdata['comment'] = row[8]
		return json.dumps({'orderDetail':orderdata,'message':'success','success':True})
	else:
		return json.dumps({'message':'false','success':False})

@app.route('/user/orderList/confirm')
def confirm():
	oid = request.args.get('orderId','')
	now = datetime.now()
	sql = 'update ootable set orderStatus = %s, createDate = %s where oid = %s'
	cursor.execute(sql,['1',str(now),oid])
	conn.commit()
	return json.dumps({'success':True,'message':'success'})

@app.route('/user/orderList/comment')
def comment():
	oid = request.args.get('orderId','')
	comments = request.args.get('comment','')
	sql = 'update ootable set comment = %s where oid = %s'
	cursor.execute(sql,[comments,oid])
	conn.commit()
	sql = 'select user, productList from ootable where oid = %s'
	cursor.execute(sql,[oid])
	res = cursor.fetchone()
	user = res[0]
	productlist = json.loads(res[1])
	for product in productlist:
		sql = 'insert into comment values(%s,%s,%s)'
		cursor.execute(sql,[product['productId'],user,comments])
		conn.commit()
	return json.dumps({'message':'success','success':True})
	

def buy(pid,num):
	sql = 'select num,user,price,image,pname from goods where pid = %s'
	cursor.execute(sql,[pid])
	res = cursor.fetchone()
	if float(num) >float(res[0]):
		return False,res[0],-1,-1,-1,res[4]
	sql = 'update goods set num = %s where pid = %s'
	cursor.execute(sql,[float(res[0]) - float(num) , pid])
	return True,-1,res[1],float(res[2]),res[3],res[4]
@app.route('/checkOut/buy')
def buy_one():
	user = request.args.get('userId','')
	pid  = request.args.get('productId','')
	num = request.args.get('num','')
	can_buy,rest,seller,price,productImg,productName = buy(pid,int(num))
	if can_buy:	
		oid = user + str(datetime.now())
		createDate = str(datetime.now())
		finishTime = ""
		productList = [{'productId':pid,'productImg':productImg,'productName':productName,'salePrice':price,'productNum':int(num)}]
		totalPrice = int(num) * price
		orderStatus = "0"
		comment = ""
		sql = 'select dormitory from userImf where user = %s'
		cursor.execute(sql,[user])
		res = cursor.fetchone()
		address = res[0]
		sql = 'insert into ootable values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
		cursor.execute(sql,[oid,user,seller,createDate,finishTime,json.dumps(productList),str(totalPrice),orderStatus,comment,address])
		conn.commit()
		return json.dumps({'success':True,'message':'success'})
	else:
		return json.dumps({'message':'false','success':False,'rest':rest})

@app.route('/checkOut/buyAll')
def buy_all():
	orders = []
	return_rest = {}
	user = request.args.get('userId','')
	sql = 'select dormitory from userImf where user = %s'
	cursor.execute(sql,[user])
	fail = False
	createDate = str(datetime.now())
	finishTime = ""
	comment = ""
	res = cursor.fetchone()
	address = res[0]
	sql = 'select cartList from cartList where id = %s'
	cursor.execute(sql,[user])
	res = cursor.fetchone()
	clist = json.loads(res[0])
	for product in clist:
		can_buy,rest,seller,price,productImg,productName = buy(product['pid'],product['num'])
		
		if can_buy:
			found = False
			for order in orders:
				if order['seller'] == seller:
					found = True
					order['productList'].append({'productId':product['pid'],'productImg':productImg,'productName':productName,'productNum':product['num'],'salePrice':price})
					order['totalPrice'] += float(price) * float(product['num'])
			if not found:
				order = {}
				order['oid'] = user + seller + str(datetime.now())
				order['user'] = user
				order['seller'] = seller
				order['createDate'] = createDate
				order['finishTime'] = finishTime
				order['productList'] = []
				order['productList'].append({'productId':product['pid'],'productImg':productImg,'productName':productName,'productNum':product['num'],'salePrice':price})	
				order['totalPrice'] = price * float(product['num'])
				order['orderStatus'] = '0'
				order['comment'] = ''
				order['address'] = address
				orders.append(order)
				
							
		else:
			fail = True
			return_rest[productName] = rest
	if fail:
		return json.dumps({'success':False,'message':'false','rest':return_rest})
	else:
		sql = 'update cartList set cartList = %s where id = %s'
		cursor.execute(sql,['[]',user])	
		for order in orders:	
			sql = 'insert into ootable values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
			cursor.execute(sql,[order['oid'],order['user'],order['seller'],order['createDate'],order['finishTime'],json.dumps(order['productList']),str(order['totalPrice']),order['orderStatus'],order['comment'],order['address']])
			conn.commit()
		return json.dumps({'success':True,'message':'success'})
if __name__ == '__main__':
	app.run(host='0.0.0.0')
	cursor.close()
