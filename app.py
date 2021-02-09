from flask import Flask, render_template, request, redirect ,url_for, send_from_directory, session, make_response, json, current_app
from http import cookies
from flaskext.mysql import MySQL

from datetime import datetime
import os

app = Flask(__name__)

mysql = MySQL()
mysql.init_app(app)



app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'ferreteria'

mysql = MySQL(app)

app.secret_key = "1234"

CARPETA= os.path.join('media')
app.config['CARPETA']=CARPETA

def login_use(data):
    datos=data[0]
    session["id"]=datos[0]
    session["username"]=datos[1]
   
   


def logout_out():
    session.pop("id",None)
    session.pop("username",None)


@app.route('/src/media/<nombrefoto>')
def media(nombrefoto):
    return send_from_directory(app.config['CARPETA'],nombrefoto)

@app.route('/set_cookie')
def cookie_insertion():
    redirect_to_index = redirect('/productos')
    response = current_app.make_response(redirect_to_index)
    response.set_cookie('carrito')
    return response    


@app.route('/')
def home():
    return  render_template('home.html')

@app.route('/nosotros')
def nosotros():
    return render_template('nosotros.html')

@app.route('/ofertas')
def ofertas():
    return render_template('ofertas.html')

@app.route('/productos/<categoria>')
def productos(categoria):
    valor=categoria
    sql='SELECT * FROM productos WHERE ID_DETALLE=%s;'
    cur =  mysql.get_db().cursor()
    cur.execute(sql,valor)
    data = cur.fetchall()

    if len(data)!=0:

        sql='SELECT * FROM detalle_producto WHERE ID_DETALLEP=%s;'
        cur =  mysql.get_db().cursor()
        cur.execute(sql,valor)
        categoria = cur.fetchall()
    
        cambio=list(zip(data,categoria))
        
        return render_template('productos.html', productos =cambio)
    else:
        return render_template('error.html')    

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/ingresar', methods=['POST'])
def ingresar():
   
    usuario =request.form['usuario']
    clav =request.form['clave']
    cur =  mysql.get_db().cursor()
    sql="SELECT * FROM `usuarios` WHERE (usuario=%s) and (clave=%s)"
    datos=(usuario,clav)
    cur.execute(sql,datos)
    data = cur.fetchall()
    

    if data =="":
        return render_template('login.html')
    else:
        login_use(data)
        return redirect(url_for('principal'))


@app.route('/principal')
def principal():
    try:
        codigo=session["id"]
    except:
        codigo=''
    if codigo!='':
        cur =  mysql.get_db().cursor()
        cur.execute('SELECT * FROM productos')
        data = cur.fetchall()
        return render_template('principal.html', productos = data)
    else:
        return render_template('login.html')
    


@app.route('/carrito_add', methods=['POST'])
def carrito():
   
        codigo=request.form['codigo']
        nombre=request.form['nombre']
        cantidad=request.form['cantidad']
        stock=request.form['disponible']
        categori=request.form['categoria']
        precio=request.form['precio']
        sub= 0
        sub= float(cantidad) * float(precio)

        if nombre and cantidad and precio and request.method == 'POST':
            if float(stock) >= float(cantidad):
                try:
                    datos = json.loads(request.cookies.get('carrito'))
                    
                except:
                    datos = []
                actualizar = False
              
                for dato in datos:
                    if dato["id"] == codigo:
                        dato["cantidad"] = cantidad
                        dato["sub"] = float(cantidad) * float(precio)
                        actualizar = True
                if not actualizar:
                    datos.append({"id": codigo,"nombre": nombre, "cantidad": cantidad,"precio": precio,"sub":sub})
                resp = make_response(redirect(url_for('productos',categoria=categori)))
                resp.set_cookie('carrito', json.dumps(datos))
                
                return resp
        return redirect(url_for('productos',categoria=categori))

@app.route('/cookie_delete/<id>')
def cookie_delete(id):
   
    try:
        datos = json.loads(request.cookies.get('carrito'))
    except:
        datos = []
    new_datos = []
    for dato in datos:
        if dato['id'] != id:
            new_datos.append(dato)
    resp = make_response(redirect(url_for('car')))
    resp.set_cookie('carrito', json.dumps(new_datos))            
    return resp

@app.route('/carrito')
def car():
    
    try:
        datos = json.loads(request.cookies.get('carrito'))
       
    except:
        datos = []
    total = 0
    iva =0
    
    for art in datos:
       
        total = total + float(art["precio"])* float(art["cantidad"])
    iva = float(total) * 0.12
    total = float(total) + float(iva)
  
    return render_template('carrito.html', articulos = datos , total = total, iva=iva)
          




@app.route('/empty')
def empty_car():
    try:
        session.clear()
        return redirect(url_for('productos'))
    except Exception as e:
        print(e)


@app.route('/crear')    
def nuevo():
    return render_template('crearProducto.html')

@app.route('/actualizar/<id>')
def actualizar(id):
    try:
        codigo=session["id"]
    except:
        codigo=''
    if codigo!='':
        cur =  mysql.get_db().cursor()
        sql="SELECT * FROM `productos` WHERE ID_PRODUCTO=%s "
        cur.execute(sql,id)
        data = cur.fetchall()
        dotos =data[0]
        
        cur.close()
        
        codi=dotos[1]

        cur =  mysql.get_db().cursor()
        sql="SELECT * FROM `detalle_producto` WHERE ID_DETALLEP=%s "
        cur.execute(sql,codi)
        datas = cur.fetchall()
        doto =datas[0]
        dot=doto[1]
       
        cur.close()

        return render_template('actualizar.html',datos=dotos,doto=dot)
    else:
        return render_template('login.html')

@app.route('/new_datos', methods=['POST'])
def new_datos():
    idpro=request.form['id']
    _nombre=request.form['nombre']
    _descripcion=request.form['descripcion']
    _precio=request.form['precio']
    _disponible=request.form['disponible']
    _categoria=request.form['categoria']
    _imagen=request.form['imagen']
    _foto=request.files['foto']
    now= datetime.now()
    tiempo=now.strftime("%Y%H%M%S")
    if _foto.filename!='':
        nuevoNombre=tiempo+_foto.filename
        _foto.save("media/"+nuevoNombre)
        foto=True

        os.remove(os.path.join(app.config['CARPETA'],_imagen))

    else:
        foto=False    
    
    if foto==True:
        sentencia="SELECT * FROM `detalle_producto` WHERE  CATEGORIA=%s;"
     
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute(sentencia,_categoria)
        data = cursor.fetchall()
        dotos = data[0]
        codigo=str(dotos[0])
        conn.commit()
        conn.close()
    
        if codigo !="":
            datos=(codigo,_nombre,_descripcion,_precio,_disponible,nuevoNombre,idpro)

            sql=" UPDATE `productos` SET `ID_DETALLE`=%s, `NOMBRE`=%s, `DESCRIPCION`=%s, `PRECIO`=%s,`DISPONIBLE`=%s, `FOTO`=%s WHERE ID_PRODUCTO=%s; "

            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.execute(sql,datos)
            conn.commit()
            return redirect(url_for('principal'))
        else:
            return redirect(url_for('principal'))
    else:
         sentencia="SELECT * FROM `detalle_producto` WHERE  CATEGORIA=%s;"
     
         conn = mysql.connect()
         cursor = conn.cursor()
         cursor.execute(sentencia,_categoria)
         data = cursor.fetchall()
         dotos = data[0]
         codigo=str(dotos[0])
         conn.commit()
         conn.close()
    
         if codigo !="":
             datos=(codigo,_nombre,_descripcion,_precio,_disponible,idpro)

             sql=" UPDATE `productos` SET `ID_DETALLE`=%s, `NOMBRE`=%s, `DESCRIPCION`=%s, `PRECIO`=%s,`DISPONIBLE`=%s WHERE ID_PRODUCTO=%s; "

             conn = mysql.connect()
             cursor = conn.cursor()
             cursor.execute(sql,datos)
             conn.commit()
             return redirect(url_for('principal'))
         else:
             return redirect(url_for('principal'))


@app.route('/store', methods=['POST'])   
def guardar():
    _nombre=request.form['nombre']
    _descripcion=request.form['descripcion']
    _precio=request.form['precio']
    _disponible=request.form['disponible']
    _categoria=request.form['categoria']
    _foto=request.files['foto']
    now= datetime.now()
    tiempo=now.strftime("%Y%H%M%S")
    if _foto.filename!='':
        nuevoNombre=tiempo+_foto.filename
        _foto.save("media/"+nuevoNombre)
    
    sentencia="SELECT * FROM `detalle_producto` WHERE  CATEGORIA=%s;"
     
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute(sentencia,_categoria)
    data = cursor.fetchall()
    dotos = data[0]
    codigo=str(dotos[0])
    conn.commit()
    conn.close()
    
    if codigo !="":
        datos=(codigo,_nombre,_descripcion,_precio,_disponible,nuevoNombre)

        sql="INSERT INTO `productos` (`ID_PRODUCTO`, `ID_DETALLE`, `NOMBRE`, `DESCRIPCION`, `PRECIO`,`DISPONIBLE`, `FOTO`) VALUES (NULL,%s, %s, %s, %s, %s, %s); "

        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute(sql,datos)
        conn.commit()
        return redirect(url_for('principal'))
    else:
        return redirect(url_for('principal'))

@app.route('/cliente/<Total>')
def cliente(Total):
    return render_template('cliente.html', total=Total)


@app.route('/generarPedido', methods=['POST'])
def generarPedido():
    codigo=0
    _cedula=request.form['cedula']
    _nombre=request.form['nombre']
    _correo=request.form['correo']
    _celular=request.form['celular']
    Total=request.form['total']

    sentencia="SELECT * FROM `clientes` WHERE  CEDULA=%s;"
     
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute(sentencia,_cedula)
    data = cursor.fetchall()
    conn.commit()
    

    if len(data) ==0:

        sql="INSERT INTO `clientes` (`ID_CLIENTE`, `CEDULA` , `NOMBRES`, `CORREO`, `CELULAR`) VALUES (NULL,%s, %s, %s, %s); "
        datos=(_cedula,_nombre,_correo,_celular)
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute(sql,datos)
        conn.commit()

        sentencia="SELECT * FROM `clientes` WHERE  CEDULA=%s;"
     
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute(sentencia,_cedula)
        data = cursor.fetchall()
        conn.commit()
        codigo=data[0][0]

        
    else:
        codigo=data[0][0]


    instruccion="INSERT INTO `pedidos` (`ID_PEDIDO`, `ID_CLIENTE` , `FECHA`, `HORA`, `TOTAL`) VALUES (NULL,%s, CURDATE(), now(), %s); "
    valores=(codigo,Total)
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute(instruccion,valores)
    conn.commit()

    sentencia="SELECT * FROM `pedidos` WHERE  ID_CLIENTE=%s;"
     
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute(sentencia,codigo)
    data = cursor.fetchall()
    ident=data[0][0]
    conn.commit()

    try:
        datos = json.loads(request.cookies.get('carrito'))
       
    except:
        datos = []

    
    for dato in datos:
        producto=dato["id"]
        cantidad=dato["cantidad"]

        instruccion="INSERT INTO `detalle_pedidos` (`ID_DETALLE`, `ID_PEDIDO` , `ID_PRODUCTO`, `CANTIDAD`) VALUES (NULL,%s,%s,%s); "
        valores=(ident,producto,cantidad)
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute(instruccion,valores)
        conn.commit()

        instruccion="UPDATE `productos` SET DISPONIBLE=(DISPONIBLE-%s) WHERE ID_PRODUCTO=%s; "
        valores=(cantidad,producto)
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute(instruccion,valores)
        conn.commit()
        
    resp = make_response(render_template('final.html'))
    resp.set_cookie('carrito',"", expires=0)
    return resp

    

@app.route('/final')
def final():
    return render_template('final.html')



@app.route('/pedidos')
def pedidos():
    try:
        codigo=session["id"]
    except:
        codigo=''
    
    if codigo!='':

        nombres=""
        conn = mysql.connect()
        cursor= conn.cursor()
        lista=[]
        cursor.execute("SELECT * FROM pedidos;")
        filas=cursor.fetchall() 
        conn.commit()
        for fila in filas:
            idc=fila[1]
      
            cursor.execute("SELECT NOMBRES FROM clientes WHERE ID_CLIENTE=%s", idc) 
            nombres= cursor.fetchall()  
            conn.commit()   
            if len(nombres)==0:
                print('no hay datos')
            else:
                nombres=nombres[0][0]
                lista.append(nombres)
                combinada = list(zip(filas, lista))    
    
        return render_template('pedidos.html',filas=combinada)
    else:
        return render_template('login.html')

@app.route('/destroy/<id>')
def destroy(id):
    conn = mysql.connect()
    cursor= conn.cursor()

    cursor.execute("SELECT FOTO FROM productos WHERE ID_PRODUCTO =%s", id)
    fila=cursor.fetchall()
    os.remove(os.path.join(app.config['CARPETA'],fila[0][0]))

    cursor.execute("DELETE FROM productos WHERE ID_PRODUCTO =%s",(id))
    conn.commit()
    return redirect(url_for('principal'))

@app.route('/buscar', methods=['POST'])
def buscar():
    palabra=request.form['clave']
    cambio="%"+palabra+"%"
    cambi=(cambio,cambio)
    
    conn = mysql.connect()
    cursor= conn.cursor()
    
    sql="SELECT * FROM productos WHERE NOMBRE LIKE %s OR DESCRIPCION LIKE %s AND DISPONIBLE>=1;"

    cursor.execute(sql,cambi)
    fila=cursor.fetchall()
    codi=fila[0][1]
    conn.commit()

    

    if len(fila)==0 :
        return render_template('error.html')
    else:
        conn = mysql.connect()
        cursor= conn.cursor()
    
        sql="SELECT * FROM detalle_producto WHERE ID_DETALLEP = %s;"
        codi=fila[0][1]
        cursor.execute(sql,codi)
        categoria=cursor.fetchall()
        conn.commit()
        combinar=list(zip(fila,categoria))
        return render_template('productos.html', productos = combinar)

@app.route('/error')
def error():
    return render_template('error.html')

@app.context_processor
def contador():
    if request.cookies.get('carrito') == None:
        return {'num_articulos':0}
    else:
        datos = json.loads(request.cookies.get('carrito'))
        return {'num_articulos':len(datos)}

@app.route('/salir')
def salir():
    logout_out()
    return render_template('login.html')

@app.context_processor
def categorias():
    cur =  mysql.get_db().cursor()
    cur.execute('SELECT * FROM detalle_producto')
    data = cur.fetchall()
    return {'categori':data}

if __name__ =='__main__':
    app.run(debug=True)    